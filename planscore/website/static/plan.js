const SHY_COLUMN = 'PlanScore:ShyColumn';

var FIELDS = [
    'Population 2010',
    'Population 2015',
    'Population 2016',
    'Population 2018',
    'Population 2019',
    'Population 2020 ACS',
    'Population 2020',
    'Black Population 2015',
    'Hispanic Population 2015',
    'Black Population 2016',
    'Hispanic Population 2016',
    'Black Population 2018',
    'Hispanic Population 2018',
    'Black Population 2019',
    'Hispanic Population 2019',
    'Asian Population 2019',
    'Black Population 2020 ACS',
    'Hispanic Population 2020 ACS',
    'Asian Population 2020 ACS',
    'Black Population 2020',
    'Hispanic Population 2020',
    'Asian Population 2020',
    //'Citizen Voting-Age Population 2015',
    'Black Citizen Voting-Age Population 2015',
    'Hispanic Citizen Voting-Age Population 2015',
    //'Citizen Voting-Age Population 2018',
    'Black Citizen Voting-Age Population 2018',
    'Hispanic Citizen Voting-Age Population 2018',
    'Citizen Voting-Age Population 2019',
    'Hispanic Citizen Voting-Age Population 2019',
    'Black Citizen Voting-Age Population 2019',
    'Asian Citizen Voting-Age Population 2019',
    'American Indian or Alaska Native Citizen Voting-Age Population 2019',
    'Citizen Voting-Age Population 2020 ACS',
    'Hispanic Citizen Voting-Age Population 2020 ACS',
    'Black Citizen Voting-Age Population 2020 ACS',
    'Asian Citizen Voting-Age Population 2020 ACS',
    'American Indian or Alaska Native Citizen Voting-Age Population 2020 ACS',
    'Citizen Voting-Age Population 2023 ACS',
    'Hispanic Citizen Voting-Age Population 2023 ACS',
    'Black Citizen Voting-Age Population 2023 ACS',
    'Asian Citizen Voting-Age Population 2023 ACS',
    'American Indian or Alaska Native Citizen Voting-Age Population 2023 ACS',
    'Democratic Wins',
    'Democratic Votes',
    'Republican Votes',
    'Vote Swing',
    'US President 2024 - DEM',
    'US President 2024 - REP',
    'US President 2020 - DEM',
    'US President 2020 - REP',
    'US President 2016 - DEM',
    'US President 2016 - REP',
    /*
    'US Senate 2024 - DEM',
    'US Senate 2024 - REP',
    'US Senate 2022 - DEM',
    'US Senate 2022 - REP',
    'US Senate 2020 - DEM',
    'US Senate 2020 - REP',
    'US Senate 2018 - DEM',
    'US Senate 2018 - REP',
    'US Senate 2016 - DEM',
    'US Senate 2016 - REP',
    */
    /*, 'Polsby-Popper', 'Reock'*/
];

const votesFieldToDisplayStr = {
    'Democratic Votes': 'Democratic Votes',
    'Republican Votes': 'Republican Votes',
    'US President 2016 - DEM': 'Clinton (D) 2016',
    'US President 2016 - REP': 'Trump (R) 2016',
    'US President 2020 - DEM': 'Biden (D) 2020',
    'US President 2020 - REP': 'Trump (R) 2020',
    'US President 2024 - DEM': 'Harris (D) 2024',
    'US President 2024 - REP': 'Trump (R) 2024',
    'US Senate 2016 - DEM': 'U.S.&nbsp;Sen. Dem. 2016',
    'US Senate 2016 - REP': 'U.S.&nbsp;Sen. Rep. 2016',
    'US Senate 2018 - DEM': 'U.S.&nbsp;Sen. Dem. 2018',
    'US Senate 2018 - REP': 'U.S.&nbsp;Sen. Rep. 2018',
    'US Senate 2020 - DEM': 'U.S.&nbsp;Sen. Dem. 2020',
    'US Senate 2020 - REP': 'U.S.&nbsp;Sen. Rep. 2020',
    'US Senate 2022 - DEM': 'U.S.&nbsp;Sen. Dem. 2022',
    'US Senate 2022 - REP': 'U.S.&nbsp;Sen. Rep. 2022',
    'US Senate 2024 - DEM': 'U.S.&nbsp;Sen. Dem. 2024',
    'US Senate 2024 - REP': 'U.S.&nbsp;Sen. Rep. 2024',
};

const fieldSubstringToDisplayStr = {
    'Black Citizen Voting-Age Population': 'Non-Hisp. Black CVAP',
    'Asian Citizen Voting-Age Population': 'Non-Hisp. Asian CVAP',
    'American Indian or Alaska Native Citizen Voting-Age Population': 'Non-Hisp. Native CVAP',
    'Citizen Voting-Age Population': 'CVAP',
    'Population': 'Pop.',
    '2020 ACS': '2020',
    '2023 ACS': '2023',
};

const months = [
  'Jan. ',
  'Feb. ',
  'Mar. ',
  'Apr. ',
  'May ',
  'Jun. ',
  'Jul. ',
  'Aug. ',
  'Sep. ',
  'Oct. ',
  'Nov. ',
  'Dec. '
];

// Keep track of substring renames for adding tooltips
const renamedHeadingToOrigField = new Map();


var BLUE_COLOR_HEX = '#4D90D1',
    RED_COLOR_HEX = '#D45557',
    LEAN_BLUE_COLOR_HEX = '#6D8AB1',
    LEAN_RED_COLOR_HEX = '#B56E6B',
    BLUEISH_COLOR_HEX = '#6D8AB0',
    REDDISH_COLOR_HEX = '#B56E6A',
    UNKNOWN_COLOR_HEX = '#838383';

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

function partisan_suffix(value)
{
    if(isNaN(value) || value == 0) {
        return '';
    }
    
    return '&nbsp;' + (value > 0 ? 'D' : 'R');
}

function nice_percent(value)
{
    if(isNaN(value)) {
        return '–';
    }
    
    return (100 * value).toFixed(1) + '%';
}

