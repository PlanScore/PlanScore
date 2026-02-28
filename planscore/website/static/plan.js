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
    'Margin Swing',
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

function nice_margin_swing(vote_swing_value)
{
    // Display vote swing as margin swing (2x) to user
    var margin_value = vote_swing_value * 2;

    if (margin_value < -0.0955) {
        return `R+${(margin_value * -100).toFixed(0)}`;
    } else if (margin_value > 0.0955) {
        return `D+${(margin_value * 100).toFixed(0)}`;
    } else if (margin_value < 0) {
        return `R+${(margin_value * -100).toFixed(1)}`;
    } else if (margin_value > 0) {
        return `D+${(margin_value * 100).toFixed(1)}`;
    }
    return '–';
}

function swing_vote(red_districts, blue_districts, amount)
{
    // Swing the vote by a percentage, positive toward blue.
    if (amount === 0) {
        return [red_districts.slice(), blue_districts.slice()];
    }

    var swung_reds = [];
    var swung_blues = [];

    for (var i = 0; i < red_districts.length; i++) {
        var r = red_districts[i];
        var b = blue_districts[i];
        var t = r + b;

        if (t > 0) {
            swung_reds.push((r / t - amount) * t);
            swung_blues.push((b / t + amount) * t);
        }
    }

    return [swung_reds, swung_blues];
}

function calculate_EG(red_districts, blue_districts)
{
    // Convert two lists of district vote counts into an EG score.
    // By convention, result is positive for blue and negative for red.
    // Note: This version does not include vote_swing parameter.

    // Calculate initial vote share
    var init_blue_total = blue_districts.reduce(function(a, b) { return a + b; }, 0);
    var init_red_total = red_districts.reduce(function(a, b) { return a + b; }, 0);
    var init_vote_share = init_blue_total / (init_blue_total + init_red_total);

    // Determine clamping swing
    var clamped_swing;
    if (init_vote_share < 0.25) {
        // Very red state, swing to 25 blue/75 red
        clamped_swing = 0.25 - init_vote_share;
    } else if (init_vote_share > 0.75) {
        // Very blue state, swing to 75 blue/25 red
        clamped_swing = init_vote_share - 0.75;
        clamped_swing = -clamped_swing;
    } else {
        clamped_swing = 0;
    }

    // Apply clamping swing
    var swung = swing_vote(red_districts, blue_districts, clamped_swing);
    var swung_red = swung[0];
    var swung_blue = swung[1];

    // Filter nonzero districts and count blue wins
    var district_blue_wins = 0;
    var nonzero_count = 0;
    var district_raw_blue_votes = 0;
    var district_raw_total_votes = 0;

    for (var i = 0; i < swung_red.length; i++) {
        if (swung_red[i] + swung_blue[i] > 0) {
            nonzero_count++;
            if (swung_blue[i] > swung_red[i]) {
                district_blue_wins++;
            }
            district_raw_blue_votes += swung_blue[i];
            district_raw_total_votes += swung_red[i] + swung_blue[i];
        }
    }

    var statewide_seat_share = district_blue_wins / nonzero_count;
    var statewide_vote_share = district_raw_blue_votes / district_raw_total_votes;

    return statewide_seat_share - 0.5 - 2 * (statewide_vote_share - 0.5);
}

function calculate_MMD(red_districts, blue_districts)
{
    // Convert two lists of district vote counts into a Mean-Median score.
    // By convention, result is positive for blue and negative for red.

    var shares = [];
    for (var i = 0; i < red_districts.length; i++) {
        var r = red_districts[i];
        var b = blue_districts[i];
        if (r + b > 0) {
            shares.push(b / (r + b));
        }
    }

    shares.sort(function(a, b) { return a - b; });

    // Calculate median
    var median;
    var mid = Math.floor(shares.length / 2);
    if (shares.length % 2 === 0) {
        median = (shares[mid - 1] + shares[mid]) / 2;
    } else {
        median = shares[mid];
    }

    // Calculate mean
    var sum = shares.reduce(function(a, b) { return a + b; }, 0);
    var mean = sum / shares.length;

    return median - mean;
}

function calculate_PB(red_districts, blue_districts)
{
    // Convert two lists of district vote counts into a Partisan Bias score.
    // By convention, result is positive for blue and negative for red.

    // Filter nonzero districts
    var nonzero_reds = [];
    var nonzero_blues = [];

    for (var i = 0; i < red_districts.length; i++) {
        if (red_districts[i] + blue_districts[i] > 0) {
            nonzero_reds.push(red_districts[i]);
            nonzero_blues.push(blue_districts[i]);
        }
    }

    var red_total = nonzero_reds.reduce(function(a, b) { return a + b; }, 0);
    var blue_total = nonzero_blues.reduce(function(a, b) { return a + b; }, 0);
    var blue_margin = (blue_total - red_total) / (blue_total + red_total);

    // Swing to 50/50
    var swung = swing_vote(nonzero_reds, nonzero_blues, -blue_margin / 2);
    var reds_5050 = swung[0];
    var blues_5050 = swung[1];

    // Count blue seats
    var blue_seats = 0;
    for (var i = 0; i < reds_5050.length; i++) {
        if (reds_5050[i] < blues_5050[i]) {
            blue_seats++;
        }
    }

    var blue_seatshare = blue_seats / blues_5050.length;
    var blue_voteshare = blues_5050.reduce(function(a, b) { return a + b; }, 0) /
        (blues_5050.reduce(function(a, b) { return a + b; }, 0) + reds_5050.reduce(function(a, b) { return a + b; }, 0));

    return blue_seatshare - blue_voteshare;
}

function calculate_D2(red_districts, blue_districts)
{
    // Convert two lists of district vote counts into a Declination score.
    // By convention, result is positive for blue and negative for red.
    // Adapt Python sample code from Warrington, 2018.

    var blue_shares = [];
    for (var i = 0; i < red_districts.length; i++) {
        var r = red_districts[i];
        var b = blue_districts[i];
        if (r + b > 0) {
            blue_shares.push(b / (r + b));
        }
    }

    var seats = blue_shares.length;
    var red_wins = blue_shares.filter(function(share) { return share <= 0.5; }).sort(function(a, b) { return a - b; });
    var blue_wins = blue_shares.filter(function(share) { return share > 0.5; }).sort(function(a, b) { return a - b; });

    var declination;

    if (red_wins.length === 0) {
        // -1 if red party does not win at least one seat
        declination = -1;
    } else if (blue_wins.length === 0) {
        // +1 if blue party does not win at least one seat
        declination = 1;
    } else {
        var mean_red_wins = red_wins.reduce(function(a, b) { return a + b; }, 0) / red_wins.length;
        var mean_blue_wins = blue_wins.reduce(function(a, b) { return a + b; }, 0) / blue_wins.length;

        var theta = Math.atan((1 - 2 * mean_red_wins) * seats / red_wins.length);
        var gamma = Math.atan((2 * mean_blue_wins - 1) * seats / blue_wins.length);

        // Convert to range [-1,1]
        declination = 2.0 * (gamma - theta) / Math.PI;
    }

    var declination2 = declination * Math.log(seats) / 2;

    return -declination2;
}

function calculate_mean(array)
{
    // Calculate the arithmetic mean of an array of numbers.
    if (array.length === 0) {
        return null;
    }
    var sum = array.reduce(function(a, b) { return a + b; }, 0);
    return sum / array.length;
}

function calculate_stdev(array)
{
    // Calculate the sample standard deviation of an array of numbers.
    // Uses n-1 denominator (Bessel's correction) for unbiased estimate.
    if (array.length < 2) {
        return null;
    }
    var mean = calculate_mean(array);
    var sum_squared_diffs = array.reduce(function(acc, val) {
        return acc + Math.pow(val - mean, 2);
    }, 0);
    return Math.sqrt(sum_squared_diffs / (array.length - 1));
}

function calculate_positives(array)
{
    // Calculate the proportion of positive values in an array.
    // Values greater than a small epsilon are considered positive.
    if (array.length === 0) {
        return null;
    }
    var epsilon = 1e-10;
    var positives = array.filter(function(val) { return val > epsilon; }).length;
    return positives / array.length;
}

