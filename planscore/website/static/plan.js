function format_url(url_pattern, id)
{
    return url_pattern.replace('{id}', id);
}

function nice_count(value)
{
    if(value >= 1000) {
        return (value / 1000).toFixed(1) + 'k';
    } else if(value >= 100) {
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
        return ['Population 2015', 'Black Population 2015', 'Hispanic Population 2015',
            'Democratic Votes', 'Republican Votes', 'Polsby-Popper', 'Reock'];
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
    var summary_name = which_score_summary_name(plan);
    clear_element(score_EG);

    var new_h3 = document.createElement('h3'),
        new_score = document.createElement('p'),
        new_words = document.createElement('p');

    new_h3.innerText = 'Efficiency Gap';
    new_score.className = 'score'
    new_score.innerText = nice_percent(Math.abs(plan.summary[summary_name]));

    if(Math.abs(plan.summary[summary_name]) < .02) {
        new_words.innerText = (nice_gap(plan.summary[summary_name])
            + ' is close to zero.');
    } else if(Math.abs(plan.summary[summary_name]) < .04) {
        new_words.innerText = (nice_gap(plan.summary[summary_name])
            + ' is well within 7% threshold.');
    } else if(Math.abs(plan.summary[summary_name]) < .07) {
        new_words.innerText = (nice_gap(plan.summary[summary_name])
            + ' is within 7% threshold.');
    } else if(Math.abs(plan.summary[summary_name]) < .09) {
        new_words.innerText = (nice_gap(plan.summary[summary_name])
            + ' is outside 7% threshold.');
    } else {
        new_words.innerText = (nice_gap(plan.summary[summary_name])
            + ' is far outside 7% threshold.');
    }

    score_EG.appendChild(new_h3);
    score_EG.appendChild(new_score);
    score_EG.appendChild(new_words);
}

function show_partisan_bias_score(plan, score_PB)
{
    var partisan_bias = plan.summary['Partisan Bias'];
    clear_element(score_PB);

    var new_h3 = document.createElement('h3'),
        new_score = document.createElement('p'),
        new_words = document.createElement('p');

    new_h3.innerText = 'Partisan Bias';
    new_score.className = 'score'
    new_score.innerText = nice_percent(Math.abs(partisan_bias));
    new_words.innerText = nice_gap(partisan_bias) + '.';

    score_PB.appendChild(new_h3);
    score_PB.appendChild(new_score);
    score_PB.appendChild(new_words);
}

function show_sensitivity_test(plan, score_sense)
{
    Highcharts.chart(score_sense, {
        chart: { type: 'line' },
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

/*
 * Return a rows * columns matrix representing a scored plan table
 */
function plan_array(plan)
{
    var fields = ['Population 2015', 'Black Population 2015', 'Hispanic Population 2015',
            'Democratic Votes', 'Republican Votes', 'Polsby-Popper', 'Reock'];

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
    
    return all_rows;
}

function load_plan_score(url, message_section, score_section,
    description, table, score_EG, score_PB, score_sense, map_url, map_div)
{
    var request = new XMLHttpRequest();
    request.open('GET', url, true);

    show_message('Loading district plan…', score_section, message_section);

    function on_loaded_score(plan, modified_at)
    {
        if(which_score_summary_name(plan) === null) {
            show_message('District plan failed to load.', score_section, message_section);
            return;

        } else {
            hide_message(score_section, message_section);
        }

        // Clear out and repopulate description.
        clear_element(description);
        
        if(plan['start_time'])
        {
            modified_at = new Date(plan['start_time'] * 1000);
        }

        //description.innerHTML = what_score_description_html(plan);
        //description.appendChild(document.createElement('br'));
        description.appendChild(document.createElement('i'));
        description.lastChild.appendChild(document.createTextNode(
            (date_age(modified_at) > 86400)
                ? 'Uploaded on '+ modified_at.toLocaleDateString()
                : 'Uploaded at '+ modified_at.toLocaleString()));

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
        
        // Populate scores.
        show_efficiency_gap_score(plan, score_EG);
        show_partisan_bias_score(plan, score_PB);
        show_sensitivity_test(plan, score_sense);

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
        }
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
        plan_array: plan_array
        };
}