function nice_round_percent(value)
{
    if(isNaN(value)) {
        return '–';
    } else if(value < .01) {
        return '<1%';
    } else if(value > .99) {
        return '>99%';
    } else {
        return (100 * value).toFixed(0) + '%';
    }
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

function nice_vote_swing(value)
{
    if (value < -0.0955) {
        return `R+${(value * -100).toFixed(0)}`;
    } else if (value > 0.0955) {
        return `D+${(value * 100).toFixed(0)}`;
    } else if (value < 0) {
        return `R+${(value * -100).toFixed(1)}`;
    } else if (value > 0) {
        return `D+${(value * 100).toFixed(1)}`;
    }
    return '–';
}

function adjust_scenario_stats(data)
{
    if (data.dimensions.length != 3) {
        throw new Error("Unexpected number of dimensions");
    }

    // Adjust statistics to represent real values
    // All scenario stat values past [0][0] are diffs atop [0][0] to save bytes
    for (var i = 0; i < data[data.dimensions[0]].length; i++) {
        for (var j = 0; j < data[data.dimensions[1]].length; j++) {
            if (i > 0 || j > 0) {
                for (var k = 0; k < data[data.dimensions[2]].length; k++) {
                    for (var s in data.statistics) {
                        var stat = data.statistics[s];
                        stat[i][j][k] = stat[0][0][k] + stat[i][j][k];
                    }
                }
            }
        }
    }
}

function create_scenario_plan(original_plan, scenarios, vote_swing_index)
{
    // Special case: 0.0 swing (index 12) returns original plan unchanged
    if (vote_swing_index === 12) {
        return original_plan;
    }

    // Create a deep copy of the plan
    var mutated_plan = JSON.parse(JSON.stringify(original_plan));

    // Update each district with scenario data
    for (var district_index = 0; district_index < mutated_plan.districts.length; district_index++) {
        // Get incumbent scenario for this district (e.g., 'O', 'D', 'R')
        var incumbent_code = original_plan.incumbents[district_index];

        // Find the index in scenarios.incumbents array
        var incumbent_index = scenarios.incumbents.indexOf(incumbent_code);

        if (incumbent_index === -1) {
            console.warn('Unknown incumbent code:', incumbent_code, 'for district', district_index);
            continue;
        }

        // Update Democratic Votes
        if (scenarios.statistics['Democratic Votes']) {
            mutated_plan.districts[district_index].totals['Democratic Votes'] =
                scenarios.statistics['Democratic Votes'][vote_swing_index][incumbent_index][district_index];
        }

        // Update Republican Votes
        if (scenarios.statistics['Republican Votes']) {
            mutated_plan.districts[district_index].totals['Republican Votes'] =
                scenarios.statistics['Republican Votes'][vote_swing_index][incumbent_index][district_index];
        }

        // Update Democratic Wins
        if (scenarios.statistics['Democratic Wins']) {
            mutated_plan.districts[district_index].totals['Democratic Wins'] =
                scenarios.statistics['Democratic Wins'][vote_swing_index][incumbent_index][district_index];
        }
    }

    return mutated_plan;
}

function setup_scenario_interactivity(original_plan, scenarios, scenario_adjustments_form, districts_table)
{
    // Get all radio buttons in the form
    var radios = scenario_adjustments_form.querySelectorAll('input[name="vote-swing"]');

    // Set the 0.0 radio button as checked initially
    for (var i = 0; i < radios.length; i++) {
        if (parseFloat(radios[i].value) === 0.0) {
            radios[i].checked = true;
            break;
        }
    }

    // Add change listener to all radio buttons
    for (var i = 0; i < radios.length; i++) {
        radios[i].addEventListener('change', function(event) {
            // Get the selected vote swing value
            var vote_swing = parseFloat(event.target.value);

            // Find the index in scenarios.vote_swings array
            var vote_swing_index = scenarios.vote_swings.indexOf(vote_swing);

            if (vote_swing_index === -1) {
                console.error('Vote swing not found in scenarios:', vote_swing);
                return;
            }

            // Create mutated plan with scenario data
            var mutated_plan = create_scenario_plan(original_plan, scenarios, vote_swing_index);

            // Update the districts table
            populate_districts_table(mutated_plan, districts_table);
        });
    }
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
    if(typeof plan.summary['Efficiency Gap Positives'] === 'number'
    || typeof plan.summary['Efficiency Gap SD'] === 'number')
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
    // Colors from http://chromatron.s3-website-us-east-1.amazonaws.com/#eNpVz8EKgzAQBNB/mV5z2JhsYvIrpQc1tkilgqXQIv57NYkNZa77mNkF3TRO8xP+vGAI8CRwHcYRHicdHAUJgTe8dizwgZdWCszwNa0iAVlA0MxsE6ikSsC4CCT9RFVErfYkodjlCopCmwOoAlo2vWkyIPUHTHUAXYAJddNSfkLavMlGwG69CLRNd7/N0+sR4iLas90Pj9Bvhtcv8ANJtQ==

    var totals = district.totals;

    if(typeof totals['Democratic Wins'] === 'number')
    {
        if(totals['Democratic Wins'] > .79 && plan.model.house == 'statesenate') {
            // for p(Dem win)>0.5 & state senate, chance of flip in a decade = p^3
            return BLUE_COLOR_HEX;
        } else if (totals['Democratic Wins'] > .87) {
            // for p(Dem win)>0.5 & lower chamber/US House, chance of flip in a decade = p^5
            return BLUE_COLOR_HEX;
        } else if (totals['Democratic Wins'] < .21 && plan.model.house == 'statesenate') {
            // for p(Dem win)<0.5 & state senate, chance of flip in a decade = (1-p)^3
            return RED_COLOR_HEX;
        } else if (totals['Democratic Wins'] < .13) {
            // for p(Dem win)<0.5 & lower chamber/US House, chance of flip in a decade = (1-p)^5
            return RED_COLOR_HEX;
        } else if (totals['Democratic Wins'] > .5) {
            return LEAN_BLUE_COLOR_HEX;
        } else if (totals['Democratic Wins'] < .5) {
            return LEAN_RED_COLOR_HEX;
        } else {
            return UNKNOWN_COLOR_HEX;
        }
    }

    if(typeof plan.summary['Efficiency Gap Positives'] === 'number'
    || typeof plan.summary['Efficiency Gap SD'] === 'number')
    {
        var dem_votes = totals['Democratic Votes'],
            rep_votes = totals['Republican Votes'],
            dem_votes_sd = totals['Democratic Votes SD'],
            rep_votes_sd = totals['Republican Votes SD'];

        if((dem_votes - dem_votes_sd*2) > (rep_votes + rep_votes_sd*2)) {
            return BLUE_COLOR_HEX;
        } else if((dem_votes + dem_votes_sd*2) < (rep_votes - rep_votes_sd*2)) {
            return RED_COLOR_HEX;
        } else if((dem_votes - dem_votes_sd) > (rep_votes + rep_votes_sd)) {
            return BLUEISH_COLOR_HEX;
        } else if((dem_votes + dem_votes_sd) < (rep_votes - rep_votes_sd)) {
            return REDDISH_COLOR_HEX;
        } else {
            return UNKNOWN_COLOR_HEX;
        }
    }

    if(typeof plan.summary['US House Efficiency Gap'] === 'number')
    {
        if(totals['US House Dem Votes'] > totals['US House Rep Votes']) {
            return BLUE_COLOR_HEX;
        } else {
            return RED_COLOR_HEX;
        }
    }

    if(typeof plan.summary['Efficiency Gap'] === 'number')
    {
        if(totals['Blue Votes'] > totals['Red Votes']) {
            return BLUE_COLOR_HEX;
        } else {
            return RED_COLOR_HEX;
        }
    }

    // neutral gray
    return '#808080';
}

function get_seatshare_array(plan)
{
    if(!('Democratic Wins' in plan.districts[0].totals))
    {
        return undefined;
    }

    var box_colors = [],
        box_districts = plan.districts.filter((d) => (d['is_counted'] !== false)),
        red_votes = 0,
        blue_votes = 0,
        seat_share = 0;

    box_districts.sort((d1, d2) => (d2.totals['Democratic Wins'] - d1.totals['Democratic Wins']));

    for(var i = 0; i < box_districts.length; i++)
    {
        var color = which_district_color(box_districts[i], plan),
            last_color = color;
        
        box_colors.push(color);
        red_votes += box_districts[i].totals['Republican Votes'];
        blue_votes += box_districts[i].totals['Democratic Votes'];
        seat_share += box_districts[i].totals['Democratic Wins'];
    }
    
    seat_share /= box_districts.length;
    
    return {
        colors: box_colors,
        red_votes: red_votes,
        blue_votes: blue_votes,
        total_votes: red_votes + blue_votes,
        seat_share: seat_share,
    };
}

function construct_districts_table(plan, districts_table)
{
    // Build table structure using DOM APIs, without populating data
    var table_array = plan_array(plan);
    if (!table_array) {
        return;
    }

    const has_incumbency = plan_has_incumbency(plan);

    // Helper function to determine if column should be left-aligned
    function should_align_left(col_index) {
        return col_index == 1 && has_incumbency;
    }

    // Helper function to get tooltip for renamed headings
    function get_tooltip(title) {
        if (!renamedHeadingToOrigField.has(title)) return '';
        return renamedHeadingToOrigField.get(title);
    }

    // Clear existing content
    districts_table.innerHTML = '';

    // Create table element with classes
    const table = document.createElement('table');
    table.className = 'table table-hover';
    table.id = 'districts';

    // Create thead
    const thead = document.createElement('thead');
    const header_row = document.createElement('tr');

    for (var j = 0; j < table_array[0].length; j++) {
        const heading_title = table_array[0][j];
        if (heading_title == SHY_COLUMN) {
            continue;
        }

        const th = document.createElement('th');
        if (should_align_left(j)) {
            th.className = 'ltxt';
        }

        const tooltip = get_tooltip(heading_title);
        if (tooltip) {
            th.title = tooltip;
        }

        // Use innerHTML for headers since they may contain HTML tags like <sup>
        th.innerHTML = heading_title;
        th.dataset.columnIndex = j;
        header_row.appendChild(th);
    }

    thead.appendChild(header_row);
    table.appendChild(thead);

    // Create tbody
    const tbody = document.createElement('tbody');

    for (var i = 1; i < table_array.length; i++) {
        const tr = document.createElement('tr');
        tr.dataset.districtIndex = i - 1;

        for (var j = 0; j < table_array[i].length; j++) {
            const heading_title = table_array[0][j];
            if (heading_title == SHY_COLUMN) {
                continue;
            }

            const cell = j == 0 ? document.createElement('th') : document.createElement('td');
            if (should_align_left(j)) {
                cell.className = 'ltxt';
            }

            cell.dataset.columnIndex = j;
            tr.appendChild(cell);
        }

        tbody.appendChild(tr);
    }

    table.appendChild(tbody);
    districts_table.appendChild(table);
}

function populate_districts_table(plan, districts_table)
{
    // Populate table cells with actual data
    var table_array = plan_array(plan);
    if (!table_array) {
        return;
    }

    const tbody = districts_table.querySelector('tbody');
    if (!tbody) {
        return;
    }

    const rows = tbody.querySelectorAll('tr');

    for (var i = 0; i < rows.length; i++) {
        const tr = rows[i];
        const table_row_index = i + 1; // +1 because table_array[0] is headers
        const district_index = parseInt(tr.dataset.districtIndex);

        // Determine row class and title
        var row_class = 'no-votes';
        var row_title = `District ${table_array[table_row_index][0]} has no votes and does not count toward partisan scores`;

        // Check if any vote field has a value > 0
        for (var j = 0; j < table_array[table_row_index].length; j++) {
            for (var p in votesFieldToDisplayStr) {
                if (table_array[0][j] == votesFieldToDisplayStr[p] && table_array[table_row_index][j] > 0) {
                    row_class = 'has-votes';
                    row_title = '';
                }
            }
        }

        // Check is_counted flag
        if (plan.districts[district_index]['is_counted'] === false) {
            row_class = 'no-votes';
            row_title = `District ${table_array[table_row_index][0]} has insufficient votes and does not count toward partisan scores`;
        }

        tr.className = row_class;
        tr.title = row_title;

        // Populate cells
        const cells = tr.querySelectorAll('td, th');
        var cell_index = 0;

        for (var j = 0; j < table_array[table_row_index].length; j++) {
            const heading_title = table_array[0][j];
            if (heading_title == SHY_COLUMN) {
                continue;
            }

            var value;
            var is_string = false;
            if (typeof table_array[table_row_index][j] == 'number') {
                value = nice_count(table_array[table_row_index][j]);
            } else if (typeof table_array[table_row_index][j] == 'string') {
                value = nice_string(table_array[table_row_index][j]);
                is_string = true;
            } else if (typeof table_array[table_row_index][j] == 'boolean') {
                value = table_array[table_row_index][j] ? 'Yes' : 'No';
            } else {
                value = '???';
            }

            if (cells[cell_index]) {
                // Use innerHTML for strings since nice_string() returns HTML entities
                if (is_string) {
                    cells[cell_index].innerHTML = value;
                } else {
                    cells[cell_index].textContent = value;
                }
            }
            cell_index++;
        }
    }
}

function construct_seatshare_graphic(plan, districts_table)
{
    if(!('Democratic Wins' in plan.districts[0].totals))
    {
        return null;
    }

    // Create container div
    var container = document.createElement('div');
    container.className = 'seatshare-graphic';

    // Create span elements for each district (structure only)
    for(var i = 0; i < plan.districts.filter((d) => (d['is_counted'] !== false)).length; i++)
    {
        var span = document.createElement('span');
        span.className = 'seatshare-box';
        span.dataset.seatIndex = i;
        span.textContent = ' ';
        container.appendChild(span);
    }

    // Create line break
    container.appendChild(document.createElement('br'));

    // Create text container for seat share vs vote share
    var text_span = document.createElement('span');
    text_span.className = 'seatshare-text';
    container.appendChild(text_span);

    // Insert after districts table
    districts_table.parentNode.parentNode.insertBefore(container, districts_table.parentNode.nextSibling);

    return container;
}

function populate_seatshare_graphic(plan)
{
    var container = document.querySelector('.seatshare-graphic');
    if(!container) {
        return;
    }

    var seatshare_array = get_seatshare_array(plan);
    if(seatshare_array === undefined) {
        return;
    }

    var spans = container.querySelectorAll('.seatshare-box');
    var last_color = false;

    // Update each seat box with colors and widths
    for(var i = 0; i < seatshare_array.colors.length; i++)
    {
        var color = seatshare_array.colors[i],
            gutter = (last_color && color != last_color) ? '3px' : '1px',
            width = `calc(${100/(seatshare_array.colors.length)}% - ${gutter})`,
            background = color;

        if(color == LEAN_BLUE_COLOR_HEX) {
            background += ' url("/static/lean-blue-pattern.png")';
        } else if(color == LEAN_RED_COLOR_HEX) {
            background += ' url("/static/lean-red-pattern.png")';
        }

        if(seatshare_array.colors.length > 50)
        {
            background += ' fixed';
        }

        spans[i].style.width = width;
        spans[i].style.marginLeft = gutter;
        spans[i].style.background = background;

        last_color = color;
    }

    // Update text with seat share and vote share percentages
    var text_span = container.querySelector('.seatshare-text');
    text_span.innerHTML = `
        Predicted
        ${nice_round_percent(seatshare_array.seat_share)} D
        / ${nice_round_percent(1 - seatshare_array.seat_share)} R
        seat share across scenarios<sup>*</sup>
        vs.
        ${nice_round_percent(seatshare_array.blue_votes / (seatshare_array.total_votes))} D
        / ${nice_round_percent(seatshare_array.red_votes / (seatshare_array.total_votes))} R
        vote share.
    `;
}

function construct_efficiency_gap_score(score_EG)
{
    for(node = score_EG.firstChild; node = node.nextSibling; node)
    {
        if(node.nodeName == 'H3') {
            // Add a span for the value
            var value_span = document.createElement('span');
            value_span.className = 'score-value';
            value_span.dataset.metric = 'eg';
            node.appendChild(document.createTextNode(': '));
            node.appendChild(value_span);

        } else if(node.nodeName == 'DIV') {
            // Mark for chart creation
            node.dataset.metric = 'eg';
            node.dataset.chartType = 'bellchart';

        } else if(node.nodeName == 'P') {
            // Mark for description population
            node.dataset.metric = 'eg';
            node.dataset.contentType = 'description';
        }
    }
}

function populate_efficiency_gap_score(plan, score_EG)
{
    var summary_name = which_score_summary_name(plan),
        gap = plan.summary[summary_name],
        gap_amount = nice_percent(Math.abs(gap)) + partisan_suffix(gap);

    for(node = score_EG.firstChild; node = node.nextSibling; node)
    {
        if(node.nodeName == 'H3') {
            var value_span = node.querySelector('.score-value[data-metric="eg"]');
            if(value_span) {
                value_span.innerHTML = gap_amount;
            }

        } else if(node.nodeName == 'DIV' && node.dataset.metric == 'eg') {
            drawBiasBellChart('eg', gap, node.id,
                (plan.model ? plan.model.house : 'ushouse'), 'plan');

        } else if(node.nodeName == 'P' && node.dataset.metric == 'eg') {
            var win_party = (gap < 0 ? 'Republican' : 'Democratic'),
                win_partisans = (gap < 0 ? 'Republicans' : 'Democrats'),
                lose_party = (gap < 0 ? 'Democratic' : 'Republican');

            clear_element(node);

            if(typeof plan.summary['Efficiency Gap Positives'] === 'number') {
                var positives = (gap < 0
                    ? (1 - plan.summary['Efficiency Gap Positives'])
                    : plan.summary['Efficiency Gap Positives']);

                node.innerHTML = [
                    'Votes for', win_party, 'candidates are expected to be inefficient at a rate',
                    gap_amount, 'lower than votes for', lose_party, 'candidates,',
                    'favoring', win_partisans,
                    'in', nice_round_percent(positives), 'of predicted scenarios.<sup>*</sup>',
                    '<a href="' + window.eg_metric_url + '">Learn more <i class="glyphicon glyphicon-chevron-right" style="font-size:0.8em;"></i></a>'
                    ].join(' ');

            } else {
                var gap_error = plan.summary['Efficiency Gap SD'];

                node.innerHTML = [
                    'Votes for', win_party, 'candidates are expected to be inefficient at a rate',
                    gap_amount+'&nbsp;(±'+nice_percent(gap_error*2)+')',
                    'lower than votes for', lose_party, 'candidates.',
                    '<a href="' + window.eg_metric_url + '">Learn more <i class="glyphicon glyphicon-chevron-right" style="font-size:0.8em;"></i></a>'
                    ].join(' ');
            }
        }
    }
}

function construct_declination2_score(score_DEC2)
{
    for(node = score_DEC2.firstChild; node = node.nextSibling; node)
    {
        if(node.nodeName == 'H3') {
            // Add a span for the value
            var value_span = document.createElement('span');
            value_span.className = 'score-value';
            value_span.dataset.metric = 'd2';
            node.appendChild(document.createTextNode(': '));
            node.appendChild(value_span);

        } else if(node.nodeName == 'DIV') {
            // Mark for chart creation
            node.dataset.metric = 'd2';
            node.dataset.chartType = 'bellchart';

        } else if(node.nodeName == 'P') {
            // Mark for description population
            node.dataset.metric = 'd2';
            node.dataset.contentType = 'description';
        }
    }
}

function populate_declination2_score(plan, score_DEC2)
{
    var declination = plan.summary['Declination'],
        dec2_amount = (Math.round(Math.abs(declination) * 100) / 100) + partisan_suffix(declination);

    for(node = score_DEC2.firstChild; node = node.nextSibling; node)
    {
        if(node.nodeName == 'H3') {
            var value_span = node.querySelector('.score-value[data-metric="d2"]');
            if(value_span) {
                value_span.innerHTML = dec2_amount;
            }

        } else if(node.nodeName == 'DIV' && node.dataset.metric == 'd2') {
            drawBiasBellChart('d2', declination, node.id,
                (plan.model ? plan.model.house : 'ushouse'), 'plan');

        } else if(node.nodeName == 'P' && node.dataset.metric == 'd2') {
            var win_party = (declination < 0 ? 'Republican' : 'Democratic'),
                win_partisans = (declination < 0 ? 'Republicans' : 'Democrats'),
                lose_party = (declination < 0 ? 'Democratic' : 'Republican');

            clear_element(node);

            if(typeof plan.summary['Declination Positives'] === 'number')
            {
                var positives = (declination < 0
                    ? (1 - plan.summary['Declination Positives'])
                    : plan.summary['Declination Positives']);

                node.innerHTML = `
                    The difference between mean ${lose_party} vote share in
                    ${lose_party} districts and mean ${win_party} vote share in
                    ${win_party} districts along with the relative fraction of
                    seats won by each party leads to a declination that favors
                    ${win_partisans} in ${nice_round_percent(positives)} of
                    predicted scenarios.<sup>*</sup>
                    <a href="${window.d2_metric_url}">Learn more <i class="glyphicon glyphicon-chevron-right" style="font-size:0.8em;"></i></a>
                    `;
            }
        }
    }
}

function construct_partisan_bias_score(score_PB)
{
    for(node = score_PB.firstChild; node = node.nextSibling; node)
    {
        if(node.nodeName == 'H3') {
            // Add a span for the value
            var value_span = document.createElement('span');
            value_span.className = 'score-value';
            value_span.dataset.metric = 'pb';
            node.appendChild(document.createTextNode(': '));
            node.appendChild(value_span);

        } else if(node.nodeName == 'DIV') {
            // Mark for chart creation
            node.dataset.metric = 'pb';
            node.dataset.chartType = 'bellchart';

        } else if(node.nodeName == 'P') {
            // Mark for description population
            node.dataset.metric = 'pb';
            node.dataset.contentType = 'description';
        }
    }
}

function populate_partisan_bias_score(plan, score_PB)
{
    var bias = plan.summary['Partisan Bias'],
        bias_amount = nice_percent(Math.abs(bias)) + partisan_suffix(bias);

    for(node = score_PB.firstChild; node = node.nextSibling; node)
    {
        if(node.nodeName == 'H3') {
            var value_span = node.querySelector('.score-value[data-metric="pb"]');
            if(value_span) {
                value_span.innerHTML = bias_amount;
            }

        } else if(node.nodeName == 'DIV' && node.dataset.metric == 'pb') {
            drawBiasBellChart('pb', bias, node.id,
                (plan.model ? plan.model.house : 'ushouse'), 'plan');

        } else if(node.nodeName == 'P' && node.dataset.metric == 'pb') {
            var win_party = (bias < 0 ? 'Republicans' : 'Democrats'),
                win_partisans = (bias < 0 ? 'Republicans' : 'Democrats');

            clear_element(node);

            if(typeof plan.summary['Partisan Bias Positives'] === 'number') {
                var positives = (bias < 0
                    ? (1 - plan.summary['Partisan Bias Positives'])
                    : plan.summary['Partisan Bias Positives']);

                node.innerHTML = [
                    win_party, 'would be expected to win', bias_amount,
                    'extra seats in a hypothetical, perfectly tied election,',
                    'favoring', win_partisans,
                    'in', nice_round_percent(positives), 'of predicted scenarios.<sup>*</sup>',
                    '<a href="' + window.pb_metric_url + '">Learn more <i class="glyphicon glyphicon-chevron-right" style="font-size:0.8em;"></i></a>'
                    ].join(' ');

            } else {
                var bias_error = plan.summary['Partisan Bias SD'];

                node.innerHTML = [
                    win_party, 'would be expected to win',
                    bias_amount+'&nbsp;(±'+nice_percent(bias_error*2)+')',
                    'extra seats in a hypothetical, perfectly tied election.',
                    '<a href="' + window.pb_metric_url + '">Learn more <i class="glyphicon glyphicon-chevron-right" style="font-size:0.8em;"></i></a>'
                    ].join(' ');
            }
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
            node.innerHTML = reason;
        }
    }
}

function construct_mean_median_score(score_MM)
{
    for(node = score_MM.firstChild; node = node.nextSibling; node)
    {
        if(node.nodeName == 'H3') {
            // Add a span for the value
            var value_span = document.createElement('span');
            value_span.className = 'score-value';
            value_span.dataset.metric = 'mm';
            node.appendChild(document.createTextNode(': '));
            node.appendChild(value_span);

        } else if(node.nodeName == 'DIV') {
            // Mark for chart creation
            node.dataset.metric = 'mm';
            node.dataset.chartType = 'bellchart';

        } else if(node.nodeName == 'P') {
            // Mark for description population
            node.dataset.metric = 'mm';
            node.dataset.contentType = 'description';
        }
    }
}

function populate_mean_median_score(plan, score_MM)
{
    var diff = plan.summary['Mean-Median'],
        diff_amount = nice_percent(Math.abs(diff)) + partisan_suffix(diff);

    for(node = score_MM.firstChild; node = node.nextSibling; node)
    {
        if(node.nodeName == 'H3') {
            var value_span = node.querySelector('.score-value[data-metric="mm"]');
            if(value_span) {
                value_span.innerHTML = diff_amount;
            }

        } else if(node.nodeName == 'DIV' && node.dataset.metric == 'mm') {
            drawBiasBellChart('mm', diff, node.id,
                (plan.model ? plan.model.house : 'ushouse'), 'plan');

        } else if(node.nodeName == 'P' && node.dataset.metric == 'mm') {
            var win_party = (diff < 0 ? 'Republican' : 'Democrat'),
                win_partisans = (diff < 0 ? 'Republicans' : 'Democrats');

            clear_element(node);

            if(typeof plan.summary['Mean-Median Positives'] === 'number') {
                var positives = (diff < 0
                    ? (1 - plan.summary['Mean-Median Positives'])
                    : plan.summary['Mean-Median Positives']);

                node.innerHTML = [
                    'The median', win_party, 'vote share is expected to be',
                    diff_amount, 'higher than the mean', win_party, 'vote share,',
                    'favoring', win_partisans,
                    'in', nice_round_percent(positives), 'of predicted scenarios.<sup>*</sup>',
                    '<a href="' + window.mm_metric_url + '">Learn more <i class="glyphicon glyphicon-chevron-right" style="font-size:0.8em;"></i></a>'
                    ].join(' ');

            } else {
                var diff_error = plan.summary['Mean-Median SD'];

                node.innerHTML = [
                    'The median', win_party, 'vote share is expected to be',
                    diff_amount+'&nbsp;(±'+nice_percent(diff_error*2)+')',
                    'higher than the mean', win_party, 'vote share.',
                    '<a href="' + window.mm_metric_url + '">Learn more <i class="glyphicon glyphicon-chevron-right" style="font-size:0.8em;"></i></a>'
                    ].join(' ');
            }
        }
    }
}

function construct_sensitivity_test(score_sense)
{
    // Create chart structure with empty data initially
    var chart = Highcharts.chart(score_sense, {
        chart: { type: 'line' },
        legend: { enabled: false },
        credits: { enabled: false },
        title: { text: null },
        series: [{
            name: 'Expected Efficiency Gap',
            data: [] // Empty data initially
        }],
        xAxis: {
            categories: ['+5 D', '+4 D', '+3 D', '+2 D', '+1 D', '0', '+1 R', '+2 R', '+3 R', '+4 R', '+5 R'],
            title: { text: 'Possible Vote Swing' }
        },
        yAxis: {
            title: { text: null },
            labels: {
                formatter: function()
                {
                    return [
                        Math.abs(this.value),
                        '% ',
                        (this.value == 0 ? '' : (this.value < 0 ? 'R' : 'D')),
                    ].join('');
                },
            },
        },
        plotOptions: {
            line: {
                dataLabels: { enabled: false },
                enableMouseTracking: false
            }
        }
    });

    // Store chart reference for later population
    score_sense._highchartsChart = chart;
}

function populate_sensitivity_test(plan, score_sense)
{
    var chart = score_sense._highchartsChart;
    if(!chart) {
        return;
    }

    var data = [
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
    ];

    // Update chart data
    chart.series[0].setData(data, true);
}

function show_message(text, score_section, message_section)
{
    // If showing the same message, just append an ellipsis.
    const match_el = Array.from(message_section.querySelectorAll('p'))
        .find(el => el.textContent.startsWith(text));

    if (match_el) {
        match_el.textContent += '…';
    } else {
        const el = document.createElement('p');
        el.textContent = text;
        message_section.append(el);
    }

    score_section.style.display = 'none';
    message_section.style.display = 'block';
}

function hide_message(score_section, message_section)
{
    score_section.style.display = 'block';
    message_section.style.display = 'none';
}

function construct_metrics_table(metrics_table)
{
    // Build table structure with all possible columns
    var thead = document.createElement('thead');
    var header_row = document.createElement('tr');

    var headers = [
        'Metric',
        'Value',
        'Favors Democrats in this % of Scenarios<sup>*</sup>',
        'More Skewed than this % of Historical Plans<sup>‡</sup>',
        'More Pro-Democratic than this % of Historical Plans<sup>‡</sup>'
    ];

    headers.forEach((header_text, idx) => {
        var th = document.createElement('th');
        th.innerHTML = header_text;
        th.dataset.columnIndex = idx;
        if(idx >= 3) {
            th.dataset.percentRankColumn = 'true';
        }
        header_row.appendChild(th);
    });

    thead.appendChild(header_row);

    // Build tbody with rows for each metric
    var tbody = document.createElement('tbody');
    var metrics = [
        {name: 'Efficiency Gap', key: 'eg', url: 'eg_metric_url'},
        {name: 'Declination', key: 'd2', url: 'd2_metric_url'},
        {name: 'Partisan Bias', key: 'pb', url: 'pb_metric_url'},
        {name: 'Mean-Median Difference', key: 'mm', url: 'mm_metric_url'}
    ];

    metrics.forEach((metric) => {
        var row = document.createElement('tr');
        row.dataset.metric = metric.key;

        // Metric name cell
        var th = document.createElement('th');
        var link = document.createElement('a');
        link.href = window[metric.url];
        link.textContent = metric.name;
        th.appendChild(link);
        row.appendChild(th);

        // Create data cells (value, positives, percentrank_abs, percentrank_rel)
        for(var i = 0; i < 4; i++) {
            var td = document.createElement('td');
            td.dataset.columnIndex = i;
            if(i >= 2) {
                td.dataset.percentRankColumn = 'true';
            }
            row.appendChild(td);
        }

        tbody.appendChild(row);
    });

    metrics_table.appendChild(thead);
    metrics_table.appendChild(tbody);
}

function populate_metrics_table(plan, metrics_table)
{
    if(!('Efficiency Gap Absolute Percent Rank' in plan.summary))
    {
        metrics_table.parentNode.style.display = 'none';
        return;
    }

    metrics_table.parentNode.style.display = 'block';

    var eg_summary_name = which_score_summary_name(plan),
        eg_value = plan.summary[eg_summary_name],
        eg_win_party = (eg_value < 0 ? 'Republican' : 'Democratic'),
        eg_positives = plan.summary['Efficiency Gap Positives'],
        eg_percentrank_abs = plan.summary['Efficiency Gap Absolute Percent Rank'],
        eg_percentrank_rel = (eg_value < 0
            ? (1 - plan.summary['Efficiency Gap Relative Percent Rank'])
            : plan.summary['Efficiency Gap Relative Percent Rank']),
        dec2_value = plan.summary['Declination'],
        dec2_win_party = (dec2_value < 0 ? 'Republican' : 'Democratic'),
        dec2_positives = plan.summary['Declination Positives'],
        dec2_percentrank_abs = plan.summary['Declination Absolute Percent Rank'],
        dec2_percentrank_rel = (dec2_value < 0
            ? (1 - plan.summary['Declination Relative Percent Rank'])
            : plan.summary['Declination Relative Percent Rank']);

    if(plan_voteshare(plan) < .1 || location.hash.match(/\bshowall\b/)) {
        var pb_value = plan.summary['Partisan Bias'],
            pb_win_party = (pb_value < 0 ? 'Republican' : 'Democratic'),
            pb_display = `${nice_percent(Math.abs(pb_value))} Pro-${pb_win_party}`,
            pb_positives = nice_round_percent(plan.summary['Partisan Bias Positives']),
            pb_percentrank_abs = nice_round_percent(plan.summary['Partisan Bias Absolute Percent Rank']),
            pb_percentrank_rel = nice_round_percent(pb_value < 0
                ? (1 - plan.summary['Partisan Bias Relative Percent Rank'])
                : plan.summary['Partisan Bias Relative Percent Rank']),
            mmd_value = plan.summary['Mean-Median'],
            mmd_win_party = (mmd_value < 0 ? 'Republican' : 'Democratic'),
            mmd_display = `${nice_percent(Math.abs(mmd_value))} Pro-${mmd_win_party}`,
            mmd_positives = nice_round_percent(plan.summary['Mean-Median Positives']),
            mmd_percentrank_abs = nice_round_percent(plan.summary['Mean-Median Absolute Percent Rank']),
            mmd_percentrank_rel = nice_round_percent(mmd_value < 0
                ? (1 - plan.summary['Mean-Median Relative Percent Rank'])
                : plan.summary['Mean-Median Relative Percent Rank']);

    } else {
        var pb_display = 'N/A',
            pb_positives = 'N/A',
            pb_percentrank_abs = 'N/A',
            pb_percentrank_rel = 'N/A',
            mmd_display = 'N/A',
            mmd_positives = 'N/A',
            mmd_percentrank_abs = 'N/A',
            mmd_percentrank_rel = 'N/A';
    }

    // Determine if we show percent rank columns
    var has_percent_rank = (plan.summary['Efficiency Gap Absolute Percent Rank'] !== null);

    // Show/hide percent rank columns
    metrics_table.querySelectorAll('[data-percent-rank-column]').forEach(el => {
        el.style.display = has_percent_rank ? '' : 'none';
    });

    // Populate Efficiency Gap row
    var eg_row = metrics_table.querySelector('tr[data-metric="eg"]');
    var eg_cells = eg_row.querySelectorAll('td');
    eg_cells[0].textContent = `${nice_percent(Math.abs(eg_value))} Pro-${eg_win_party}`;
    eg_cells[1].textContent = nice_round_percent(eg_positives);
    if(has_percent_rank) {
        eg_cells[2].textContent = nice_round_percent(eg_percentrank_abs);
        eg_cells[3].textContent = nice_round_percent(eg_percentrank_rel);
    }

    // Populate/hide Declination row
    var d2_row = metrics_table.querySelector('tr[data-metric="d2"]');
    if(plan.summary['Declination Is Valid'] !== 0) {
        d2_row.style.display = '';
        var d2_cells = d2_row.querySelectorAll('td');
        d2_cells[0].textContent = `${Math.round(Math.abs(dec2_value) * 100)/100} Pro-${dec2_win_party}`;
        d2_cells[1].textContent = nice_round_percent(dec2_positives);
        if(has_percent_rank) {
            d2_cells[2].textContent = nice_round_percent(dec2_percentrank_abs);
            d2_cells[3].textContent = nice_round_percent(dec2_percentrank_rel);
        }
    } else {
        d2_row.style.display = 'none';
    }

    // Populate Partisan Bias row
    var pb_row = metrics_table.querySelector('tr[data-metric="pb"]');
    var pb_cells = pb_row.querySelectorAll('td');
    pb_cells[0].textContent = pb_display;
    pb_cells[1].textContent = pb_positives;
    if(has_percent_rank) {
        pb_cells[2].textContent = pb_percentrank_abs;
        pb_cells[3].textContent = pb_percentrank_rel;
    }

    // Populate Mean-Median row
    var mm_row = metrics_table.querySelector('tr[data-metric="mm"]');
    var mm_cells = mm_row.querySelectorAll('td');
    mm_cells[0].textContent = mmd_display;
    mm_cells[1].textContent = mmd_positives;
    if(has_percent_rank) {
        mm_cells[2].textContent = mmd_percentrank_abs;
        mm_cells[3].textContent = mmd_percentrank_rel;
    }
}

function construct_library_metadata(metadata_el)
{
    // The structure is already in HTML, just mark elements for population
    for(node = metadata_el.firstChild; node = node.nextSibling; node)
    {
        if(node.nodeName == 'DIV' && node.className == 'link-grid') {
            node.dataset.contentType = 'links';
        } else if(node.nodeName == 'DIV' && node.className == 'notes') {
            node.dataset.contentType = 'notes';
        }
    }
}

function populate_library_metadata(plan, metadata_el, geom_prefix)
{
    var links = [
        {
            text: 'Authoritative Link',
            href: plan.library_metadata['authoritative_link'],
            img: window.metadata_link_img_url,
            alt: "authoritative link for this plan"
        },
        {
            text: 'Preceding Enacted Plan',
            href: plan.library_metadata['predecessor_link'],
            img: window.metadata_arrow_img_url,
            alt: "link to the preceding enacted plan"
        },
        {
            text: 'Shapefile',
            href: plan.library_metadata['shapefile_file'],
            img: window.metadata_file_img_url,
            alt: "link to a shapefile download"
        },
        {
            text: 'Block Assignment File',
            href: plan.library_metadata['blockassign_file'],
            img: window.metadata_file_img_url,
            alt: "link to a block assignment file download"
        },
        {
            text: 'Preview GeoJSON',
            href: geom_prefix + plan.geometry_key,
            img: window.metadata_file_img_url,
            alt: "link to a geojson download"
        },
    ];

    for(node = metadata_el.firstChild; node = node.nextSibling; node)
    {
        if(node.nodeName == 'DIV' && node.dataset.contentType == 'links') {
            clear_element(node);

            for(var i = 0; i < links.length; i++)
            {
                if(!links[i].href)
                    continue;

                var a = document.createElement('a');
                a.href = links[i].href;
                a.innerHTML = `
                    ${links[i].text}
                    <img width="20" height="20" src="${links[i].img}" alt="${links[i].alt}"/>
                `;
                node.appendChild(a);
            }
        } else if(node.nodeName == 'DIV' && node.dataset.contentType == 'notes') {
            if(plan.library_metadata['notes']) {
                node.innerHTML = plan.library_metadata['notes'];
            } else {
                node.innerHTML = '<i>N/A</i>';
            }
        }
    }

    console.log(links);
}

function construct_ftva_race_scores(scores_FTVA)
{
    // Mark each score element for later population
    for(var i = 0; i < scores_FTVA.length; i++)
    {
        scores_FTVA[i].dataset.ftvaIndex = i;
    }
}

function populate_ftva_race_scores(plan, scores_FTVA)
{
    if('US President 2020 Efficiency Gap' in plan.summary)
    {
        var ftva_races = [{office: 'U.S. President', year: '2020', gap: plan.summary['US President 2020 Efficiency Gap']}];

        if('US President 2016 Efficiency Gap' in plan.summary) {
            ftva_races.push({office: 'U.S. President', year: '2016', gap: plan.summary['US President 2016 Efficiency Gap']});
        }

        if('US Senate 2020 Efficiency Gap' in plan.summary) {
            ftva_races.push({office: 'U.S. Senate', year: '2020', gap: plan.summary['US Senate 2020 Efficiency Gap']});
        }

        if('US Senate 2018 Efficiency Gap' in plan.summary) {
            ftva_races.push({office: 'U.S. Senate', year: '2018', gap: plan.summary['US Senate 2018 Efficiency Gap']});
        }

        if('US Senate 2016 Efficiency Gap' in plan.summary) {
            ftva_races.push({office: 'U.S. Senate', year: '2016', gap: plan.summary['US Senate 2016 Efficiency Gap']});
        }

        // We have space for no more than four FTVA races
        ftva_races = ftva_races.slice(0, 4);

        for(var i = 0; i < ftva_races.length; i++)
        {
            var score_FTVA = scores_FTVA[i],
                gap = ftva_races[i].gap,
                gap_amount = nice_percent(Math.abs(gap)) + partisan_suffix(gap),
                win_party = (gap < 0 ? 'Republican' : 'Democratic'),
                lose_party = (gap < 0 ? 'Democratic' : 'Republican');

            clear_element(score_FTVA);
            score_FTVA.style.display = '';

            score_FTVA.innerHTML = `
                <h5>${ftva_races[i].office} ${ftva_races[i].year}: ${gap_amount}</h5>
                <p>
                Under this plan, votes for the ${win_party}
                candidate were inefficient at a rate
                ${gap_amount} lower than votes for the
                ${lose_party} candidate.
                </p>
                `;
        }

        // Hide unused score elements
        for(var j = i; j < scores_FTVA.length; j++)
        {
            scores_FTVA[j].style.display = 'none';
        }
    } else {
        // Hide all FTVA sections if no data
        for(var i = 0; i < scores_FTVA.length; i++)
        {
            scores_FTVA[i].parentNode.style.display = 'none';
        }
    }
}

function update_heading_titles(head)
{
    var dem_index = head.indexOf('Democratic Votes'),
        rep_index = head.indexOf('Republican Votes'),
        wins_index = head.indexOf('Democratic Wins');

    if(wins_index >= 0)
    {
        head[wins_index] = 'Chance of Democratic Win';

        if(dem_index >= 0 && rep_index >= 0)
        {
            head[dem_index] = 'Predicted Vote Shares';
            head.splice(rep_index, 1);
        }
    } else if(dem_index >= 0 && rep_index >= 0) {
        head[dem_index] = 'Predicted Democratic Vote Share';
        head[rep_index] = 'Predicted Republican Vote Share';
    }

    // Rename titles for optimal text-wrapping
    head.forEach((dataTitle, i) => {
        // Rename entire titles
        if (votesFieldToDisplayStr[dataTitle]) {
            head[i] = votesFieldToDisplayStr[dataTitle];
        }
        // Rename title substrings, eg 'Citizen Voting-Age Population' => 'CVAP'
        for (const [substrMatch, substrReplacement] of Object.entries(fieldSubstringToDisplayStr)) {
            if (head[i].includes(substrMatch)) {
                const newTitle = head[i].replace(substrMatch, substrReplacement);
                renamedHeadingToOrigField.set(newTitle, head[i]);
                head[i] = newTitle;
            }
        }
    });
    
    // Hide selected shy columns by renaming them to a signal value
    head.forEach((dataTitle, i) => {
        if(head[i] == 'Trump (R) 2016' && head.indexOf('Trump (R) 2020') >= 0) {
            head[i] = SHY_COLUMN;

        } else if(head[i] == 'Trump (R) 2016' && head.indexOf('Trump (R) 2024') >= 0) {
            head[i] = SHY_COLUMN;

        } else if(head[i] == 'Trump (R) 2020' && head.indexOf('Trump (R) 2024') >= 0) {
            head[i] = SHY_COLUMN;

        } else if(head[i] == 'Clinton (D) 2016' && head.indexOf('Biden (D) 2020') >= 0) {
            head[i] = SHY_COLUMN;

        } else if(head[i] == 'Clinton (D) 2016' && head.indexOf('Harris (D) 2024') >= 0) {
            head[i] = SHY_COLUMN;

        } else if(head[i] == 'Biden (D) 2020' && head.indexOf('Harris (D) 2024') >= 0) {
            head[i] = SHY_COLUMN;

        } else if(head[i] == 'CVAP 2019') {
            head[i] = SHY_COLUMN;

        } else if(head[i] == 'CVAP 2020' || head[i] == 'CVAP 2020 ACS') {
            head[i] = SHY_COLUMN;

        } else if(head[i] == 'CVAP 2023' || head[i] == 'CVAP 2023 ACS') {
            head[i] = SHY_COLUMN;
        }
    });
}

function update_vote_percentages(head, row, source_row)
{
    var dem_index = head.indexOf('Democratic Votes'),
        rep_index = head.indexOf('Republican Votes'),
        wins_index = head.indexOf('Democratic Wins'),
        vote_count;

    if(wins_index >= 0)
    {
        row[wins_index] = nice_round_percent(row[wins_index]);

        if(dem_index >= 0 && rep_index >= 0)
        {
            vote_count = (row[dem_index] + row[rep_index]);
            row[dem_index] = [
                nice_round_percent(row[dem_index] / vote_count), ' D / ',
                nice_round_percent(row[rep_index] / vote_count), ' R'
            ].join('');
            row.splice(rep_index, 1);
        }
    } else if(dem_index >= 0 && rep_index >= 0) {
        vote_count = (row[dem_index] + row[rep_index]);
        row[dem_index] = nice_percent(row[dem_index] / vote_count);
        row[rep_index] = nice_percent(row[rep_index] / vote_count);

        if(typeof source_row['Democratic Votes SD'] === 'number'
        && typeof source_row['Republican Votes SD'] === 'number')
        {
            row[dem_index] += ' (±' + nice_percent(2 * source_row['Democratic Votes SD'] / vote_count) + ')';
            row[rep_index] += ' (±' + nice_percent(2 * source_row['Republican Votes SD'] / vote_count) + ')';
        }
    }
}

function update_vote_swings(head, row)
{
    var swing_index = head.indexOf('Vote Swing');

    if(swing_index >= 0)
    {
        row[swing_index] = nice_vote_swing(row[swing_index]);
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

function update_acs2018_percentages(head, row)
{
    var total_index = head.indexOf('Population 2018'),
        black_index = head.indexOf('Black Population 2018'),
        latin_index = head.indexOf('Hispanic Population 2018');

    if(total_index >= 0 && black_index >= 0 && latin_index >= 0)
    {
        row[black_index] = nice_percent(row[black_index] / row[total_index]);
        row[latin_index] = nice_percent(row[latin_index] / row[total_index]);
    }
}

function update_acs2019_percentages(head, row)
{
    var total_index = head.indexOf('Population 2019'),
        black_index = head.indexOf('Black Population 2019'),
        latin_index = head.indexOf('Hispanic Population 2019');

    if(total_index >= 0 && black_index >= 0 && latin_index >= 0)
    {
        row[black_index] = nice_percent(row[black_index] / row[total_index]);
        row[latin_index] = nice_percent(row[latin_index] / row[total_index]);
    }
}

function update_acs2020_percentages(head, row)
{
    var total_index = head.indexOf('Population 2020 ACS'),
        black_index = head.indexOf('Black Population 2020 ACS'),
        latin_index = head.indexOf('Hispanic Population 2020 ACS');

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

function update_cvap2018_percentages(head, row)
{
    var total_index = head.indexOf('Citizen Voting-Age Population 2018'),
        black_index = head.indexOf('Black Citizen Voting-Age Population 2018'),
        latin_index = head.indexOf('Hispanic Citizen Voting-Age Population 2018');

    if(total_index >= 0 && black_index >= 0 && latin_index >= 0)
    {
        row[black_index] = nice_percent(row[black_index] / row[total_index]);
        row[latin_index] = nice_percent(row[latin_index] / row[total_index]);
    }
}

function update_cvap2019_percentages(head, row)
{
    var total_index = head.indexOf('Citizen Voting-Age Population 2019'),
        black_index = head.indexOf('Black Citizen Voting-Age Population 2019'),
        latin_index = head.indexOf('Hispanic Citizen Voting-Age Population 2019'),
        asian_index = head.indexOf('Asian Citizen Voting-Age Population 2019'),
        native_index = head.indexOf('American Indian or Alaska Native Citizen Voting-Age Population 2019');

    if(total_index >= 0 && black_index >= 0)
    {
        row[black_index] = nice_percent(row[black_index] / row[total_index]);
    }

    if(total_index >= 0 && latin_index >= 0)
    {
        row[latin_index] = nice_percent(row[latin_index] / row[total_index]);
    }

    if(total_index >= 0 && asian_index >= 0)
    {
        row[asian_index] = nice_percent(row[asian_index] / row[total_index]);
    }

    if(total_index >= 0 && native_index >= 0)
    {
        row[native_index] = nice_percent(row[native_index] / row[total_index]);
    }
}

function update_cvap2020_percentages(head, row)
{
    var total_index = head.indexOf('Citizen Voting-Age Population 2020 ACS'),
        black_index = head.indexOf('Black Citizen Voting-Age Population 2020 ACS'),
        latin_index = head.indexOf('Hispanic Citizen Voting-Age Population 2020 ACS'),
        asian_index = head.indexOf('Asian Citizen Voting-Age Population 2020 ACS'),
        native_index = head.indexOf('American Indian or Alaska Native Citizen Voting-Age Population 2020 ACS');

    if(total_index >= 0 && black_index >= 0)
    {
        row[black_index] = nice_percent(row[black_index] / row[total_index]);
    }

    if(total_index >= 0 && latin_index >= 0)
    {
        row[latin_index] = nice_percent(row[latin_index] / row[total_index]);
    }

    if(total_index >= 0 && asian_index >= 0)
    {
        row[asian_index] = nice_percent(row[asian_index] / row[total_index]);
    }

    if(total_index >= 0 && native_index >= 0)
    {
        row[native_index] = nice_percent(row[native_index] / row[total_index]);
    }
}

function update_cvap2023_percentages(head, row)
{
    var total_index = head.indexOf('Citizen Voting-Age Population 2023 ACS'),
        black_index = head.indexOf('Black Citizen Voting-Age Population 2023 ACS'),
        latin_index = head.indexOf('Hispanic Citizen Voting-Age Population 2023 ACS'),
        asian_index = head.indexOf('Asian Citizen Voting-Age Population 2023 ACS'),
        native_index = head.indexOf('American Indian or Alaska Native Citizen Voting-Age Population 2023 ACS');

    if(total_index >= 0 && black_index >= 0)
    {
        row[black_index] = nice_percent(row[black_index] / row[total_index]);
    }

    if(total_index >= 0 && latin_index >= 0)
    {
        row[latin_index] = nice_percent(row[latin_index] / row[total_index]);
    }

    if(total_index >= 0 && asian_index >= 0)
    {
        row[asian_index] = nice_percent(row[asian_index] / row[total_index]);
    }

    if(total_index >= 0 && native_index >= 0)
    {
        row[native_index] = nice_percent(row[native_index] / row[total_index]);
    }
}

/*
 * Return a rows * columns matrix representing a scored plan table
 */
function plan_array(plan)
{
    var incumbency = {'O': 'Open Seat', 'D': 'Democratic Incumbent', 'R': 'Republican Incumbent'},
        flippy_colors = [LEAN_BLUE_COLOR_HEX, LEAN_RED_COLOR_HEX],
        fields = FIELDS.slice();

    // Build list of columns
    var head_row = ['District'],
        all_rows = [head_row],
        field, current_row, field_missing, flip_chance;

    const has_incumbency = plan_has_incumbency(plan);

    if(has_incumbency) {
        head_row.push('Candidate Scenario');
    }

    if(plan.districts.length == 0)
    {
        return undefined;
    }

    for(var j = 0; j < plan.districts.length; j++)
    {
        var new_row = [],
            number;
        
        if('number' in plan.districts[j]) {
            number = plan.districts[j].number;
            new_row.push(typeof number == 'number' ? number.toFixed(0) : '–');
        } else {
            new_row.push((j + 1).toString());
        }

        if(has_incumbency) {
            new_row.push(incumbency[plan.incumbents[j]]);
        }

        all_rows.push(new_row);
    }

    for(var i in fields)
    {
        field = fields[i];
        field_missing = false;
        has_nonzero_vote_swings = false;

        for(var j in plan.districts)
        {
            if(field in plan.districts[j].totals) {
                continue;
            } else if('compactness' in plan.districts[j] && field in plan.districts[j].compactness) {
                continue;
            } else if('vote_swing' in plan.districts[j] && field == 'Vote Swing') {
                if (plan.districts[j].vote_swing != 0.0) {
                    has_nonzero_vote_swings = true;
                }
                continue;
            } else {
                field_missing = true;
            }
        }

        if(field_missing) {
            continue;
        } else if(field == 'Population 2019' && fields.indexOf('Population 2020') !== -1) {
            // Do not show 2019 ACS population if 2020 Census population is present
            continue;
        } else if(field == 'Population 2020 ACS' && fields.indexOf('Population 2020') !== -1) {
            // Do not show 2020 ACS population if 2020 Census population is present
            continue;
        }

        if(field == 'Democratic Wins')
        {
            head_row.push('Chance of 1+ Flips<sup>†</sup>');

            for(var j in plan.districts)
            {
                current_row = all_rows[parseInt(j) + 1];
                flip_chance = flippy_colors.indexOf(which_district_color(plan.districts[j], plan)) != -1;
                current_row.push(flip_chance);
            }
        } else if(field == 'Vote Swing' && !has_nonzero_vote_swings) {
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

            } else if('vote_swing' in plan.districts[j] && field == 'Vote Swing' && has_nonzero_vote_swings) {
                current_row.push(plan.districts[j].vote_swing);
            }
        }
    }

    for(var j = 1; j < all_rows.length; j++)
    {
        update_vote_swings(head_row, all_rows[j]);
        update_acs2015_percentages(head_row, all_rows[j]);
        update_acs2016_percentages(head_row, all_rows[j]);
        update_acs2018_percentages(head_row, all_rows[j]);
        update_acs2019_percentages(head_row, all_rows[j]);
        update_acs2020_percentages(head_row, all_rows[j]);
        update_cvap2015_percentages(head_row, all_rows[j]);
        update_cvap2018_percentages(head_row, all_rows[j]);
        update_cvap2019_percentages(head_row, all_rows[j]);
        update_cvap2020_percentages(head_row, all_rows[j]);
        update_cvap2023_percentages(head_row, all_rows[j]);

        // Do this last! It leaves head out of synch with rows, needs update_heading_titles()
        update_vote_percentages(head_row, all_rows[j], plan.districts[j - 1].totals);
    }

    // Fix the synch problem introduced in update_vote_percentages()
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

function nice_plan_voteshare(plan)
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

    return (nice_percent(blue_votes / (blue_votes + red_votes)) + ' (Democratic) '
        + 'and ' + nice_percent(red_votes / (blue_votes + red_votes)) + ' (Republican)');
}

function get_state_full_name(postal_code)
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

    return states[postal_code];
}

function get_house_full_name(house_code)
{
    var houseNames = {
        'ushouse': 'U.S. House',
        'statesenate': 'State Senate',
        'statehouse': 'State House',
        'localplan': 'Local Plan',
    };

    return houseNames[house_code];
}

function get_plan_headings(plan, modified_at)
{
    const description = plan.description || false;

    // Prefer model's time over the XHR's Last-Modified
    if(plan['start_time'])
    {
        modified_at = new Date(plan.start_time * 1000);
    }

    // Display timestamp if plan is from the last 24 hours.
    const date_str = date_age(modified_at) > 60 * 60 * 24
        ? modified_at.toLocaleDateString()
        : modified_at.toLocaleString();
    const uploaded = `Uploaded: ${date_str}`;

    const date_only =
      months[modified_at.getMonth()] +
      modified_at.getDate() + ', ' +
      modified_at.getFullYear();

    return {
        description,
        uploaded,
        date_only
    };
}


function plan_has_incumbency(plan)
{
    return plan.model && plan.model.incumbency
        && plan.incumbents && plan.incumbents.length == plan.districts.length;
}

function start_load_plan_polling(url, message_section, score_section,
    description_el, metadata_el, model_link, model_footnote, model_url_pattern,
    districts_table, metrics_table, score_EG, score_PB, score_MM, score_DEC2,
    score_sense, scores_FTVA, text_url, text_link, geom_prefix, map_div, seat_count,
    scenario_adjustments_form)
{
    const make_xhr = () => {
        load_plan_score(url, message_section, score_section,
            description_el, metadata_el, model_link, model_footnote, model_url_pattern,
            districts_table, metrics_table, score_EG, score_PB, score_MM,
            score_DEC2, score_sense, scores_FTVA, text_url, text_link, geom_prefix, map_div,
            seat_count, scenario_adjustments_form, xhr_retry_callback);
    };

    const xhr_retry_callback = () => {
        setTimeout(() => {
            make_xhr();
        }, 5000);
    };

    show_message('Loading district plan', score_section, message_section);
    make_xhr();
}

function load_plan_score(url, message_section, score_section,
    description_el, metadata_el, model_link, model_footnote, model_url_pattern,
    districts_table, metrics_table, score_EG, score_PB, score_MM, score_DEC2,
    score_sense, scores_FTVA, text_url, text_link, geom_prefix, map_div, seat_count,
    scenario_adjustments_form, xhr_retry_callback)
{
    var request = new XMLHttpRequest();
    request.open('GET', url, true);

    function on_loaded_score(plan, modified_at)
    {
        const is_plan_still_parsing = (plan.status !== true && which_score_summary_name(plan) === null);
        if(is_plan_still_parsing) {
            if (plan.message) {
                // Still processing
                show_message(plan.message, score_section, message_section);
                if (typeof xhr_retry_callback === 'function') xhr_retry_callback();
            } else {
                show_message('District plan failed to load.', score_section, message_section);
            }
            return;
        }

        // Immediately kick off scenario loading
        if (plan.scenarios !== undefined) {
            load_plan_scenarios(geom_prefix + plan.scenarios.replace(/^\//, ''), function(scenarios) {
                setup_scenario_interactivity(plan, scenarios, scenario_adjustments_form, districts_table);
            });
        }

        // Plan is done parsing and we can render the page
        hide_message(score_section, message_section);

        // Clear out and repopulate plan description, upload date, plan type
        clear_element(description_el);
        const headings = get_plan_headings(plan, modified_at);
        if (headings.description) {
            const desc_el = document.createElement('h1');
            desc_el.textContent = plan.description;
            description_el.append(desc_el);
        }

        const hr = document.createElement('hr');
        hr.classList.add('no-margin-bottom');
        description_el.append(hr);

        const info_el = document.createElement('div');
        info_el.classList.add('info');

        info_el.append(create_info_box('State', get_state_full_name(plan.model.state)));

        info_el.append(create_info_box('Legislative', get_house_full_name(plan.model.house)));

        info_el.append(create_info_box('Added to PlanScore', headings.date_only));

        // needs the author name
        if (false) { // check for a plan author
          info_el.append(create_info_box('Author', '%author'));
        }

        function create_info_box(label, info){
          const info_box = document.createElement('div');
          info_box.classList.add('box');
          info_box.innerHTML = `<strong>${label}</strong> ${info}`;
          return info_box;
        };

        description_el.append(info_el);

        if(plan.model_version) {
            model_link.href = model_url_pattern.replace('2020', plan.model_version);
            model_footnote.href = model_url_pattern.replace('2020', plan.model_version);
        
        } else if(plan.model && (plan.model.version == '2017' || !plan.model.version)) {
            model_link.href = model_url_pattern.replace('data/2020', plan.model.key_prefix);
            model_footnote.href = model_url_pattern.replace('data/2020', plan.model.key_prefix);

        } else if(plan.model && plan.model.version) {
            model_link.href = model_url_pattern.replace('2020', plan.model.version);
            model_footnote.href = model_url_pattern.replace('2020', plan.model.version);
        }

        // Build the results table
        construct_districts_table(plan, districts_table);
        populate_districts_table(plan, districts_table);
        construct_seatshare_graphic(plan, districts_table);
        populate_seatshare_graphic(plan);

        text_link.href = text_url;

        if(plan.districts)
        {
            if(plan.districts.length == 1) {
                seat_count.innerHTML = '1 seat';
            } else {
                seat_count.innerHTML = plan.districts.length.toString() + ' seats';
            }

            if(plan.districts.length < 7)
            {
                console.log(seat_count.parentNode.style.display = 'block');
            }
        }

        // Construct and populate scores.
        construct_efficiency_gap_score(score_EG);
        populate_efficiency_gap_score(plan, score_EG);
        construct_sensitivity_test(score_sense);
        populate_sensitivity_test(plan, score_sense);

        if('Declination' in plan.summary && plan.summary['Declination Is Valid'] !== 0) {
            construct_declination2_score(score_DEC2);
            populate_declination2_score(plan, score_DEC2);
        } else if('Declination' in plan.summary) {
            hide_score_with_reason(score_DEC2,
                'Declination is only shown where both parties each win one or more'
                + 'seats in a sufficient number of predicted scenarios<sup>*</sup>.');
        } else {
            hide_score_with_reason(score_DEC2,
                'We were not yet calculating declination at the time that we scored this plan.');
        }

        if(plan_voteshare(plan) < .1 || location.hash.match(/\bshowall\b/)) {
            construct_partisan_bias_score(score_PB);
            populate_partisan_bias_score(plan, score_PB);
            construct_mean_median_score(score_MM);
            populate_mean_median_score(plan, score_MM);
        } else {
            hide_score_with_reason(score_PB,
                'The parties\' statewide vote shares are ' + nice_plan_voteshare(plan) + ' based on the model.'
                + ' Partisan bias is shown only where the parties\' statewide vote shares fall between 45% and 55%.'
                + ' Outside this range the metric\'s assumptions are not plausible.');
            hide_score_with_reason(score_MM,
                'The parties\' statewide vote shares are ' + nice_plan_voteshare(plan) + ' based on the model.'
                + ' The mean-median difference is shown only where the parties\' statewide vote shares fall between 45% and 55%.'
                + ' Outside this range the metric\'s assumptions are not plausible.');
        }

        construct_metrics_table(metrics_table);
        populate_metrics_table(plan, metrics_table);
        construct_ftva_race_scores(scores_FTVA);
        populate_ftva_race_scores(plan, scores_FTVA);

        if('library_metadata' in plan && plan['library_metadata']) {
            construct_library_metadata(metadata_el);
            populate_library_metadata(plan, metadata_el, geom_prefix);
        } else {
            metadata_el.style.display = 'none';
        }

        // Go on to load the map.
        load_plan_map(geom_prefix + plan.geometry_key, map_div, plan, districts_table);
    }

    request.onload = function()
    {
        if(request.status >= 200 && request.status < 400)
        {
            // Returns a dictionary with a list of districts
            var data = JSON.parse(request.responseText),
                modified_at = new Date(request.getResponseHeader('Last-Modified'));

            // older uploads had geometries but did not include geometry_key
            if(!('geometry_key' in data)) {
                console.log('Added geometry_key in post');
                data.geometry_key = 'uploads/' + data.id + '/geometry.json';
            }

            on_loaded_score(data, modified_at);
            return;
        }

        show_message('The district plan failed to load.', score_section, message_section);
    };

    request.onerror = function() { /* There was a connection error of some sort */ };
    request.send();
}

function load_plan_scenarios(url, callback)
{
    var request = new XMLHttpRequest();
    request.open('GET', url, true);

    function on_loaded_scenarios(data)
    {
        adjust_scenario_stats(data);
        console.log('New scenarios:', data);
        if (callback) {
            callback(data);
        }
    }

    request.onload = function()
    {
        if(request.status >= 200 && request.status < 400)
        {
            // Returns a GeoJSON dictionary
            var data = JSON.parse(request.responseText);
            console.log('Loaded scenarios:', data);
            on_loaded_scenarios(data);
        }
    };

    request.onerror = function() { /* There was a connection error of some sort */ };
    request.send();
}

function load_plan_map(url, div, plan, table)
{
    var request = new XMLHttpRequest();
    request.open('GET', url, true);

    function on_loaded_geojson(data)
    {
        function district_popup_content(layer)
        {
            var index = data.features.indexOf(layer.feature),
                incumbency = {'O': 'Open Seat', 'D': 'Democratic Incumbent', 'R': 'Republican Incumbent'},
                has_incumbency = plan_has_incumbency(plan);

            if(has_incumbency) {
                return 'District ' + (index + 1) + '<br>' + incumbency[plan.incumbents[index]];
            }

            return 'District ' + (index + 1);
        }

        var geojson = L.geoJSON(data, {
            style: function(feature)
            {
                var district = plan.districts[data.features.indexOf(feature)];
                return { weight: 2, fillOpacity: .5, color: which_district_color(district, plan) };
            }
            }).bindPopup(district_popup_content);


        // On map layer hover: highlight associated table rows
        function on_geojson_mouse_event(evtdata) {
            const should_apply_highlight = evtdata.type === 'mouseover';
            const index = data.features.indexOf(evtdata.layer.feature);
            const tableRowEl = $('table tbody tr').get(index);
            tableRowEl.classList.toggle('highlighted', should_apply_highlight);
        }
        geojson.on('mouseover', on_geojson_mouse_event);
        geojson.on('mouseout', on_geojson_mouse_event);


        // On table row hover: highlight map district
        table.querySelectorAll('tbody tr').forEach((elem, j) => {
            const on_tr_mouse_event = e => {
                const should_apply_highlight = e.type === 'mouseover';
                const matched_feature = data.features[j];
                const layer = Object.values(geojson._layers).find(l => l.feature === matched_feature);
                const path_elem = layer['_path'];
                path_elem.classList.toggle('highlight', should_apply_highlight);
            };
            elem.addEventListener('mouseover', on_tr_mouse_event);
            elem.addEventListener('mouseout', on_tr_mouse_event);
        });

        console.log('GeoJSON bounds:', geojson.getBounds());

        //
        var show_leans = (typeof plan.districts[0].totals['Democratic Wins'] === 'number');
        add_map_pattern_support(show_leans);

        // Initialize the map on the passed div in the middle of the ocean
        var map = L.map(div, {
            scrollWheelZoom: false,
            zoomControl: false,
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
        if(plan.model.state == 'AK') {
            map.fitBounds(L.latLngBounds(L.latLng(54.6, -128.8), L.latLng(71.2, -174.1)));
        } else if(plan.model.state == 'HI') {
            map.fitBounds(L.latLngBounds(L.latLng(18.6, -154.3), L.latLng(22.5, -160.2)));
        } else {
            map.fitBounds(geojson.getBounds());
        }

        // Add Toner label tiles for base map
        L.tileLayer('https://tiles.stadiamaps.com/tiles/stamen_toner_labels/{z}/{x}/{y}{r}.png', {
            attribution: '&copy;<a href="http://stamen.com/">Stamen</a>, &copy;<a href="http://www.stadiamaps.com/">Stadia</a>',
            pane: 'labels',
            maxZoom: 18
        }).addTo(map);

        map.addControl(L.control.zoom({'position': 'topright'}));
        map.addControl(new L.Control.PartyLegend({'position': 'topleft'}));
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

function add_map_pattern_support(show_leans)
{
    // Custom map legend control copied from
    // https://github.com/PlanScore/PlanScore/blob/b48188b/_common/jslibs/leaflet-control-partylegend.js
    L.Control.PartyLegend = L.Control.extend({
        options: {
            position: 'topright',
        },

        initialize: function(options) {
            L.Util.setOptions(this, options);
        },

        onAdd: function (map) {
            var container = L.DomUtil.create('div', 'planscore-partylegend');

            var row_d    = L.DomUtil.create('div', 'planscore-partylegend-legend', container);
            var swatch_d = L.DomUtil.create('div', 'planscore-partylegend-swatch planscore-partylegend-swatch-democrat', row_d);
            var words_d  = L.DomUtil.create('div', 'planscore-partylegend-words', row_d);
            words_d.innerHTML = 'Democratic';

            var row_r    = L.DomUtil.create('div', 'planscore-partylegend-legend', container);
            var swatch_r = L.DomUtil.create('div', 'planscore-partylegend-swatch planscore-partylegend-swatch-republican', row_r);
            var words_r  = L.DomUtil.create('div', 'planscore-partylegend-words', row_r);
            words_r.innerHTML = 'Republican';

            if(show_leans)
            {
                var row_ld    = L.DomUtil.create('div', 'planscore-partylegend-legend', container);
                var swatch_ld = L.DomUtil.create('div', 'planscore-partylegend-swatch planscore-partylegend-swatch-lean-democrat', row_ld);
                var words_ld  = L.DomUtil.create('div', 'planscore-partylegend-words', row_ld);
                words_ld.innerHTML = 'Leans Dem.';

                var row_lr    = L.DomUtil.create('div', 'planscore-partylegend-legend', container);
                var swatch_lr = L.DomUtil.create('div', 'planscore-partylegend-swatch planscore-partylegend-swatch-lean-republican', row_lr);
                var words_lr  = L.DomUtil.create('div', 'planscore-partylegend-words', row_lr);
                words_lr.innerHTML = 'Leans Rep.';

            } else {
                var row_x    = L.DomUtil.create('div', 'planscore-partylegend-legend', container);
                var swatch_x = L.DomUtil.create('div', 'planscore-partylegend-swatch planscore-partylegend-swatch-both', row_x);
                var words_x  = L.DomUtil.create('div', 'planscore-partylegend-words', row_x);
                words_x.innerHTML = 'Uncertain';

                /*
                var row_0    = L.DomUtil.create('div', 'planscore-partylegend-legend', container);
                var swatch_0 = L.DomUtil.create('div', 'planscore-partylegend-swatch planscore-partylegend-swatch-nodata', row_0);
                var words_0  = L.DomUtil.create('div', 'planscore-partylegend-words', row_0);
                words_0.innerHTML = 'No Data';
                */
            }

            return container;
        },
    });

    if(L.Browser.svg)
    {
        L.SVG.include({

            // Exact copy of Leaflet SVG _updateStyle with additional awareness of unknown color
            // https://github.com/Leaflet/Leaflet/blob/b1e59c9/src/layer/vector/SVG.js#L141-L176
            _updateStyle: function _updateStyle(layer) {
                var path = layer._path,
                    options = layer.options;

                if (!path) { return; }

                if (options.stroke) {
                    path.setAttribute('stroke', options.color);
                    path.setAttribute('stroke-opacity', options.opacity);
                    path.setAttribute('stroke-width', options.weight);
                    path.setAttribute('stroke-linecap', options.lineCap);
                    path.setAttribute('stroke-linejoin', options.lineJoin);

                    if (options.dashArray) {
                        path.setAttribute('stroke-dasharray', options.dashArray);
                    } else {
                        path.removeAttribute('stroke-dasharray');
                    }

                    if (options.dashOffset) {
                        path.setAttribute('stroke-dashoffset', options.dashOffset);
                    } else {
                        path.removeAttribute('stroke-dashoffset');
                    }
                } else {
                    path.setAttribute('stroke', 'none');
                }

                if (options.fill)
                {
                    var pattern_colors = [UNKNOWN_COLOR_HEX, REDDISH_COLOR_HEX,
                        BLUEISH_COLOR_HEX, LEAN_BLUE_COLOR_HEX, LEAN_RED_COLOR_HEX];

                    if (typeof options.color == "string" && pattern_colors.indexOf(options.color) >= 0) {
                        // Add support for unknown color, a gray
                        this.__fillPattern(layer);
                    } else {
                        path.setAttribute('fill', options.fillColor || options.color);
                    }
                    path.setAttribute('fill-opacity', options.fillOpacity);
                    path.setAttribute('fill-rule', options.fillRule || 'evenodd');
                } else {
                    path.setAttribute('fill', 'none');
                }
            },

            // Close adaptation of __fillPattern from PlanScore static site visualization
            // https://github.com/PlanScore/PlanScore/blob/b48188b/_common/jslibs/leaflet-polygon.fillPattern.js
            __fillPattern: function __fillPattern(layer) {
                var path = layer._path,
                    options = layer.options;

                if (!this._defs) {
                    this._defs = L.SVG.create('defs');
                    this._container.appendChild(this._defs);
                }

                if(options.color == UNKNOWN_COLOR_HEX) {
                    var _img_url = UNKNOWN_PATTERN_URL;
                    var _ref_id = 'UNKNOWN_PATTERN_URL' + new Date().getUTCMilliseconds();
                } else if(options.color == LEAN_RED_COLOR_HEX) {
                    var _img_url = LEAN_RED_PATTERN_URL;
                    var _ref_id = 'LEAN_RED_PATTERN_URL' + new Date().getUTCMilliseconds();
                } else if(options.color == LEAN_BLUE_COLOR_HEX) {
                    var _img_url = LEAN_BLUE_PATTERN_URL;
                    var _ref_id = 'LEAN_BLUE_PATTERN_URL' + new Date().getUTCMilliseconds();
                } else if(options.color == REDDISH_COLOR_HEX) {
                    var _img_url = REDDISH_PATTERN_URL;
                    var _ref_id = 'REDDISH_PATTERN_URL' + new Date().getUTCMilliseconds();
                } else if(options.color == BLUEISH_COLOR_HEX) {
                    var _img_url = BLUEISH_PATTERN_URL;
                    var _ref_id = 'BLUEISH_PATTERN_URL' + new Date().getUTCMilliseconds();
                }

                var _p = document.getElementById(_ref_id);
                if (!_p) {
                    var _im = new Image();
                    _im.src = _img_url;

                    _p = L.SVG.create('pattern');
                    _p.setAttribute('id', _ref_id);
                    _p.setAttribute('x', '0');
                    _p.setAttribute('y', '0');
                    _p.setAttribute('patternUnits', 'userSpaceOnUse');
                    _p.setAttribute('width', '24');
                    _p.setAttribute('height', '24');
                    var _rect = L.SVG.create('rect');
                    _rect.setAttribute('width', 24);
                    _rect.setAttribute('height', 24);
                    _rect.setAttribute('x', 0);
                    _rect.setAttribute('x', 0);
                    _rect.setAttribute('fill', options.fillColor || options.color);

                    _p.appendChild(_rect);
                    this._defs.appendChild(_p);

                    var _img = L.SVG.create('image');
                    _img.setAttribute('x', '0');
                    _img.setAttribute('y', '0');
                    _img.setAttributeNS('http://www.w3.org/1999/xlink', 'href', _img_url);
                    _img.setAttribute('width', '24');
                    _img.setAttribute('height', '24');
                    _p.appendChild(_img);

                    _im.onload = function () {
                        _p.setAttribute('width', _im.width);
                        _p.setAttribute('height', _im.height);
                        _img.setAttribute('width', _im.width);
                        _img.setAttribute('height', _im.height);
                    };
                }
                path.setAttribute('fill', "url(#" + _ref_id + ")");
            }
        });
    }
}

// Export functions for testing
if(typeof module !== 'undefined' && module.exports)
{
    module.exports = {
        format_url,
        nice_count,
        nice_string,
        nice_percent,
        nice_round_percent,
        nice_vote_swing,
        partisan_suffix,
        get_plan_headings,
        nice_gap,
        date_age,
        which_score_summary_name,
        which_score_column_names,
        which_district_color,
        get_seatshare_array,
        plan_array,
        plan_has_incumbency,
        update_vote_percentages,
        update_vote_swings,
        update_acs2015_percentages,
        update_acs2016_percentages,
        update_cvap2015_percentages,
        update_heading_titles,
        adjust_scenario_stats,
        create_scenario_plan,
        SHY_COLUMN,
    };
}
