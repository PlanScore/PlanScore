var FIELDS = ['Population 2010', 'Population 2015', 'Black Population 2015',
    'Hispanic Population 2015', 'Population 2016', 'Black Population 2016',
    'Hispanic Population 2016', 'Citizen Voting-Age Population 2015',
    'Black Citizen Voting-Age Population 2015',
    'Hispanic Citizen Voting-Age Population 2015',
    'Democratic Votes', 'Republican Votes'
    /*, 'Polsby-Popper', 'Reock'*/];

function format_url(url_pattern, id)
{
    return url_pattern.replace('{id}', id);
}

function nice_count(value)
{
    if(value >= 1000)
    {
        var raw = value.toFixed(0);
        
        while(raw.match(/\d\d\d\d\b/))
        {
            raw = raw.replace(/(\d)(\d\d\d)\b/, '$1,$2');
        }
        
        return raw;
    }
    
    if(value >= 100) {
        return value.toFixed(0);
    } else if(value >= 10) {
        return value.toFixed(1);
    } else if(value >= 0) {
        return value.toFixed(2);
    } else {
        return '–';
    }
}

function nice_percent(value)
{
    return (100 * value).toFixed(1) + '%';
}

function nice_gap(value)
{
    if(value > 0) {
        return '+' + nice_percent(value) + ' for Democrats';
    } else {
        return '+' + nice_percent(-value) + ' for Republicans';
    }
}

function nice_string(value)
{
    return value.replace(/./gm, function(c) { return "&#" + c.charCodeAt(0) + ";" });
}

function clear_element(el)
{
    while(el.lastChild)
    {
        el.removeChild(el.lastChild);
    }
}

function date_age(date)
{
    return (new Date()).getTime() / 1000 - date.getTime() / 1000;
}

function what_score_description_html(plan)
{
    if(typeof plan['description'] === 'string')
    {
        return plan['description'];
    }

    return '<i>No description provided</i>';
}

function which_score_summary_name(plan)
{
    var summaries = [
        'US House Efficiency Gap', 'Efficiency Gap',
        'SLDL Efficiency Gap', 'SLDU Efficiency Gap'
        ];

    for(var i = 0; i < summaries.length; i++)
    {
        var name = summaries[i];

        if(typeof plan.summary[name] === 'number')
        {
            return name;
        }
    }

    return null;
}

function which_score_column_names(plan)
{
    if(typeof plan.summary['Efficiency Gap SD'] === 'number')
    {
        return FIELDS.slice();
    }

    if(typeof plan.summary['US House Efficiency Gap'] === 'number')
    {
        return [
            'Population', 'Voting-Age Population', 'Black Voting-Age Population',
            'US House Dem Votes', 'US House Rep Votes'
        ];
    }

    if(typeof plan.summary['Efficiency Gap'] === 'number')
    {
        return ['Voters', 'Blue Votes', 'Red Votes'];
    }

    return [];
}

function which_district_color(district, plan)
{
    var totals = district.totals,
        color_red = '#D45557',
        color_blue = '#4D90D1';

    if(typeof plan.summary['Efficiency Gap SD'] === 'number')
    {
        if(totals['Democratic Votes'] > totals['Republican Votes']) {
            return color_blue;
        } else {
            return color_red;
        }
    }

    if(typeof plan.summary['US House Efficiency Gap'] === 'number')
    {
        if(totals['US House Dem Votes'] > totals['US House Rep Votes']) {
            return color_blue;
        } else {
            return color_red;
        }
    }

    if(typeof plan.summary['Efficiency Gap'] === 'number')
    {
        if(totals['Blue Votes'] > totals['Red Votes']) {
            return color_blue;
        } else {
            return color_red;
        }
    }

    // neutral gray
    return '#808080';
}