function percentrank_abs(column, house, value)
{
    // Calculate absolute percentrank: what proportion of historical plans
    // have absolute value less than this plan's absolute value?
    // Higher percentrank = more extreme (skewed) than more historical plans.

    if (house === 'localplan' || !HISTORICAL_PERCENTRANK_DATA) {
        return null;
    }

    if (!HISTORICAL_PERCENTRANK_DATA[house] || !HISTORICAL_PERCENTRANK_DATA[house][column]) {
        return null;
    }

    var historical_values = HISTORICAL_PERCENTRANK_DATA[house][column];
    if (historical_values.length === 0) {
        return null;
    }

    var abs_value = Math.abs(value);
    var count = 0;

    for (var i = 0; i < historical_values.length; i++) {
        if (Math.abs(historical_values[i]) < abs_value) {
            count++;
        }
    }

    return count / historical_values.length;
}

function percentrank_rel(column, house, value)
{
    // Calculate relative (directional) percentrank matching server implementation.
    // Server code: score.py lines 301-324
    // For negative values: count where value < historical (historical is more pro-D)
    // For positive values: count where value > historical (historical is less pro-D)
    // This asymmetry matches the server behavior exactly.

    if (house === 'localplan' || !HISTORICAL_PERCENTRANK_DATA) {
        return null;
    }

    if (!HISTORICAL_PERCENTRANK_DATA[house] || !HISTORICAL_PERCENTRANK_DATA[house][column]) {
        return null;
    }

    var historical_values = HISTORICAL_PERCENTRANK_DATA[house][column];
    if (historical_values.length === 0) {
        return null;
    }

    var count = 0;

    if (value < 0) {
        // For negative values: count where value < historical
        for (var i = 0; i < historical_values.length; i++) {
            if (value < historical_values[i]) {
                count++;
            }
        }
    } else {
        // For positive values: count where value > historical
        for (var i = 0; i < historical_values.length; i++) {
            if (value > historical_values[i]) {
                count++;
            }
        }
    }

    return count / historical_values.length;
}

function adjust_scenario_stats(data)
{
    // Handle both legacy (3 dimensions) and new (4 dimensions with model_year) formats
    if (data.dimensions.length == 3) {
        // Legacy format: [vote_swings, incumbents, districts]
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
    } else if (data.dimensions.length == 4) {
        // New format with model_year dimension: [model_years, vote_swings, incumbents, districts]
        // Adjust statistics to represent real values
        // All scenario stat values past [0][0][0] are diffs atop [0][0][0] to save bytes
        for (var i = 0; i < data[data.dimensions[0]].length; i++) {
            for (var j = 0; j < data[data.dimensions[1]].length; j++) {
                for (var k = 0; k < data[data.dimensions[2]].length; k++) {
                    if (i > 0 || j > 0 || k > 0) {
                        for (var m = 0; m < data[data.dimensions[3]].length; m++) {
                            for (var s in data.statistics) {
                                var stat = data.statistics[s];
                                stat[i][j][k][m] = stat[0][0][0][m] + stat[i][j][k][m];
                            }
                        }
                    }
                }
            }
        }
    } else {
        throw new Error("Unexpected number of dimensions: " + data.dimensions.length);
    }
}

/**
 * Get a statistic value from scenarios, handling both legacy (3 dimensions) and new (with model_year) formats
 *
 * @param {Object} scenarios - The scenarios object
 * @param {string} stat_name - Name of statistic (e.g., 'Democratic Votes')
 * @param {number} model_year_idx - Model year index (ignored for legacy format)
 * @param {number} swing_idx - Vote swing index
 * @param {number} inc_idx - Incumbent index
 * @param {number} dist_idx - District index
 * @returns {number} The statistic value
 */
function get_scenario_statistic(scenarios, stat_name, model_year_idx, swing_idx, inc_idx, dist_idx)
{
    var statistic = scenarios.statistics[stat_name];
    if (!statistic) {
        return null;
    }

    // Check if this is the new format with model_years dimension
    if (scenarios.dimensions && scenarios.dimensions[0] === 'model_years') {
        // New format: [model_year][swing][incumbent][district]
        return statistic[model_year_idx][swing_idx][inc_idx][dist_idx];
    } else {
        // Legacy format: [swing][incumbent][district]
        return statistic[swing_idx][inc_idx][dist_idx];
    }
}

/**
 * Check if scenarios include the model_year dimension
 * (as opposed to legacy scenarios with only vote_swings, incumbents, districts)
 */
function has_model_year_dimension(scenarios)
{
    return scenarios.dimensions && scenarios.dimensions[0] === 'model_years';
}

/**
 * Parse a scenario key in format "model_year (pvote_year)"
 * Returns {model_year: int, pvote_year: int} or null if not parseable
 * Handles both old integer format and new string format for compatibility
 */
function parse_scenario_year_key(key)
{
    if (typeof key === 'number') {
        // Legacy integer format: use as both model_year and pvote_year
        return {model_year: key, pvote_year: key};
    }

    // New string format: "2024 (2020)"
    var match = String(key).match(/^(\d{4})\s*\((\d{4})\)$/);
    if (match) {
        return {
            model_year: parseInt(match[1]),
            pvote_year: parseInt(match[2])
        };
    }

    // Try simple integer string
    var year = parseInt(key);
    if (!isNaN(year)) {
        return {model_year: year, pvote_year: year};
    }

    return null;
}

function read_scenario_incumbents_from_table(districts_table)
{
    // Query all checked radio buttons in incumbent scenario forms
    // Return array of incumbent codes ['O', 'D', 'R', ...] in district order
    var incumbents = [];
    var rows = districts_table.querySelectorAll('tbody tr');

    for (var i = 0; i < rows.length; i++) {
        var checked_radio = rows[i].querySelector('form.candidate-scenario input[type="radio"]:checked');
        if (checked_radio) {
            incumbents.push(checked_radio.value);
        } else {
            // If no radio button is checked, this shouldn't happen but fall back to 'O'
            incumbents.push('O');
        }
    }

    return incumbents;
}

function check_all_open_seats(incumbents)
{
    // Check if all incumbents are open seats
    for (var i in incumbents) {
        if (incumbents[i] !== 'O') {
            return false;
        }
    }
    return true;
}

function create_scenario_plan(original_plan, scenarios, vote_swing, scenario_incumbents, model_year_idx)
{
    // Default to first model year (index 0) if not provided
    if (typeof model_year_idx === 'undefined') {
        model_year_idx = 0;
    }

    // Extract pvote_year from scenario key if available
    var pvote_year = original_plan.pvote_year; // default
    if (has_model_year_dimension(scenarios) && scenarios.model_years[model_year_idx]) {
        var parsed = parse_scenario_year_key(scenarios.model_years[model_year_idx]);
        if (parsed) {
            pvote_year = parsed.pvote_year;
        }
    }

    // Find the vote swing index in scenarios.vote_swings array
    var vote_swing_index = scenarios.vote_swings.indexOf(vote_swing);

    if (vote_swing_index === -1) {
        console.error('Vote swing not found in scenarios:', vote_swing);
        return original_plan;
    }

    // Find the baseline (0.0 swing) index for calculating vote_swing values
    var baseline_vote_swing_index = scenarios.vote_swings.indexOf(0.0);
    if (baseline_vote_swing_index === -1) {
        console.error('Baseline vote swing (0.0) not found in scenarios');
        baseline_vote_swing_index = vote_swing_index; // Fallback to current
    }

    // Create a deep copy of the plan
    // Note: We always create a mutated plan even when vote_swing=0 and incumbents unchanged,
    // because we need to add sensitivity sweep properties that aren't in the original
    var mutated_plan = JSON.parse(JSON.stringify(original_plan));

    // Update the plan's incumbents to reflect the scenario
    mutated_plan.incumbents = scenario_incumbents.slice();

    // Add pvote_year to mutated plan so update_heading_titles can use it
    mutated_plan.pvote_year = pvote_year;

    // Arrays to store mean and SD values for simulations
    var dem_votes_mean = [];
    var rep_votes_mean = [];
    var dem_votes_sd = [];
    var rep_votes_sd = [];

    var all_open_seats = check_all_open_seats(scenario_incumbents);

    // Update each district with scenario data
    for (var district_index = 0; district_index < mutated_plan.districts.length; district_index++) {
        // Get incumbent scenario for this district (e.g., 'O', 'D', 'R', or 'U')
        // When all seats are open we use a slightly different model matrix
        var incumbent_code = all_open_seats ? 'U' : scenario_incumbents[district_index];

        // Find the index in scenarios.incumbents array
        var incumbent_index = scenarios.incumbents.indexOf(incumbent_code);

        if (incumbent_index === -1) {
            console.warn('Unknown incumbent code:', incumbent_code, 'for district', district_index);
            continue;
        }

        // Use helper function for all statistic access
        var dem_mean = get_scenario_statistic(
            scenarios, 'Democratic Votes',
            model_year_idx, vote_swing_index, incumbent_index, district_index
        );
        var rep_mean = get_scenario_statistic(
            scenarios, 'Republican Votes',
            model_year_idx, vote_swing_index, incumbent_index, district_index
        );
        var dem_wins = get_scenario_statistic(
            scenarios, 'Democratic Wins',
            model_year_idx, vote_swing_index, incumbent_index, district_index
        );
        var dem_sd = get_scenario_statistic(
            scenarios, 'Democratic Votes SD',
            model_year_idx, vote_swing_index, incumbent_index, district_index
        );
        var rep_sd = get_scenario_statistic(
            scenarios, 'Republican Votes SD',
            model_year_idx, vote_swing_index, incumbent_index, district_index
        );

        if (dem_mean !== null) {
            mutated_plan.districts[district_index].totals['Democratic Votes'] = dem_mean;
            dem_votes_mean.push(dem_mean);
        }
        if (rep_mean !== null) {
            mutated_plan.districts[district_index].totals['Republican Votes'] = rep_mean;
            rep_votes_mean.push(rep_mean);
        }
        if (dem_wins !== null) {
            mutated_plan.districts[district_index].totals['Democratic Wins'] = dem_wins;
        }
        if (dem_sd !== null) {
            dem_votes_sd.push(dem_sd);
        }
        if (rep_sd !== null) {
            rep_votes_sd.push(rep_sd);
        }

        // Get baseline votes for vote_swing calculation
        var baseline_dem = get_scenario_statistic(
            scenarios, 'Democratic Votes',
            model_year_idx, baseline_vote_swing_index, incumbent_index, district_index
        );
        var baseline_rep = get_scenario_statistic(
            scenarios, 'Republican Votes',
            model_year_idx, baseline_vote_swing_index, incumbent_index, district_index
        );

        var current_dem = dem_mean;
        var current_rep = rep_mean;

        // Calculate vote swing as difference from baseline with same incumbents
        // Handle edge case where total votes might be zero
        var current_total = current_dem + current_rep;
        var baseline_total = baseline_dem + baseline_rep;

        if (current_total > 0 && baseline_total > 0) {
            mutated_plan.districts[district_index].vote_swing =
                current_dem / current_total - baseline_dem / baseline_total;
        } else {
            mutated_plan.districts[district_index].vote_swing = 0.0;
        }
    }

    var EG_sims = [];
    var MMD_sims = [];
    var PB_sims = [];
    var D2_sims = [];

    for (var i in GAUSSIAN_RANDOMS) {
        var random = GAUSSIAN_RANDOMS[i];

        // Generate symmetric vote perturbations (zero-sum per simulation)
        var dem_sim = [];
        var rep_sim = [];

        for (var d = 0; d < dem_votes_mean.length; d++) {
            dem_sim.push(dem_votes_mean[d] + random * dem_votes_sd[d]);
            rep_sim.push(rep_votes_mean[d] - random * rep_votes_sd[d]);
        }

        // Calculate metrics for this simulation
        EG_sims.push(calculate_EG(rep_sim, dem_sim));
        MMD_sims.push(calculate_MMD(rep_sim, dem_sim));
        PB_sims.push(calculate_PB(rep_sim, dem_sim));
        D2_sims.push(calculate_D2(rep_sim, dem_sim));
    }

    // Calculate summary statistics from simulations
    var house = original_plan.model ? original_plan.model.house : null;

    mutated_plan.summary['Efficiency Gap'] = calculate_mean(EG_sims);
    mutated_plan.summary['Efficiency Gap SD'] = calculate_stdev(EG_sims);
    mutated_plan.summary['Efficiency Gap Positives'] = calculate_positives(EG_sims);
    mutated_plan.summary['Efficiency Gap Absolute Percent Rank'] =
        percentrank_abs('eg_adj_avg', house, mutated_plan.summary['Efficiency Gap']);
    mutated_plan.summary['Efficiency Gap Relative Percent Rank'] =
        percentrank_rel('eg_adj_avg', house, mutated_plan.summary['Efficiency Gap']);

    mutated_plan.summary['Mean-Median'] = calculate_mean(MMD_sims);
    mutated_plan.summary['Mean-Median SD'] = calculate_stdev(MMD_sims);
    mutated_plan.summary['Mean-Median Positives'] = calculate_positives(MMD_sims);
    mutated_plan.summary['Mean-Median Absolute Percent Rank'] =
        percentrank_abs('mmd_avg', house, mutated_plan.summary['Mean-Median']);
    mutated_plan.summary['Mean-Median Relative Percent Rank'] =
        percentrank_rel('mmd_avg', house, mutated_plan.summary['Mean-Median']);

    mutated_plan.summary['Partisan Bias'] = calculate_mean(PB_sims);
    mutated_plan.summary['Partisan Bias SD'] = calculate_stdev(PB_sims);
    mutated_plan.summary['Partisan Bias Positives'] = calculate_positives(PB_sims);
    mutated_plan.summary['Partisan Bias Absolute Percent Rank'] =
        percentrank_abs('bias_avg', house, mutated_plan.summary['Partisan Bias']);
    mutated_plan.summary['Partisan Bias Relative Percent Rank'] =
        percentrank_rel('bias_avg', house, mutated_plan.summary['Partisan Bias']);

    mutated_plan.summary['Declination'] = calculate_mean(D2_sims);
    mutated_plan.summary['Declination SD'] = calculate_stdev(D2_sims);
    mutated_plan.summary['Declination Positives'] = calculate_positives(D2_sims);
    mutated_plan.summary['Declination Absolute Percent Rank'] =
        percentrank_abs('dec2_avg', house, mutated_plan.summary['Declination']);
    mutated_plan.summary['Declination Relative Percent Rank'] =
        percentrank_rel('dec2_avg', house, mutated_plan.summary['Declination']);

    // Calculate sensitivity sweep values for the sensitivity chart
    // Chart shows margin swings (D+10, D+8, etc.) but we calculate with vote swings (margin/2)
    // scenarios.vote_swings uses percentage points (5.0 = 5%), not decimal (0.05)
    var sensitivity_vote_swings = [
        { swing: 5.0, name: 'Efficiency Gap +5 Dem' },   // D+10 margin
        { swing: 4.0, name: 'Efficiency Gap +4 Dem' },   // D+8 margin
        { swing: 3.0, name: 'Efficiency Gap +3 Dem' },   // D+6 margin
        { swing: 2.0, name: 'Efficiency Gap +2 Dem' },   // D+4 margin
        { swing: 1.0, name: 'Efficiency Gap +1 Dem' },   // D+2 margin
        { swing: 0.0, name: 'Efficiency Gap 0 Swing' },  // Even (for sensitivity chart center)
        { swing: -1.0, name: 'Efficiency Gap +1 Rep' },  // R+2 margin
        { swing: -2.0, name: 'Efficiency Gap +2 Rep' },  // R+4 margin
        { swing: -3.0, name: 'Efficiency Gap +3 Rep' },  // R+6 margin
        { swing: -4.0, name: 'Efficiency Gap +4 Rep' },  // R+8 margin
        { swing: -5.0, name: 'Efficiency Gap +5 Rep' }   // R+10 margin
    ];

    for (var s = 0; s < sensitivity_vote_swings.length; s++) {
        var sensitivity_swing = sensitivity_vote_swings[s].swing;
        var sensitivity_name = sensitivity_vote_swings[s].name;

        // Find this vote_swing in scenarios.vote_swings array
        var sensitivity_index = scenarios.vote_swings.indexOf(sensitivity_swing);

        if (sensitivity_index === -1) {
            // This swing not in scenarios data, skip
            continue;
        }

        // Recalculate EG simulations at this vote_swing with current scenario_incumbents
        var EG_sims_sensitivity = [];

        for (var i in GAUSSIAN_RANDOMS) {
            var random = GAUSSIAN_RANDOMS[i];
            var dem_sim = [];
            var rep_sim = [];

            for (var d = 0; d < original_plan.districts.length; d++) {
                var incumbent_code = all_open_seats ? 'U' : scenario_incumbents[d];
                var incumbent_index = scenarios.incumbents.indexOf(incumbent_code);

                var dem_mean = get_scenario_statistic(
                    scenarios, 'Democratic Votes',
                    model_year_idx, sensitivity_index, incumbent_index, d
                );
                var rep_mean = get_scenario_statistic(
                    scenarios, 'Republican Votes',
                    model_year_idx, sensitivity_index, incumbent_index, d
                );
                var dem_sd = get_scenario_statistic(
                    scenarios, 'Democratic Votes SD',
                    model_year_idx, sensitivity_index, incumbent_index, d
                );
                var rep_sd = get_scenario_statistic(
                    scenarios, 'Republican Votes SD',
                    model_year_idx, sensitivity_index, incumbent_index, d
                );

                dem_sim.push(dem_mean + random * dem_sd);
                rep_sim.push(rep_mean - random * rep_sd);
            }

            EG_sims_sensitivity.push(calculate_EG(rep_sim, dem_sim));
        }

        mutated_plan.summary[sensitivity_name] = calculate_mean(EG_sims_sensitivity);
    }

    return mutated_plan;
}