function show_efficiency_gap_score(plan, score_EG)
{
    var summary_name = which_score_summary_name(plan),
        gap = plan.summary[summary_name],
        gap_amount = nice_percent(Math.abs(gap)),
        gap_error = plan.summary['Efficiency Gap SD'];
    
    for(node = score_EG.firstChild; node = node.nextSibling; node)
    {
        if(node.nodeName == 'H3') {
            node.innerHTML += ': ' + gap_amount;

        } else if(node.nodeName == 'DIV') {
            drawBiasBellChart('eg', gap, node.id,
                (plan.model ? plan.model.house : 'ushouse'), 'election');

        } else if(node.nodeName == 'P') {
            var win_party = (gap < 0 ? 'Republican' : 'Democratic'),
                lose_party = (gap < 0 ? 'Democratic' : 'Republican');

            clear_element(node);
            node.innerHTML = [
                'Votes for', win_party, 'candidates are expected to be wasted at a rate',
                gap_amount+'&nbsp;(±'+nice_percent(gap_error*2)+')',
                'lower than votes for', lose_party, 'candidates.',
                ' <a href="' + window.eg_metric_url + '">Learn more <i class="glyphicon glyphicon-chevron-right" style="font-size:0.8em;"></i></a>'
                ].join(' ');
        }
    }
}

function show_partisan_bias_score(plan, score_PB)
{
    var bias = plan.summary['Partisan Bias'],
        bias_amount = nice_percent(Math.abs(bias)),
        bias_error = plan.summary['Partisan Bias SD'];
    
    for(node = score_PB.firstChild; node = node.nextSibling; node)
    {
        if(node.nodeName == 'H3') {
            node.innerHTML += ': ' + bias_amount;

        } else if(node.nodeName == 'DIV') {
            drawBiasBellChart('pb', bias, node.id,
                (plan.model ? plan.model.house : 'ushouse'), 'election');

        } else if(node.nodeName == 'P') {
            var win_party = (bias < 0 ? 'Republicans' : 'Democrats');

            clear_element(node);
            node.innerHTML = [
                win_party, 'would be expected to win',
                bias_amount+'&nbsp;(±'+nice_percent(bias_error*2)+')',
                'extra seats in a hypothetical, perfectly tied election.',
                ' <a href="' + window.pb_metric_url + '">Learn more <i class="glyphicon glyphicon-chevron-right" style="font-size:0.8em;"></i></a>'
                ].join(' ');
        }
    }
}

function hide_score_with_reason(score_node, reason)
{
    for(node = score_node.firstChild; node = node.nextSibling; node)
    {
        if(node.nodeName == 'DIV')
        {
            clear_element(node);

        } else if(node.nodeName == 'P') {
            clear_element(node);
            node.appendChild(document.createTextNode(reason));
        }
    }
}

function show_mean_median_score(plan, score_MM)
{
    var diff = plan.summary['Mean-Median'],
        diff_amount = nice_percent(Math.abs(diff)),
        diff_error = plan.summary['Mean-Median SD'];
    
    for(node = score_MM.firstChild; node = node.nextSibling; node)
    {
        if(node.nodeName == 'H3') {
            node.innerHTML += ': ' + diff_amount;

        } else if(node.nodeName == 'DIV') {
            drawBiasBellChart('mm', diff, node.id,
                (plan.model ? plan.model.house : 'ushouse'), 'election');

        } else if(node.nodeName == 'P') {
            var win_party = (diff < 0 ? 'Republican' : 'Democrat');

            clear_element(node);
            node.innerHTML = [
                'The median', win_party, 'vote share is expected to be',
                diff_amount+'&nbsp;(±'+nice_percent(diff_error*2)+')',
                'higher than the mean', win_party, 'vote share.',
                ' <a href="' + window.mm_metric_url + '">Learn more <i class="glyphicon glyphicon-chevron-right" style="font-size:0.8em;"></i></a>'
                ].join(' ');
        }
    }
}