function encode_incumbents_rle(incumbents_string)
{
    // Compress incumbents string using run-length encoding
    // e.g., "OOOOOOOOOOOOOOO" -> "15O", "OOOOORRRDDD" -> "5ORR3D"
    // Rules: runs of 3+ use number prefix, runs of 2 repeat character, runs of 1 use single character
    if (!incumbents_string || incumbents_string.length === 0) {
        return '';
    }

    var result = [];
    var current_char = incumbents_string[0];
    var count = 1;

    for (var i = 1; i < incumbents_string.length; i++) {
        if (incumbents_string[i] === current_char) {
            count++;
        } else {
            // Output the run
            if (count >= 3) {
                result.push(count + current_char);
            } else {
                // count is 1 or 2, just repeat the character
                for (var j = 0; j < count; j++) {
                    result.push(current_char);
                }
            }
            current_char = incumbents_string[i];
            count = 1;
        }
    }

    // Don't forget the last run
    if (count >= 3) {
        result.push(count + current_char);
    } else {
        for (var j = 0; j < count; j++) {
            result.push(current_char);
        }
    }

    return result.join('');
}

function decode_incumbents_rle(encoded_string)
{
    // Decode run-length encoded incumbents string
    // Supports both compressed format (e.g., "15O", "5ORR3D") and legacy uncompressed format (e.g., "ORDORD")
    // Returns expanded string, e.g., "15O" -> "OOOOOOOOOOOOOOO"
    if (!encoded_string || encoded_string.length === 0) {
        return '';
    }

    var result = [];
    var regex = /(\d*)([ODR])/g;
    var match;

    while ((match = regex.exec(encoded_string)) !== null) {
        var count = match[1] ? parseInt(match[1]) : 1;
        var char = match[2];
        for (var i = 0; i < count; i++) {
            result.push(char);
        }
    }

    return result.join('');
}

function parse_scenario_hash()
{
    // Parse URL hash to extract margin swing, incumbents, and model year
    // Supports: #scenario, #scenario=margin_swing:3.0, #scenario=incumbents:ORDORD,
    //           #scenario=margin_swing:3.0;incumbents:ORDORD;model_year:2024
    var hash = window.location.hash;

    if (!hash || !hash.match(/\bscenario\b/)) {
        return null; // No scenario hash present
    }

    var result = {
        vote_swing: 0.0,
        incumbents: null,
        model_year: null
    };

    // Parse margin_swing parameter and convert to vote_swing (divide by 2)
    var margin_swing_match = hash.match(/margin_swing:([-\d.]+)/);
    if (margin_swing_match) {
        result.vote_swing = parseFloat(margin_swing_match[1]) / 2;
    }

    // Look for incumbents parameter (string of O/D/R characters, optionally run-length encoded)
    var incumbents_match = hash.match(/incumbents:([0-9ODR]+)/);
    if (incumbents_match) {
        result.incumbents = decode_incumbents_rle(incumbents_match[1]);
    }

    // Look for model_year parameter
    var model_year_match = hash.match(/model_year:(\d+)/);
    if (model_year_match) {
        result.model_year = parseInt(model_year_match[1]);
    }

    return result;
}

function update_scenario_hash(vote_swing, incumbents_string, original_incumbents_string, model_year_idx, scenarios, default_model_year)
{
    // Update URL hash with margin swing (2x vote swing), incumbents, and model year without page reload
    // Omit margin_swing if 0.0, omit incumbents if matches original, omit model_year if matches default
    var parts = [];

    if (vote_swing !== 0.0) {
        // Store as margin_swing in URL (2x for user readability)
        var margin_swing = vote_swing * 2;
        parts.push('margin_swing:' + margin_swing.toFixed(1));
    }

    if (incumbents_string && incumbents_string !== original_incumbents_string) {
        parts.push('incumbents:' + encode_incumbents_rle(incumbents_string));
    }

    // Add model_year if scenarios include model_year dimension and it's not the default from plan
    if (scenarios && has_model_year_dimension(scenarios)) {
        var scenario_key = scenarios.model_years[model_year_idx];
        var parsed = parse_scenario_year_key(scenario_key);
        if (parsed) {
            // Only include in hash if different from plan's default model_year
            if (!default_model_year || parsed.model_year !== default_model_year) {
                parts.push('model_year:' + parsed.model_year);
            }
        }
    }

    var hash_value = parts.length > 0
        ? '#scenario=' + parts.join(';')
        : '#scenario';

    // Use replaceState to avoid adding to browser history
    if (window.history && window.history.replaceState) {
        window.history.replaceState(null, null, hash_value);
    } else {
        window.location.hash = hash_value;
    }
}

function has_scenario_hash()
{
    // Check if URL contains #scenario hash
    var hash = window.location.hash;
    return hash && hash.match(/\bscenario\b/) !== null;
}

function check_scenarios_available(plan)
{
    // Check if scenarios feature is available for this plan
    // Returns: { available: boolean, reason: string }

    // Check if plan has scenarios linked
    if (!plan.scenarios) {
        return { available: false, reason: 'PlanScore did not calculate alternative outcomes for this plan' };
    }

    // Check if all districts have zero vote_swing initially
    // (Plans with pre-applied vote swings shouldn't show the interactive feature)
    for (var i = 0; i < plan.districts.length; i++) {
        if ('vote_swing' in plan.districts[i] && plan.districts[i].vote_swing !== 0.0) {
            return { available: false, reason: 'This plan already has margin swing adjustments applied' };
        }
    }

    return { available: true, reason: null };
}

function update_form_visibility(form, plan, districts_table, on_change_callback)
{
    // Update form visibility based on URL hash and plan availability
    var has_hash = has_scenario_hash();
    var availability = check_scenarios_available(plan);
    var caption_el = form.querySelector('.caption');

    if (!has_hash) {
        // No hash: hide form completely
        form.classList.add('scenario-adjustments-hidden');
        form.classList.remove('scenario-adjustments-disabled');
    } else if (!availability.available) {
        // Has hash but scenarios not available: show disabled form with reason
        form.classList.remove('scenario-adjustments-hidden');
        form.classList.add('scenario-adjustments-disabled');
        // Replace the caption text with the disabled reason
        if (caption_el) {
            caption_el.textContent = availability.reason;
        }
    } else {
        // Has hash and scenarios available: enable form but keep hidden
        // Form will be shown by setup_scenario_interactivity after initialization
        form.classList.remove('scenario-adjustments-disabled');
    }

    // Calculate whether scenarios are active and update incumbent scenario cells
    var is_scenarios_active = has_hash && availability.available;
    if (districts_table) {
        populate_districts_table(plan, districts_table, is_scenarios_active, on_change_callback);
    }
}

function setup_form_visibility_listener(form, plan, districts_table, on_change_callback)
{
    // Set up hashchange listener to toggle form visibility
    window.addEventListener('hashchange', function() {
        update_form_visibility(form, plan, districts_table, on_change_callback);
    });

    // Set initial visibility
    update_form_visibility(form, plan, districts_table, on_change_callback);
}