function show_sensitivity_test(plan, score_sense)
{
    Highcharts.chart(score_sense, {
        chart: { type: 'line' },
        legend: { enabled: false },
        credits: { enabled: false },
        title: { text: null },
        series: [{
            name: 'Expected Efficiency Gap',
            data: [
                100 * plan.summary['Efficiency Gap +5 Dem'],
                100 * plan.summary['Efficiency Gap +4 Dem'],
                100 * plan.summary['Efficiency Gap +3 Dem'],
                100 * plan.summary['Efficiency Gap +2 Dem'],
                100 * plan.summary['Efficiency Gap +1 Dem'],
                100 * plan.summary['Efficiency Gap'],
                100 * plan.summary['Efficiency Gap +1 Rep'],
                100 * plan.summary['Efficiency Gap +2 Rep'],
                100 * plan.summary['Efficiency Gap +3 Rep'],
                100 * plan.summary['Efficiency Gap +4 Rep'],
                100 * plan.summary['Efficiency Gap +5 Rep']
                ]
        }],
        xAxis: {
            categories: ['+5 D', '+4 D', '+3 D', '+2 D', '+1 D', '0', '+1 R', '+2 R', '+3 R', '+4 R', '+5 R'],
            title: { text: 'Possible Vote Swing' }
        },
        yAxis: { title: { text: null } },
        plotOptions: {
            line: {
                dataLabels: { enabled: false },
                enableMouseTracking: false
            }
        }
    });
}

function show_message(text, score_section, message_section)
{
    while(message_section.firstChild)
    {
        message_section.removeChild(message_section.firstChild);
    }

    message_section.appendChild(document.createElement('p'));
    message_section.firstChild.appendChild(document.createTextNode(text));

    score_section.style.display = 'none';
    message_section.style.display = 'block';
}

function hide_message(score_section, message_section)
{
    score_section.style.display = 'block';
    message_section.style.display = 'none';
}

function update_heading_titles(head)
{
    if(head.indexOf('Democratic Votes') >= 0 && head.indexOf('Republican Votes') >= 0)
    {
        head[head.indexOf('Democratic Votes')] = 'Predicted Democratic Vote Share';
        head[head.indexOf('Republican Votes')] = 'Predicted Republican Vote Share';
    }

    if(head.indexOf('Citizen Voting-Age Population 2015') >= 0
        && head.indexOf('Black Citizen Voting-Age Population 2015') >= 0
        && head.indexOf('Hispanic Citizen Voting-Age Population 2015') >= 0)
    {
        head[head.indexOf('Black Citizen Voting-Age Population 2015')] = 'Black Non-Hispanic CVAP 2015';
        head[head.indexOf('Hispanic Citizen Voting-Age Population 2015')] = 'Hispanic CVAP 2015';
    }
}

function update_vote_percentages(head, row)
{
    var dem_index = head.indexOf('Democratic Votes'),
        rep_index = head.indexOf('Republican Votes'),
        vote_count;

    if(dem_index >= 0 && rep_index >= 0)
    {
        vote_count = (row[dem_index] + row[rep_index]);
        row[dem_index] = nice_percent(row[dem_index] / vote_count);
        row[rep_index] = nice_percent(row[rep_index] / vote_count);
    }
}

function update_acs2015_percentages(head, row)
{
    var total_index = head.indexOf('Population 2015'),
        black_index = head.indexOf('Black Population 2015'),
        latin_index = head.indexOf('Hispanic Population 2015');

    if(total_index >= 0 && black_index >= 0 && latin_index >= 0)
    {
        row[black_index] = nice_percent(row[black_index] / row[total_index]);
        row[latin_index] = nice_percent(row[latin_index] / row[total_index]);
    }
}

function update_acs2016_percentages(head, row)
{
    var total_index = head.indexOf('Population 2016'),
        black_index = head.indexOf('Black Population 2016'),
        latin_index = head.indexOf('Hispanic Population 2016');

    if(total_index >= 0 && black_index >= 0 && latin_index >= 0)
    {
        row[black_index] = nice_percent(row[black_index] / row[total_index]);
        row[latin_index] = nice_percent(row[latin_index] / row[total_index]);
    }
}

function update_cvap2015_percentages(head, row)
{
    var total_index = head.indexOf('Citizen Voting-Age Population 2015'),
        black_index = head.indexOf('Black Citizen Voting-Age Population 2015'),
        latin_index = head.indexOf('Hispanic Citizen Voting-Age Population 2015');

    if(total_index >= 0 && black_index >= 0 && latin_index >= 0)
    {
        row[black_index] = nice_percent(row[black_index] / row[total_index]);
        row[latin_index] = nice_percent(row[latin_index] / row[total_index]);
    }
}