function setup_scenario_interactivity(original_plan, scenarios, scenario_adjustments_form, districts_table, map_div, metrics_table, score_EG, score_sense, score_PB, score_MM, score_DEC2, scores_FTVA)
{
    // Get the range input and display element
    var range_input = scenario_adjustments_form.querySelector('input[name="margin-swing"]');
    var display = document.getElementById('margin-swing-display');

    // Centralized scheduling for visualization updates with optional debouncing
    // Defers heavy computation using setTimeout to allow browser to paint UI changes first.
    // Uses is_visualization_updating flag to prevent feedback loops from programmatic DOM updates.
    var pending_visualization_update_timer = null;
    var is_visualization_updating = false;

    function schedule_visualization_update(vote_swing, scenario_incumbents, model_year_idx) {
        // Cancel any pending update to avoid queue buildup
        if (pending_visualization_update_timer !== null) {
            clearTimeout(pending_visualization_update_timer);
        }

        // Schedule the heavy work with specified delay
        pending_visualization_update_timer = setTimeout(
            function() {
                is_visualization_updating = true;
                var original_incumbents_string = original_plan.incumbents.join('');
                var scenario_incumbents_string = scenario_incumbents.join('');
                update_scenario_hash(vote_swing, scenario_incumbents_string, original_incumbents_string, model_year_idx, scenarios, original_plan.model_year);
                update_visualizations(vote_swing, scenario_incumbents, model_year_idx);
                pending_visualization_update_timer = null;
                is_visualization_updating = false;
            },
            25 // this msec value feels good after testing on desktop and mobile
        );
    }

    // Helper function to get current model_year_idx from radio buttons
    function get_selected_model_year_idx() {
        var checked_radio = scenario_adjustments_form.querySelector('input[name="model-year"]:checked');
        if (!checked_radio) {
            return 0; // Default to first model year
        }

        // Find the index where model_year matches
        if (has_model_year_dimension(scenarios)) {
            var selected_year = parseInt(checked_radio.value);

            // Parse each scenario key and find matching model_year
            for (var i = 0; i < scenarios.model_years.length; i++) {
                var parsed = parse_scenario_year_key(scenarios.model_years[i]);
                if (parsed && parsed.model_year === selected_year) {
                    return i;
                }
            }

            return 0; // Default to first if not found
        }

        return 0; // Legacy scenarios without model_year dimension always use index 0
    }

    // Define callback for incumbent scenario radio button changes
    // This will be called when a user selects a different incumbency option
    function on_candidate_scenario_change(row, value) {
        // Prevent feedback loop: ignore events triggered by our own programmatic updates
        if (is_visualization_updating) {
            return;
        }

        // Read current incumbents from the table forms
        var scenario_incumbents = read_scenario_incumbents_from_table(districts_table);

        // Get current margin swing from the range input and convert to vote swing
        var margin_swing = parseFloat(range_input.value);
        var vote_swing = margin_swing / 2;

        // Get current model year index
        var model_year_idx = get_selected_model_year_idx();

        // Schedule heavy work, let browser paint input changes first
        schedule_visualization_update(vote_swing, scenario_incumbents, model_year_idx);
    }

    // Initialize vote_swing field if it doesn't exist
    // This ensures the Margin Swing column can be toggled when scenarios are available
    if (original_plan.districts.length > 0 && !('vote_swing' in original_plan.districts[0])) {
        for (var i = 0; i < original_plan.districts.length; i++) {
            original_plan.districts[i].vote_swing = 0.0;
        }
        // Reconstruct table once to include the Margin Swing column (initially hidden)
        construct_districts_table(original_plan, districts_table, true);
        populate_districts_table(original_plan, districts_table, true, on_candidate_scenario_change);
    }

    // Helper function to format vote swing percentages for display
    function format_vote_swing(vote_swing_percent) {
        return nice_margin_swing(vote_swing_percent / 100);
    }

    // Helper function to update all visualizations for a given vote swing and incumbents
    function update_visualizations(vote_swing, scenario_incumbents, model_year_idx) {
        // Create mutated plan with scenario data
        var mutated_plan = create_scenario_plan(original_plan, scenarios, vote_swing, scenario_incumbents, model_year_idx);

        // Update the districts table
        populate_districts_table(mutated_plan, districts_table, true, on_candidate_scenario_change);

        // Update the seat share graphic
        populate_seatshare_graphic(mutated_plan);

        // Update the map colors
        populate_plan_map(mutated_plan, map_div);

        // Update the score cards (each function handles its own validation)
        populate_efficiency_gap_score(mutated_plan, score_EG);
        populate_sensitivity_test(mutated_plan, score_sense);  // Use mutated plan to get scenario-aware sensitivity values
        populate_partisan_bias_score(mutated_plan, score_PB);
        populate_mean_median_score(mutated_plan, score_MM);

        // Only update declination if it's valid
        if (mutated_plan.summary['Declination'] !== null && mutated_plan.summary['Declination'] !== undefined) {
            populate_declination2_score(mutated_plan, score_DEC2);
        }

        // Update the metrics table with new percentrank values
        populate_metrics_table(mutated_plan, metrics_table);
        populate_ftva_race_scores(mutated_plan, scores_FTVA);
    }

    // Set initial values from hash or defaults
    var hash_data = parse_scenario_hash();
    var initial_vote_swing = 0.0;
    var initial_incumbents = original_plan.incumbents.slice();
    var initial_model_year = original_plan.model_year || null; // Use plan's model_year as default

    console.log('Initial setup - plan.model_year:', original_plan.model_year, 'hash_data:', hash_data);

    if (hash_data !== null) {
        initial_vote_swing = hash_data.vote_swing;

        // Parse incumbents from hash if present
        if (hash_data.incumbents !== null) {
            // Validate incumbents length matches district count
            if (hash_data.incumbents.length === original_plan.incumbents.length) {
                initial_incumbents = hash_data.incumbents.split('');
            } else {
                console.warn('Incumbents from hash has wrong length, ignoring:', hash_data.incumbents);
            }
        }

        // Parse model_year from hash if present (overrides plan.model_year)
        if (hash_data.model_year !== null && hash_data.model_year !== undefined) {
            initial_model_year = hash_data.model_year;
            console.log('Overriding with model_year from hash:', initial_model_year);
        }
    }

    console.log('Final initial_model_year:', initial_model_year);

    // Validate that the initial vote swing exists in scenarios
    if (scenarios.vote_swings.indexOf(initial_vote_swing) === -1) {
        console.warn('Vote swing from hash not found in scenarios, defaulting to 0.0:', initial_vote_swing);
        initial_vote_swing = 0.0;
    }

    range_input.value = initial_vote_swing * 2;  // Convert vote_swing to margin_swing for slider
    display.textContent = format_vote_swing(initial_vote_swing);

    // Set up model year radio buttons
    if (has_model_year_dimension(scenarios)) {
        console.log('Setting up model year radio buttons. Available years:', scenarios.model_years, 'Initial year:', initial_model_year);

        // Show/hide radio buttons based on available model years
        var radio_buttons = scenario_adjustments_form.querySelectorAll('input[name="model-year"]');
        var first_available_checked = false;

        // First pass: uncheck all and show/hide based on availability
        for (var i = 0; i < radio_buttons.length; i++) {
            var radio_year = parseInt(radio_buttons[i].value);
            var radio_input = radio_buttons[i];
            var radio_label = scenario_adjustments_form.querySelector('label[for="' + radio_input.id + '"]');

            radio_input.checked = false; // Clear all first

            // Find if this radio_year matches any scenario key
            var found = false;
            for (var j = 0; j < scenarios.model_years.length; j++) {
                var parsed = parse_scenario_year_key(scenarios.model_years[j]);
                if (parsed && parsed.model_year === radio_year) {
                    found = true;
                    break;
                }
            }

            if (found) {
                radio_input.style.display = '';
                if (radio_label) radio_label.style.display = '';
            } else {
                radio_input.style.display = 'none';
                if (radio_label) radio_label.style.display = 'none';
            }
        }

        // Second pass: check the appropriate button
        for (var i = 0; i < radio_buttons.length; i++) {
            var radio_year = parseInt(radio_buttons[i].value);

            // Find if this radio_year matches any scenario key
            var found = false;
            for (var j = 0; j < scenarios.model_years.length; j++) {
                var parsed = parse_scenario_year_key(scenarios.model_years[j]);
                if (parsed && parsed.model_year === radio_year) {
                    found = true;
                    break;
                }
            }

            if (found) {
                // Check radio button based on initial_model_year (from hash or plan.model_year)
                if (initial_model_year !== null && radio_year === initial_model_year) {
                    console.log('Checking radio button for year:', radio_year);
                    radio_buttons[i].checked = true;
                    first_available_checked = true;
                    break; // Found and checked the right one
                } else if (!first_available_checked && initial_model_year === null) {
                    // Default to first available radio button if no model_year specified
                    console.log('Checking first available radio button for year:', radio_year);
                    radio_buttons[i].checked = true;
                    first_available_checked = true;
                    break; // Checked the first available
                }
            }
        }

        // Add change listener to model year radio buttons
        for (var i = 0; i < radio_buttons.length; i++) {
            radio_buttons[i].addEventListener('change', function(event) {
                if (is_visualization_updating) {
                    return;
                }

                var margin_swing = parseFloat(range_input.value);
                var vote_swing = margin_swing / 2;
                var scenario_incumbents = read_scenario_incumbents_from_table(districts_table);
                var model_year_idx = get_selected_model_year_idx();

                schedule_visualization_update(vote_swing, scenario_incumbents, model_year_idx);
            });
        }
    } else {
        // Legacy scenarios without model_year dimension: disable model year selection
        var radio_buttons = scenario_adjustments_form.querySelectorAll('input[name="model-year"]');

        // Disable all model year radio buttons
        for (var i = 0; i < radio_buttons.length; i++) {
            radio_buttons[i].disabled = true;
        }

        // Add a class to the model year container for styling
        var model_year_container = scenario_adjustments_form.querySelector('#model-year');
        if (model_year_container) {
            model_year_container.classList.add('model-year-disabled');
        }
    }

    // Always update visualizations on initial load (even for 0.0)
    // This ensures that if we were waiting_for_scenarios, we now populate everything
    var initial_model_year_idx = get_selected_model_year_idx();
    update_visualizations(initial_vote_swing, initial_incumbents, initial_model_year_idx);

    // Show the form now that it's fully initialized
    scenario_adjustments_form.classList.remove('scenario-adjustments-hidden');
    scenario_adjustments_form.classList.remove('scenario-adjustments-disabled');

    // Add input listener to range slider for live updates
    range_input.addEventListener('input', function(event) {
        // Get the selected margin swing value from slider and convert to vote swing for server data
        var margin_swing = parseFloat(event.target.value);
        var vote_swing = margin_swing / 2;

        // Read current incumbents from the table forms
        var scenario_incumbents = read_scenario_incumbents_from_table(districts_table);

        // Get current model year index
        var model_year_idx = get_selected_model_year_idx();

        // Update the display immediately
        display.textContent = format_vote_swing(vote_swing);

        // Schedule heavy work, let browser paint input changes first
        schedule_visualization_update(vote_swing, scenario_incumbents, model_year_idx);
    });

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

function populate_candidate_scenario_content(cell, row, value, is_scenarios_active, on_change_callback)
{
    var incumbency = {'O': 'Open Seat', 'D': 'Democratic Incumbent', 'R': 'Republican Incumbent'};

    // Handle inactive case: show text only if no form exists
    // (never go from active to inactive - forms are never removed once created)
    if (!is_scenarios_active) {
        if (!cell.firstChild || cell.firstChild.tagName !== 'FORM') {
            cell.textContent = incumbency[value] || '';
        }
        return;
    }

    // Handle active case with existing form: just update checked state
    if (cell.firstChild && cell.firstChild.tagName === 'FORM') {
        var form = cell.firstChild;
        form.childNodes[0].checked = (value === 'D');
        form.childNodes[2].checked = (value === 'O');
        form.childNodes[4].checked = (value === 'R');
        return;
    }

    // Handle active case with no form: create new form
    cell.innerHTML = [
        `<form class="candidate-scenario">`,
        `<input type="radio" name="C${row}" value="D" id="D${row}"/><label for="D${row}" class="D">DEM</label>`,
        `<input type="radio" name="C${row}" value="O" id="O${row}"/><label for="O${row}" class="O">OPEN</label>`,
        `<input type="radio" name="C${row}" value="R" id="R${row}"/><label for="R${row}" class="R">REP</label>`,
        `</form>`
    ].join('');

    // Attach event listeners if callback provided
    if (on_change_callback) {
        var form = cell.firstChild;
        var radios = form.querySelectorAll('input[type="radio"]');
        for (var i = 0; i < radios.length; i++) {
            radios[i].addEventListener('change', function(e) {
                on_change_callback(row, e.target.value);
            });
        }
    }

    // Set initial checked state
    var form = cell.firstChild;
    form.childNodes[0].checked = (value === 'D');
    form.childNodes[2].checked = (value === 'O');
    form.childNodes[4].checked = (value === 'R');
}

function construct_districts_table(plan, districts_table, is_scenarios_active)
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

        // Mark Margin Swing column for show/hide toggling
        if (heading_title === 'Margin Swing') {
            th.dataset.columnName = 'Margin Swing';
        }

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

            if (heading_title === 'Incumbent Scenario') {
                populate_candidate_scenario_content(cell, i, '', is_scenarios_active, null);
            } else if (heading_title === 'Margin Swing') {
                // Mark Margin Swing column for show/hide toggling
                cell.dataset.columnName = 'Margin Swing';
            }

            tr.appendChild(cell);
        }

        tbody.appendChild(tr);
    }

    table.appendChild(tbody);
    districts_table.appendChild(table);
}

function populate_districts_table(plan, districts_table, is_scenarios_active, on_change_callback)
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

    // Add or remove 'all-open-seats' class based on incumbency
    const table = districts_table.querySelector('table');
    if (table && plan.incumbents && plan.incumbents.length > 0) {
        if (check_all_open_seats(plan.incumbents)) {
            table.classList.add('all-open-seats');
        } else {
            table.classList.remove('all-open-seats');
        }
    }

    // Update thead headers with new pvote_year data
    const thead = districts_table.querySelector('thead tr');
    if (thead) {
        const header_cells = thead.querySelectorAll('th');
        var header_index = 0;

        for (var j = 0; j < table_array[0].length; j++) {
            const heading_title = table_array[0][j];
            if (heading_title == SHY_COLUMN) {
                continue;
            }

            if (header_cells[header_index]) {
                header_cells[header_index].innerHTML = heading_title;
            }
            header_index++;
        }
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
            if (heading_title == 'Incumbent Scenario') {
                value = table_array[table_row_index][j];
            } else if (typeof table_array[table_row_index][j] == 'number') {
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
                if (heading_title == 'Incumbent Scenario') {
                    populate_candidate_scenario_content(cells[cell_index], i, value, is_scenarios_active, on_change_callback);
                } else if (is_string) {
                    cells[cell_index].innerHTML = value;
                } else {
                    cells[cell_index].textContent = value;
                }
            }
            cell_index++;
        }
    }

    // Show or hide the Margin Swing column based on whether all swings are 0.0
    var all_swings_zero = true;
    for (var i = 0; i < plan.districts.length; i++) {
        if (plan.districts[i].vote_swing && plan.districts[i].vote_swing !== 0.0) {
            all_swings_zero = false;
            break;
        }
    }

    var swing_cells = districts_table.querySelectorAll('[data-column-name="Margin Swing"]');
    for (var i = 0; i < swing_cells.length; i++) {
        swing_cells[i].style.display = all_swings_zero ? 'none' : '';
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
            // Add a span for the value (includes colon)
            var value_span = document.createElement('span');
            value_span.className = 'score-value';
            value_span.dataset.metric = 'eg';
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
        gap_amount = nice_percent(Math.abs(gap)),
        gap_amount_suffixed = gap_amount + partisan_suffix(gap);

    for(node = score_EG.firstChild; node = node.nextSibling; node)
    {
        if(node.nodeName == 'H3') {
            var value_span = node.querySelector('.score-value[data-metric="eg"]');
            if(value_span) {
                value_span.innerHTML = ': ' + gap_amount_suffixed;
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
            // Add a span for the value (includes colon)
            var value_span = document.createElement('span');
            value_span.className = 'score-value';
            value_span.dataset.metric = 'd2';
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
        dec2_amount = (Math.round(Math.abs(declination) * 100) / 100),
        dec2_amount_suffixed = dec2_amount + partisan_suffix(declination);

    for(node = score_DEC2.firstChild; node = node.nextSibling; node)
    {
        if(node.nodeName == 'H3') {
            var value_span = node.querySelector('.score-value[data-metric="d2"]');
            if(value_span) {
                value_span.innerHTML = ': ' + dec2_amount_suffixed;
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
            // Add a span for the value (includes colon)
            var value_span = document.createElement('span');
            value_span.className = 'score-value';
            value_span.dataset.metric = 'pb';
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
    // Check if vote shares are within 45-55% range
    if (plan_voteshare(plan) >= 0.1) {
        hide_score_with_reason(score_PB,
            'The parties\' statewide vote shares are ' + nice_plan_voteshare(plan) + ' based on the model.'
            + ' Partisan bias is shown only where the parties\' statewide vote shares fall between 45% and 55%.'
            + ' Outside this range the metric\'s assumptions are not plausible.');
        return;
    }

    var bias = plan.summary['Partisan Bias'],
        bias_amount = nice_percent(Math.abs(bias)),
        bias_amount_suffixed = bias_amount + partisan_suffix(bias);

    for(node = score_PB.firstChild; node = node.nextSibling; node)
    {
        if(node.nodeName == 'H3') {
            var value_span = node.querySelector('.score-value[data-metric="pb"]');
            if(value_span) {
                value_span.innerHTML = ': ' + bias_amount_suffixed;
            }

        } else if(node.nodeName == 'DIV' && node.dataset.metric == 'pb') {
            // Show the DIV in case it was hidden by hide_score_with_reason
            node.style.display = '';
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
        if(node.nodeName == 'H3')
        {
            // Clear the score value from the title
            var value_span = node.querySelector('.score-value');
            if(value_span) {
                value_span.innerHTML = '';
            }

        } else if(node.nodeName == 'DIV')
        {
            // Hide the chart DIV instead of clearing it, preserving the chart structure
            node.style.display = 'none';

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
            // Add a span for the value (includes colon)
            var value_span = document.createElement('span');
            value_span.className = 'score-value';
            value_span.dataset.metric = 'mm';
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
    // Check if vote shares are within 45-55% range
    if (plan_voteshare(plan) >= 0.1) {
        hide_score_with_reason(score_MM,
            'The parties\' statewide vote shares are ' + nice_plan_voteshare(plan) + ' based on the model.'
            + ' The mean-median difference is shown only where the parties\' statewide vote shares fall between 45% and 55%.'
            + ' Outside this range the metric\'s assumptions are not plausible.');
        return;
    }

    var diff = plan.summary['Mean-Median'],
        diff_amount = nice_percent(Math.abs(diff)),
        diff_amount_suffixed = diff_amount + partisan_suffix(diff);

    for(node = score_MM.firstChild; node = node.nextSibling; node)
    {
        if(node.nodeName == 'H3') {
            var value_span = node.querySelector('.score-value[data-metric="mm"]');
            if(value_span) {
                value_span.innerHTML = ': ' + diff_amount_suffixed;
            }

        } else if(node.nodeName == 'DIV' && node.dataset.metric == 'mm') {
            // Show the DIV in case it was hidden by hide_score_with_reason
            node.style.display = '';
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
    // Check if Highcharts is available
    if (typeof Highcharts === 'undefined') {
        console.error('Highcharts library failed to load, sensitivity test chart will not be displayed.');
        score_sense.innerHTML = '<p>Chart unavailable.</p>';
        return;
    }

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
            categories: ['D+10', 'D+8', 'D+6', 'D+4', 'D+2', '0', 'R+2', 'R+4', 'R+6', 'R+8', 'R+10'],
            title: { text: 'Possible Margin Swing' }
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

    // Use 'Efficiency Gap 0 Swing' for chart center if available (scenario mode),
    // otherwise fall back to 'Efficiency Gap' (non-scenario mode)
    var center_value = plan.summary['Efficiency Gap 0 Swing'] !== undefined
        ? plan.summary['Efficiency Gap 0 Swing']
        : plan.summary['Efficiency Gap'];

    var data = [
        100 * plan.summary['Efficiency Gap +5 Dem'],
        100 * plan.summary['Efficiency Gap +4 Dem'],
        100 * plan.summary['Efficiency Gap +3 Dem'],
        100 * plan.summary['Efficiency Gap +2 Dem'],
        100 * plan.summary['Efficiency Gap +1 Dem'],
        100 * center_value,
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

    if(plan_voteshare(plan) < .1) {
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

function construct_plan_map(data, div, plan, table, waiting_for_scenarios)
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

    // Store references for later updates
    div._geojson_layer = geojson;
    div._geojson_data = data;
    div._leaflet_map = map;

    // Populate with initial plan data (unless waiting for scenarios)
    if (!waiting_for_scenarios) {
        populate_plan_map(plan, div);
    }
}

function populate_plan_map(plan, div)
{
    // NOTE: For future enhancement, if we want to add scenario-dependent data to popups
    // (e.g., "Democratic Win Probability: 73%"), we would update popup content here
    // using layer.getPopup().setContent(newContent) or layer.bindPopup(newContent).
    // Currently, popups only show district number and incumbent status, which are
    // scenario-independent, so they don't need updates.

    var geojson = div._geojson_layer;
    var data = div._geojson_data;

    if (!geojson || !data) {
        return;
    }

    // Update district colors based on current plan data
    Object.values(geojson._layers).forEach(function(layer) {
        var index = data.features.indexOf(layer.feature);
        var district = plan.districts[index];
        var color = which_district_color(district, plan);
        layer.setStyle({ color: color, fillOpacity: .5, weight: 2 });
    });
}

function update_heading_titles(head, pvote_year)
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
        if (pvote_year == undefined) {
            // No PVote year defined so assume the newest one should be shown
            switch (true) {
                case (head[i] == 'Trump (R) 2016' && head.indexOf('Trump (R) 2020') >= 0):
                case (head[i] == 'Trump (R) 2016' && head.indexOf('Trump (R) 2024') >= 0):
                case (head[i] == 'Trump (R) 2020' && head.indexOf('Trump (R) 2024') >= 0):
                case (head[i] == 'Clinton (D) 2016' && head.indexOf('Biden (D) 2020') >= 0):
                case (head[i] == 'Clinton (D) 2016' && head.indexOf('Harris (D) 2024') >= 0):
                case (head[i] == 'Biden (D) 2020' && head.indexOf('Harris (D) 2024') >= 0):
                    head[i] = SHY_COLUMN;
            }
        } else {
            // Show the used PVote year
            switch (true) {
                case (head[i] == 'Clinton (D) 2016' && pvote_year != 2016):
                case (head[i] == 'Trump (R) 2016' && pvote_year != 2016):
                case (head[i] == 'Biden (D) 2020' && pvote_year != 2020):
                case (head[i] == 'Trump (R) 2020' && pvote_year != 2020):
                case (head[i] == 'Harris (D) 2024' && pvote_year != 2024):
                case (head[i] == 'Trump (R) 2024' && pvote_year != 2024):
                    head[i] = SHY_COLUMN;
            }
        }

        if(head[i] == 'CVAP 2019') {
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

function update_margin_swings(head, row)
{
    var swing_index = head.indexOf('Margin Swing');

    if(swing_index >= 0)
    {
        row[swing_index] = nice_margin_swing(row[swing_index]);
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
    var flippy_colors = [LEAN_BLUE_COLOR_HEX, LEAN_RED_COLOR_HEX],
        fields = FIELDS.slice();

    // Build list of columns
    var head_row = ['District'],
        all_rows = [head_row],
        field, current_row, field_missing, flip_chance;

    const has_incumbency = plan_has_incumbency(plan);

    if(has_incumbency) {
        head_row.push('Incumbent Scenario');
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
            new_row.push(plan.incumbents[j]);
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
            } else if('vote_swing' in plan.districts[j] && field == 'Margin Swing') {
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
        } else if(field == 'Margin Swing' && field_missing) {
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

            } else if('vote_swing' in plan.districts[j] && field == 'Margin Swing') {
                current_row.push(plan.districts[j].vote_swing);
            }
        }
    }

    for(var j = 1; j < all_rows.length; j++)
    {
        update_margin_swings(head_row, all_rows[j]);
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
    update_heading_titles(head_row, plan.pvote_year);
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

        // Check if we should wait for scenarios before populating
        // Only wait if hash contains a non-default value (not 0.0)
        var initial_vote_swing = parse_scenario_hash();
        var waiting_for_scenarios = (
            plan.scenarios !== undefined &&
            initial_vote_swing !== null &&
            initial_vote_swing !== 0.0
        );

        // Set up form visibility based on hash and availability
        setup_form_visibility_listener(scenario_adjustments_form, plan, districts_table, null);

        // Plan is done parsing and we can render the page
        hide_message(score_section, message_section);

        // Clear out and repopulate plan description, upload date, plan type
        clear_element(description_el);
        const headings = get_plan_headings(plan, modified_at);
        if (headings.description) {
            const desc_el = document.createElement('h1');
            desc_el.textContent = plan.description;
            description_el.append(desc_el);
            document.title = document.title + ' :: ' + plan.description;
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
        construct_districts_table(plan, districts_table, false);
        construct_seatshare_graphic(plan, districts_table);
        if (!waiting_for_scenarios) {
            populate_districts_table(plan, districts_table, false, null);
            populate_seatshare_graphic(plan);
        }

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
        construct_sensitivity_test(score_sense);

        if('Declination' in plan.summary && plan.summary['Declination Is Valid'] !== 0) {
            construct_declination2_score(score_DEC2);
        } else if('Declination' in plan.summary) {
            hide_score_with_reason(score_DEC2,
                'Declination is only shown where both parties each win one or more'
                + 'seats in a sufficient number of predicted scenarios<sup>*</sup>.');
        } else {
            hide_score_with_reason(score_DEC2,
                'We were not yet calculating declination at the time that we scored this plan.');
        }

        // Always construct the score elements, even if initially outside valid range
        construct_partisan_bias_score(score_PB);
        construct_mean_median_score(score_MM);

        // Hide if outside valid range initially
        if(plan_voteshare(plan) >= .1) {
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
        construct_ftva_race_scores(scores_FTVA);

        // Kick off scenario loading after table construction if available and hash present
        // This ensures the table structure exists before any populate calls from scenario callbacks
        if (plan.scenarios !== undefined && has_scenario_hash()) {
            // Add disabled class while loading scenarios
            scenario_adjustments_form.classList.add('scenario-adjustments-disabled');

            load_plan_scenarios(geom_prefix + plan.scenarios.replace(/^\//, ''), plan, scenario_adjustments_form, districts_table, map_div, metrics_table, score_EG, score_sense, score_PB, score_MM, score_DEC2, scores_FTVA);
        }

        if (!waiting_for_scenarios) {
            populate_efficiency_gap_score(plan, score_EG);
            populate_sensitivity_test(plan, score_sense);

            if('Declination' in plan.summary && plan.summary['Declination Is Valid'] !== 0) {
                populate_declination2_score(plan, score_DEC2);
            }

            if(plan_voteshare(plan) < .1) {
                populate_partisan_bias_score(plan, score_PB);
                populate_mean_median_score(plan, score_MM);
            }

            populate_metrics_table(plan, metrics_table);
            populate_ftva_race_scores(plan, scores_FTVA);
        }

        if('library_metadata' in plan && plan['library_metadata']) {
            construct_library_metadata(metadata_el);
            if (!waiting_for_scenarios) {
                populate_library_metadata(plan, metadata_el, geom_prefix);
            }
        } else {
            metadata_el.style.display = 'none';
        }

        // Go on to load the map (construct_plan_map includes populate_plan_map call).
        // Note: The map's populate call is inside construct_plan_map, so we need special handling.
        load_plan_map(geom_prefix + plan.geometry_key, map_div, plan, districts_table, waiting_for_scenarios);
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

function load_plan_scenarios(url, plan, scenario_adjustments_form, districts_table, map_div, metrics_table, score_EG, score_sense, score_PB, score_MM, score_DEC2, scores_FTVA)
{
    var request = new XMLHttpRequest();
    request.open('GET', url, true);

    request.onload = function()
    {
        if(request.status >= 200 && request.status < 400)
        {
            // Returns a scenarios dictionary
            var data = JSON.parse(request.responseText);
            console.log('Loaded scenarios:', data);
            adjust_scenario_stats(data);
            console.log('New scenarios:', data);
            setup_scenario_interactivity(plan, data, scenario_adjustments_form, districts_table, map_div, metrics_table, score_EG, score_sense, score_PB, score_MM, score_DEC2, scores_FTVA);
        }
    };

    request.onerror = function() { /* There was a connection error of some sort */ };
    request.send();
}

function load_plan_map(url, div, plan, table, waiting_for_scenarios)
{
    var request = new XMLHttpRequest();
    request.open('GET', url, true);

    request.onload = function()
    {
        if(request.status >= 200 && request.status < 400)
        {
            // Returns a GeoJSON dictionary
            var data = JSON.parse(request.responseText);
            console.log('Loaded map:', data);
            construct_plan_map(data, div, plan, table, waiting_for_scenarios);
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
// Adjust scenario form position to avoid overlapping with Olark chat button
function adjust_scenario_form_for_olark()
{
    var scenario_form = document.getElementById('scenario-adjustments');
    if (!scenario_form) return;

    // Only adjust on narrow viewports (below desktop breakpoint)
    // Use matchMedia to match CSS @media query exactly (handles scrollbar width correctly)
    var is_narrow = !window.matchMedia('(min-width: 769px)').matches;

    if (is_narrow) {
        // Look for any fixed-position elements in the bottom-right corner
        // This detects Olark or similar chat widgets without hardcoding IDs
        var bottom_right_elements = Array.from(document.querySelectorAll('*')).filter(function(el) {
            // Skip our own form
            if (el === scenario_form) return false;

            var style = window.getComputedStyle(el);
            if (style.position !== 'fixed') return false;

            var right = parseInt(style.right);
            var bottom = parseInt(style.bottom);

            // Element is in bottom-right if right and bottom are both small positive numbers
            return !isNaN(right) && right >= 0 && right < 100 &&
                   !isNaN(bottom) && bottom >= 0 && bottom < 100;
        });

        if (bottom_right_elements.length > 0) {
            // Found other fixed element(s) in bottom-right, move form up to avoid overlap
            scenario_form.style.bottom = '90px';
        } else {
            // No other elements, use default
            scenario_form.style.bottom = '20px';
        }
    } else {
        // Desktop: clear inline style to let CSS media query handle it
        scenario_form.style.bottom = '';
    }
}

// Run on page load and when window resizes
if (typeof window !== 'undefined') {
    window.addEventListener('load', function() {
        // Initial adjustment
        adjust_scenario_form_for_olark();

        // Check again after a delay to catch late-loading Olark
        setTimeout(adjust_scenario_form_for_olark, 1000);

        // Set up grow/shrink checkbox for scenario adjustments form
        var grow_shrink_checkbox = document.getElementById('grow-shrink');
        var scenario_form = document.getElementById('scenario-adjustments');
        if (grow_shrink_checkbox && scenario_form) {
            grow_shrink_checkbox.addEventListener('change', function() {
                if (this.checked) {
                    // Checked = grown (remove shrunken class)
                    scenario_form.classList.remove('scenario-adjustments-shrunken');
                } else {
                    // Unchecked = shrunken (add shrunken class)
                    scenario_form.classList.add('scenario-adjustments-shrunken');
                }
            });
        }
    });

    window.addEventListener('resize', adjust_scenario_form_for_olark);
}

if(typeof module !== 'undefined' && module.exports)
{
    module.exports = {
        format_url,
        nice_count,
        nice_string,
        nice_percent,
        nice_round_percent,
        nice_margin_swing,
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
        update_margin_swings,
        update_acs2015_percentages,
        update_acs2016_percentages,
        update_cvap2015_percentages,
        update_heading_titles,
        adjust_scenario_stats,
        create_scenario_plan,
        parse_scenario_hash,
        encode_incumbents_rle,
        decode_incumbents_rle,
        get_scenario_statistic,
        has_model_year_dimension,
        parse_scenario_year_key,
        swing_vote,
        calculate_EG,
        calculate_MMD,
        calculate_PB,
        calculate_D2,
        calculate_mean,
        calculate_stdev,
        calculate_positives,
        percentrank_abs,
        percentrank_rel,
        SHY_COLUMN,
    };
}