/*
 * Return a rows * columns matrix representing a scored plan table
 */
function plan_array(plan)
{
    var fields = FIELDS.slice();

    // Build list of columns
    var head_row = ['District'],
        all_rows = [head_row],
        field, current_row, field_missing;

    if(plan.districts.length == 0)
    {
        return undefined;
    }
    
    for(var j = 0; j < plan.districts.length; j++)
    {
        all_rows.push([(j + 1).toString()]);
    }
    
    for(var i in fields)
    {
        field = fields[i];
        field_missing = false;
        
        for(var j in plan.districts)
        {
            if(field in plan.districts[j].totals) {
                continue;
            } else if('compactness' in plan.districts[j] && field in plan.districts[j].compactness) {
                continue;
            } else {
                field_missing = true;
            }
        }
        
        if(field_missing) {
            continue;
        }
        
        head_row.push(field);

        for(var j in plan.districts)
        {
            current_row = all_rows[parseInt(j) + 1];
        
            if(field in plan.districts[j].totals) {
                current_row.push(plan.districts[j].totals[field]);

            } else if('compactness' in plan.districts[j] && field in plan.districts[j].compactness) {
                current_row.push(plan.districts[j].compactness[field]);
            }
        }
    }
    
    for(var j = 1; j < all_rows.length; j++)
    {
        update_vote_percentages(head_row, all_rows[j]);
        update_acs2015_percentages(head_row, all_rows[j]);
        update_acs2016_percentages(head_row, all_rows[j]);
        update_cvap2015_percentages(head_row, all_rows[j]);
    }
    
    update_heading_titles(head_row);
    return all_rows;
}

function plan_voteshare(plan)
{
    var red_votes = 0, blue_votes = 0,
        red_fields = ['Republican Votes'],
        blue_fields = ['Democratic Votes'];

    for(var i in plan.districts)
    {
        for(var j in red_fields)
        {
            if(red_fields[j] in plan.districts[i].totals)
            {
                red_votes += plan.districts[i].totals[red_fields[j]];
            }
        }

        for(var k in blue_fields)
        {
            if(blue_fields[k] in plan.districts[i].totals)
            {
                blue_votes += plan.districts[i].totals[blue_fields[k]];
            }
        }
    }
    
    return Math.abs(blue_votes - red_votes) / (blue_votes + red_votes);
}

function get_description(plan, modified_at)
{
    var states = {
        'XX': 'Null Island',
        'AL': 'Alabama', 'NE': 'Nebraska', 'AK': 'Alaska', 'NV': 'Nevada',
        'AZ': 'Arizona', 'NH': 'New Hampshire', 'AR': 'Arkansas',
        'NJ': 'New Jersey', 'CA': 'California', 'NM': 'New Mexico',
        'CO': 'Colorado', 'NY': 'New York', 'CT': 'Connecticut',
        'NC': 'North Carolina', 'DE': 'Delaware', 'ND': 'North Dakota',
        'DC': 'District of Columbia', 'OH': 'Ohio', 'FL': 'Florida',
        'OK': 'Oklahoma', 'GA': 'Georgia', 'OR': 'Oregon', 'HI': 'Hawaii',
        'PA': 'Pennsylvania', 'ID': 'Idaho', 'PR': 'Puerto Rico',
        'IL': 'Illinois', 'RI': 'Rhode Island', 'IN': 'Indiana',
        'SC': 'South Carolina', 'IA': 'Iowa', 'SD': 'South Dakota',
        'KS': 'Kansas', 'TN': 'Tennessee', 'KY': 'Kentucky', 'TX': 'Texas',
        'LA': 'Louisiana', 'UT': 'Utah', 'ME': 'Maine', 'VT': 'Vermont',
        'MD': 'Maryland', 'VA': 'Virginia', 'MA': 'Massachusetts',
        'VI': 'Virgin Islands', 'MI': 'Michigan', 'WA': 'Washington',
        'MN': 'Minnesota', 'WV': 'West Virginia', 'MS': 'Mississippi',
        'WI': 'Wisconsin', 'MO': 'Missouri', 'WY': 'Wyoming',
        'MT': 'Montana'
        };
    
    var description = ['Plan uploaded'], houses = {'ushouse': 'U.S. House',
        'statesenate': 'State Senate', 'statehouse': 'State House'};
    
    if(plan['start_time'])
    {
        modified_at = new Date(plan.start_time * 1000);
    }
    
    if(plan['model'])
    {
        description = [states[plan.model.state],
            houses[plan.model.house], 'plan uploaded'].join(' ');
    }

    return (date_age(modified_at) > 86400)
            ? [description, 'on', modified_at.toLocaleDateString()].join(' ')
            : [description, 'at', modified_at.toLocaleString()].join(' ');
}

function get_explanation(plan)
{
    if(plan['model'] && plan.model['incumbency'])
    {
        return 'PlanScore’s partisan asymmetry scores are based on a precinct-level model using election results, demographic data, and incumbency status from the 2016 general election. The scores displayed here rely on currently available information about which incumbents will run for reelection. These real-world estimates reveal the partisan skew that a plan is likely to exhibit by incorporating the effects of incumbency.';
    }

    return 'PlanScore’s partisan asymmetry scores are based on a precinct-level model using election results and demographic data from the 2016 general election.';
    return 'PlanScore’s partisan asymmetry scores are based on a precinct-level model using election results, demographic data, and incumbency status from the 2016 general election. The scores displayed here assume that all congressional seats will be open. These open-seat estimates reveal a plan’s underlying partisan skew by removing the effects of incumbency.';
}

function load_plan_score(url, message_section, score_section,
    description, table, score_EG, score_PB, score_MM, score_sense, text_url,
    text_link, map_url, map_div)
{
    var request = new XMLHttpRequest();
    request.open('GET', url, true);

    show_message('Loading district plan…', score_section, message_section);

    function on_loaded_score(plan, modified_at)
    {
        if(which_score_summary_name(plan) === null) {
            show_message(plan['message'] ? plan.message : 'District plan failed to load.',
                score_section, message_section);
            return;

        } else {
            hide_message(score_section, message_section);
        }

        // Clear out and repopulate description.
        clear_element(description);
        description.appendChild(document.createElement('i'));
        description.lastChild.appendChild(
            document.createTextNode(get_description(plan, modified_at)));
        description.appendChild(document.createElement('br'));
        description.appendChild(
            document.createTextNode(get_explanation(plan)));

        // Build the results table
        var table_array = plan_array(plan),
            tags, value;
        
        tags = ['<thead>', '<tr>'];
        for(var j = 0; j < table_array[0].length; j++)
        {
            tags = tags.concat(['<th>', table_array[0][j], '</th>']);
        }
        tags = tags.concat(['</tr>', '</thead>', '<tbody>']);
        for(var i = 1; i < table_array.length; i++)
        {
            tags = tags.concat(['<tr>']);
            for(var j = 0; j < table_array[i].length; j++)
            {
                if(typeof table_array[i][j] == 'number') {
                    value = nice_count(table_array[i][j]);
                } else if(typeof table_array[i][j] == 'string') {
                    value = nice_string(table_array[i][j]);
                } else {
                    value = '???';
                }
                tags = tags.concat(['<td>', value, '</td>']);
            }
            tags = tags.concat(['</tr>']);
        }

        tags = tags.concat(['</tbody>']);
        table.innerHTML = tags.join('');
        text_link.href = text_url;
        
        // Populate scores.
        show_efficiency_gap_score(plan, score_EG);
        show_sensitivity_test(plan, score_sense);
        
        if(plan_voteshare(plan) > .1) {
            hide_score_with_reason(score_PB,
                'This state’s vote share is '
                + nice_percent(.5 - plan_voteshare(plan)/2) + '/' + nice_percent(.5 + plan_voteshare(plan)/2) + '.'
                + ' Partisan Bias is shown only where the statewide vote share falls between 45% and 55%.'
                + ' Outside this range the metric’s assumptions are not plausible.');
            hide_score_with_reason(score_MM,
                'This state’s vote share is '
                + nice_percent(.5 - plan_voteshare(plan)/2) + '/' + nice_percent(.5 + plan_voteshare(plan)/2) + '.'
                + ' Mean-Median Difference is shown only where the statewide vote share falls between 45% and 55%.'
                + ' Outside this range the metric’s assumptions are not plausible.');
        } else {
            show_partisan_bias_score(plan, score_PB);
            show_mean_median_score(plan, score_MM);
        }

        // Go on to load the map.
        load_plan_map(map_url, map_div, plan);
    }

    request.onload = function()
    {
        if(request.status >= 200 && request.status < 400)
        {
            // Returns a dictionary with a list of districts
            var data = JSON.parse(request.responseText),
                modified_at = new Date(request.getResponseHeader('Last-Modified'));
            console.log('Loaded plan:', data);
            on_loaded_score(data, modified_at);
            return;
        }
        
        show_message('The district plan failed to load.', score_section, message_section);
    };

    request.onerror = function() { /* There was a connection error of some sort */ };
    request.send();
}

function load_plan_map(url, div, plan)
{
    var request = new XMLHttpRequest();
    request.open('GET', url, true);

    function on_loaded_geojson(data)
    {
        var geojson = L.geoJSON(data, {
            style: function(feature)
            {
                var district = plan.districts[data.features.indexOf(feature)];
                return { weight: 2, fillOpacity: .5, color: which_district_color(district, plan) };
            }
            });

        console.log('GeoJSON bounds:', geojson.getBounds());

        // Initialize the map on the passed div in the middle of the ocean
        var map = L.map(div, {
            scrollWheelZoom: false,
            center: [0, 0],
            zoom: 8
        });

        var pane = map.createPane('labels');
        pane.style.zIndex = 650; // http://leafletjs.com/examples/map-panes/
        pane.style.pointerEvents = 'none';

        // Add Toner tiles for base map
        L.tileLayer('https://cartodb-basemaps-{s}.global.ssl.fastly.net/light_nolabels/{z}/{x}/{y}{r}.png', {
            attribution: '&copy;<a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>, &copy;<a href="https://carto.com/attribution">CARTO</a>',
            maxZoom: 18
        }).addTo(map);

        // Add a GeoJSON layer and fit it into view
        geojson.addTo(map);
        map.fitBounds(geojson.getBounds());

        // Add Toner label tiles for base map
        L.tileLayer('https://stamen-tiles.a.ssl.fastly.net/toner-labels/{z}/{x}/{y}{r}.png', {
            attribution: '&copy;<a href="http://stamen.com/">Stamen</a>',
            pane: 'labels',
            maxZoom: 18
        }).addTo(map);
    }

    request.onload = function()
    {
        if(request.status >= 200 && request.status < 400)
        {
            // Returns a GeoJSON dictionary
            var data = JSON.parse(request.responseText);
            console.log('Loaded map:', data);
            on_loaded_geojson(data);
        }
    };

    request.onerror = function() { /* There was a connection error of some sort */ };
    request.send();
}

// Export functions for testing
if(typeof module !== 'undefined' && module.exports)
{
    module.exports = {
        format_url: format_url, nice_count: nice_count, nice_string: nice_string,
        nice_percent: nice_percent, nice_gap: nice_gap, date_age: date_age,
        what_score_description_html: what_score_description_html,
        which_score_summary_name: which_score_summary_name,
        which_score_column_names: which_score_column_names,
        which_district_color: which_district_color,
        plan_array: plan_array, get_description: get_description,
        update_vote_percentages: update_vote_percentages,
        update_acs2015_percentages: update_acs2015_percentages,
        update_acs2016_percentages: update_acs2016_percentages,
        update_cvap2015_percentages: update_cvap2015_percentages,
        update_heading_titles: update_heading_titles,
        get_explanation: get_explanation
        };
}
