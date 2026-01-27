assert = require('assert');
plan = require('./planscore/website/static/plan.js');
annotate_new = require('./planscore/website/static/annotate-new.js');

// Mock gaussian randoms for testing
global.GAUSSIAN_RANDOMS = [1.647, -1.307, -0.401, 0.925, -0.827, 0.366, 0.684, -0.593, -1.197, 0.702];

// Mock historical percentrank data for testing
global.HISTORICAL_PERCENTRANK_DATA = {
    ushouse: {
        eg_adj_avg: [-0.15, -0.10, -0.05, 0.00, 0.05, 0.10, 0.15],
        bias_avg: [-0.12, -0.08, -0.04, 0.00, 0.04, 0.08, 0.12],
        mmd_avg: [-0.20, -0.10, 0.00, 0.10, 0.20],
        dec2_avg: [-0.50, -0.25, 0.00, 0.25, 0.50]
    },
    statehouse: {
        eg_adj_avg: [-0.20, -0.15, -0.10, -0.05, 0.00, 0.05, 0.10, 0.15, 0.20],
        bias_avg: [-0.15, -0.10, -0.05, 0.00, 0.05, 0.10, 0.15],
        mmd_avg: [-0.25, -0.15, -0.05, 0.05, 0.15, 0.25],
        dec2_avg: [-0.60, -0.40, -0.20, 0.00, 0.20, 0.40, 0.60]
    },
    statesenate: {
        eg_adj_avg: [-0.18, -0.12, -0.06, 0.00, 0.06, 0.12, 0.18],
        bias_avg: [-0.14, -0.09, -0.04, 0.00, 0.04, 0.09, 0.14],
        mmd_avg: [-0.22, -0.11, 0.00, 0.11, 0.22],
        dec2_avg: [-0.55, -0.30, 0.00, 0.30, 0.55]
    }
};

// Object.entries() polyfill for circle-ci machines with Node 6
if (!Object.entries) {
    Object.entries = function (obj) {
        var ownProps = Object.keys(obj),
        i = ownProps.length,
        resArray = new Array(i); // preallocate the Array
        while (i--) resArray[i] = [ownProps[i], obj[ownProps[i]]];

        return resArray;
    };
}

var NC_index = require('./data/sample-NC-1-992/index.json'),
    NC_incomplete_index = require('./data/sample-NC-1-992-incomplete/index.json'),
    NC_simple_index = require('./data/sample-NC-1-992-simple/index.json'),
    NC_multisim_index = require('./data/sample-NC-simulations/index.json'),
    NC_public_index = require('./data/sample-NC5.1/index.json'),
    NC_2019_preread_start = require('./data/sample-NC2019/index-preread-start.json'),
    NC_2019_preread_end = require('./data/sample-NC2019/index-preread-end.json'),
    NC_2019_no_incumbency = require('./data/sample-NC2019/index-no-incumbency.json'),
    NC_2019_incumbency = require('./data/sample-NC2019/index-incumbency.json'),
    NC_2020 = require('./data/sample-NC2020/index.json'),
    NC_2020_unified = require('./data/sample-NC-unified/index.json'),
    NC_2025_index = require('./data/sample-NC2025/index.json'),
    NC_2025_scenarios = require('./data/sample-NC2025/scenarios.json'),
    NC_2025_incumbents_index = require('./data/sample-NC2025-incumbents/index.json'),
    NC_2025_incumbents_scenarios = require('./data/sample-NC2025-incumbents/scenarios.json'),
    FL_2020_declination = require('./data/sample-FL-declination/index.json'),
    CT_2021_water_district = require('./data/sample-CT-mostly-water-district/index.json'),
    MS_zero_vote_swings = require('./data/sample-MS-zero-vote-swings/index.json'),
    MS_vote_swings = require('./data/sample-MS-vote-swings/index.json');

// Old-style red vs. blue plan

assert.equal(plan.get_plan_headings(NC_simple_index, new Date(2018, 0, 14)).description,
   false, 'Should identify there is no description');

assert.equal(plan.which_score_summary_name(NC_simple_index),
    'Efficiency Gap', 'Should pick out the right summary name');

assert.deepEqual(plan.which_score_column_names(NC_simple_index),
    ['Voters', 'Blue Votes', 'Red Votes'], 'Should pick out the right column names');

assert.equal(plan.which_district_color(NC_simple_index.districts[0], NC_simple_index),
    '#D45557', 'Should return the red district color');

assert.equal(plan.which_district_color(NC_simple_index.districts[7], NC_simple_index),
    '#4D90D1', 'Should return the blue district color');

assert.equal(plan.get_seatshare_array(NC_simple_index), undefined, 'Should omit seat shares');

var plan_array1 = plan.plan_array(NC_simple_index);
assert.equal(plan_array1.length, 14, 'Should have a header with 13 districts');

// Incomplete plan, seen just after upload but before scoring is complete

assert.equal(plan.get_plan_headings(NC_incomplete_index, new Date(2018, 0, 14)).description,
    false, 'Should find the right description');

assert.strictEqual(plan.which_score_summary_name(NC_incomplete_index),
    null, 'Should return a null summary name');

assert.deepEqual(plan.which_score_column_names(NC_incomplete_index),
    [], 'Should return an empty list of column names');

var plan_array2 = plan.plan_array(NC_incomplete_index);
assert.equal(plan_array2, undefined, 'Should have an undefined table');

// North Carolina plan with named house and parties

assert.equal(plan.get_plan_headings(NC_index, new Date(2018, 0, 14)).description,
    'This plan is okay.', 'Should find the right description');

assert.equal(plan.which_score_summary_name(NC_index),
    'US House Efficiency Gap', 'Should pick out the right summary name');

assert.deepEqual(plan.which_score_column_names(NC_index),
    ['Population', 'Voting-Age Population', 'Black Voting-Age Population',
     'US House Dem Votes', 'US House Rep Votes'], 'Should pick out the right column names');

assert.equal(plan.format_url('https://example.com/{id}.html', 'xyz'),
    'https://example.com/xyz.html', 'URL should format correctly');

assert.equal(plan.which_district_color(NC_index.districts[0], NC_index),
    '#D45557', 'Should return the red district color');

assert.equal(plan.which_district_color(NC_index.districts[7], NC_index),
    '#4D90D1', 'Should return the blue district color');

assert.equal(plan.get_seatshare_array(NC_index), undefined, 'Should omit seat shares');

var plan_array3 = plan.plan_array(NC_index);
assert.equal(plan_array3.length, 14, 'Should have a header with 13 districts');

// New-style North Carolina plan with confidence intervals from simulations

assert.equal(plan.get_plan_headings(NC_multisim_index, new Date(2018, 0, 14)).description,
    false, 'Should find the right description');

assert.equal(plan.which_score_summary_name(NC_multisim_index),
    'Efficiency Gap', 'Should pick out the right summary name');

assert.deepEqual(plan.which_score_column_names(NC_multisim_index),
    [
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
        /*, 'Polsby-Popper', 'Reock'*/
    ],
    'Should pick out the right column names');

assert.equal(plan.which_district_color(NC_multisim_index.districts[0], NC_multisim_index),
    '#D45557', 'Should return the red district color');

assert.equal(plan.which_district_color(NC_multisim_index.districts[7], NC_multisim_index),
    '#4D90D1', 'Should return the blue district color');

assert.equal(plan.get_seatshare_array(NC_multisim_index), undefined, 'Should omit seat shares');

var plan_array4 = plan.plan_array(NC_multisim_index);
assert.equal(plan_array4.length, 14, 'Should have a header with 13 districts');

assert.deepEqual(plan_array4[0],
    ['District', 'Predicted Democratic Vote Share',
    'Predicted Republican Vote Share'],
    'Should pick out the right column names');

assert.deepEqual(plan_array4[1],
    ['1', '47.4% (±0.9%)', '52.6% (±0.9%)'],
    'Should pick out the right column values');

assert.deepEqual(plan_array4[13],
    ['13', '42.3% (±1.0%)', '57.7% (±1.0%)'],
    'Should pick out the right column values');

assert.deepEqual(plan.get_plan_headings(NC_multisim_index, new Date(2018, 0, 14)), {
    description: false,
    uploaded: 'Uploaded: 1/14/2018',
    date_only: 'Jan. 14, 2018'
});

// North Carolina plan in proposed final form

var plan_array5 = plan.plan_array(NC_public_index);
assert.equal(plan_array5.length, 14, 'Should have a header with 13 districts');

assert.deepEqual(plan.get_plan_headings(NC_public_index), {
    description: 'Here is a great plan.',
    uploaded: 'Uploaded: 1/14/2018',
    date_only: 'Jan. 14, 2018'
}, 'Should determine the right heading text');

assert.deepEqual(plan_array5[0],
    ['District', 'Pop. 2010', 'Pop. 2015',
    'Black Pop. 2015', 'Hispanic Pop. 2015',
    'Predicted Democratic Vote Share', 'Predicted Republican Vote Share',
    'Clinton (D) 2016', 'Trump (R) 2016'
    /*, 'Polsby-Popper', 'Reock'*/],
    'Should pick out the right column names');

assert.deepEqual(plan_array5[1],
    ['1', 733460.0, 734814.32, '46.3%', '8.3%', '66.1% (±0.9%)', '33.9% (±0.9%)', 229243.28, 110009.85/*, 0.1992, 0.3469*/],
    'Should pick out the right column values');

assert.deepEqual(plan_array5[13],
    ['13', 733505.0, 747501.53, '22.8%', '7.5%', '43.9% (±0.6%)', '56.1% (±0.6%)', 158659.94, 192109.37/*, 0.2274, 0.3557*/],
    'Should pick out the right column values');

assert.deepEqual(plan.get_plan_headings(NC_public_index, undefined), {
    description: 'Here is a great plan.',
    uploaded: 'Uploaded: 1/14/2018',
    date_only: 'Jan. 14, 2018'
}, 'Should determine the right heading text');

assert.equal(plan.which_district_color(NC_public_index.districts[0], NC_public_index),
    '#4D90D1', 'Should return the blue district color');

assert.equal(plan.which_district_color(NC_public_index.districts[1], NC_public_index),
    '#838383', 'Should return the unknown district color');

assert.equal(plan.which_district_color(NC_public_index.districts[2], NC_public_index),
    '#D45557', 'Should return the red district color');

assert.equal(plan.get_seatshare_array(NC_public_index), undefined, 'Should omit seat shares');

// Plan with default incumbency and no model support

var plan_array6 = plan.plan_array(NC_2019_no_incumbency);
assert.equal(plan_array6.length, 14, 'Should have a header with 13 districts');

assert.deepEqual(plan_array6[0],
    ['District', 'Pop. 2010', 'Pop. 2016',
    'Black Pop. 2016', 'Hispanic Pop. 2016',
    'Predicted Democratic Vote Share', 'Predicted Republican Vote Share'],
    'Should pick out the right column names');

assert.deepEqual(plan_array6[1],
    ['1', 730943, 738237.35, '46.3%', '8.7%', '72.2% (±4.3%)', '27.8% (±2.3%)'],
    'Should pick out the right column values');

assert.deepEqual(plan_array6[2],
    ['2', 734253, 824484.63, '21.3%', '9.7%', '50.8% (±3.0%)', '49.2% (±2.9%)'],
    'Should pick out the right column values');

assert.deepEqual(plan_array6[3],
    ['3', 732416, 708958.98, '23.2%', '7.9%', '44.1% (±3.2%)', '55.9% (±3.7%)'],
    'Should pick out the right column values');

// Plan with defined incumbency and a supporting model

var plan_array7 = plan.plan_array(NC_2019_incumbency);
assert.equal(plan_array7.length, 14, 'Should have a header with 13 districts');

assert.deepEqual(plan_array7[0],
    ['District', 'Incumbent Scenario', 'Pop. 2010', 'Pop. 2016',
    'Black Pop. 2016', 'Hispanic Pop. 2016',
    'Predicted Democratic Vote Share', 'Predicted Republican Vote Share'],
    'Should pick out the right column names');

assert.deepEqual(plan_array7[1],
    ['1', 'O', 730943, 738237.35, '46.3%', '8.7%', '72.2% (±4.3%)', '27.8% (±2.3%)'],
    'Should pick out the right column values');

assert.deepEqual(plan_array7[2],
    ['2', 'D', 734253, 824484.63, '21.3%', '9.7%', '50.8% (±3.0%)', '49.2% (±2.9%)'],
    'Should pick out the right column values');

assert.deepEqual(plan_array7[3],
    ['3', 'R', 732416, 708958.98, '23.2%', '7.9%', '44.1% (±3.2%)', '55.9% (±3.7%)'],
    'Should pick out the right column values');

// Plan with defined incumbency and a supporting model

var plan_array8 = plan.plan_array(NC_2020);
assert.equal(plan_array8.length, 14, 'Should have a header with 13 districts');

const headings8 = plan.get_plan_headings(NC_2020, undefined);
delete headings8.uploaded; // CI env won't have a matching TZ
delete headings8.date_only;
assert.deepEqual(headings8, {
    description: 'geometry.json (v8, with corrected incumbents)',
}, 'Should determine the right heading text');

assert.equal(plan.which_district_color(NC_2020.districts[0], NC_2020),
    '#4D90D1', 'Should return the blue district color for District 1');

assert.equal(plan.which_district_color(NC_2020.districts[1], NC_2020),
    '#838383', 'Should return the unknown district color for District 2');

assert.equal(plan.which_district_color(NC_2020.districts[2], NC_2020),
    '#D45557', 'Should return the red district color for District 3');

assert.equal(plan.which_district_color(NC_2020.districts[3], NC_2020),
    '#4D90D1', 'Should return the blue district color for District 4');

assert.equal(plan.which_district_color(NC_2020.districts[4], NC_2020),
    '#D45557', 'Should return the red district color for District 5');

assert.equal(plan.which_district_color(NC_2020.districts[5], NC_2020),
    '#B56E6A', 'Should return the reddish district color for District 6');

assert.equal(plan.which_district_color(NC_2020.districts[6], NC_2020),
    '#D45557', 'Should return the red district color for District 7');

assert.equal(plan.which_district_color(NC_2020.districts[7], NC_2020),
    '#D45557', 'Should return the red district color for District 8');

assert.equal(plan.which_district_color(NC_2020.districts[8], NC_2020),
    '#D45557', 'Should return the red district color for District 9');

assert.equal(plan.which_district_color(NC_2020.districts[9], NC_2020),
    '#D45557', 'Should return the red district color for District 10');

assert.equal(plan.which_district_color(NC_2020.districts[10], NC_2020),
    '#D45557', 'Should return the red district color for District 11');

assert.equal(plan.which_district_color(NC_2020.districts[11], NC_2020),
    '#4D90D1', 'Should return the blue district color for District 12');

assert.equal(plan.which_district_color(NC_2020.districts[12], NC_2020),
    '#D45557', 'Should return the red district color for District 13');

assert.equal(plan.get_seatshare_array(NC_2020), undefined, 'Should omit seat shares');

// Plan based on unified district model

var plan_array9 = plan.plan_array(NC_2020_unified);
assert.equal(plan_array9.length, 14, 'Should have a header with 13 districts');

const headings9 = plan.get_plan_headings(NC_2020_unified, undefined);
delete headings9.uploaded; // CI env won't have a matching TZ
delete headings9.date_only;

assert.deepEqual(headings9, {
    description: 'NC-plan-1-992.geojson (Oct 27: new form, new model, all open, with wins)',
}, 'Should determine the right heading text');

assert.equal(plan.which_district_color(NC_2020_unified.districts[0], NC_2020_unified),
    '#D45557', 'Should return the red district color for District 1');

assert.equal(plan.which_district_color(NC_2020_unified.districts[1], NC_2020_unified),
    '#D45557', 'Should return the red district color for District 2');

assert.equal(plan.which_district_color(NC_2020_unified.districts[2], NC_2020_unified),
    '#D45557', 'Should return the red district color for District 3');

assert.equal(plan.which_district_color(NC_2020_unified.districts[3], NC_2020_unified),
    '#B56E6B', 'Should return the lean-red district color for District 4');

assert.equal(plan.which_district_color(NC_2020_unified.districts[4], NC_2020_unified),
    '#4D90D1', 'Should return the blue district color for District 5');

assert.equal(plan.which_district_color(NC_2020_unified.districts[5], NC_2020_unified),
    '#4D90D1', 'Should return the blue district color for District 6');

assert.equal(plan.which_district_color(NC_2020_unified.districts[6], NC_2020_unified),
    '#6D8AB1', 'Should return the lean-blue district color for District 7');

assert.equal(plan.which_district_color(NC_2020_unified.districts[7], NC_2020_unified),
    '#6D8AB1', 'Should return the lean-blue district color for District 8');

assert.equal(plan.which_district_color(NC_2020_unified.districts[8], NC_2020_unified),
    '#4D90D1', 'Should return the blue district color for District 9');

assert.equal(plan.which_district_color(NC_2020_unified.districts[9], NC_2020_unified),
    '#B56E6B', 'Should return the lean-red district color for District 10');

assert.equal(plan.which_district_color(NC_2020_unified.districts[10], NC_2020_unified),
    '#D45557', 'Should return the red district color for District 11');

assert.equal(plan.which_district_color(NC_2020_unified.districts[11], NC_2020_unified),
    '#D45557', 'Should return the red district color for District 12');

assert.equal(plan.which_district_color(NC_2020_unified.districts[12], NC_2020_unified),
    '#6D8AB1', 'Should return the lean-blue district color for District 13');

var NC_2020_unified_seatshare = plan.get_seatshare_array(NC_2020_unified);

assert.equal(NC_2020_unified_seatshare.colors.length, 13, 'Should see the correct number of colors');

assert.equal(Math.round(NC_2020_unified_seatshare.red_votes), 2273424, 'Should see the correct number of red votes');
assert.equal(Math.round(NC_2020_unified_seatshare.blue_votes), 2181551, 'Should see the correct number of blue votes');
assert.equal(Math.round(NC_2020_unified_seatshare.seat_share*1000)/1000, 0.421, 'Should see the correct share of blue seats');

// Plan with defined all-zero vote swings

var plan_array10 = plan.plan_array(MS_zero_vote_swings);
assert.equal(plan_array10.length, 5, 'Should have a header with 4 districts');

assert.deepEqual(plan_array10[0],
    ['District', 'Incumbent Scenario', 'Pop. 2020', 'PlanScore:ShyColumn',
    'Hispanic CVAP 2023', 'Non-Hisp. Black CVAP 2023', 'Non-Hisp. Asian CVAP 2023',
    'Non-Hisp. Native CVAP 2023', 'Chance of 1+ Flips<sup>†</sup>', 'Chance of Democratic Win',
    'Predicted Vote Shares', 'Margin Swing', 'Harris (D) 2024', 'Trump (R) 2024', 'PlanScore:ShyColumn',
    'PlanScore:ShyColumn', 'PlanScore:ShyColumn', 'PlanScore:ShyColumn'],
    'Should pick out the right column names');

assert.equal(plan_array10[1].length, plan_array10[0].length);

// Plan with defined non-zero vote swings

var plan_array11 = plan.plan_array(MS_vote_swings);
assert.equal(plan_array11.length, 5, 'Should have a header with 4 districts');

assert.deepEqual(plan_array11[0],
    ['District', 'Incumbent Scenario', 'Pop. 2020', 'PlanScore:ShyColumn',
    'Hispanic CVAP 2023', 'Non-Hisp. Black CVAP 2023', 'Non-Hisp. Asian CVAP 2023',
    'Non-Hisp. Native CVAP 2023', 'Chance of 1+ Flips<sup>†</sup>', 'Chance of Democratic Win',
    'Predicted Vote Shares', 'Margin Swing', 'Harris (D) 2024', 'Trump (R) 2024',
    'PlanScore:ShyColumn', 'PlanScore:ShyColumn', 'PlanScore:ShyColumn', 'PlanScore:ShyColumn'],
    'Should pick out the right column names');

assert.equal(plan_array11[1].length, plan_array11[0].length);
assert.equal(plan_array11[1][10], '36% D / 64% R');
assert.equal(plan_array11[1][11], 'D+16');

assert.equal(plan_array11[2].length, plan_array11[0].length);
assert.equal(plan_array11[2][10], '68% D / 32% R');
assert.equal(plan_array11[2][11], 'D+10');

assert.equal(plan_array11[3].length, plan_array11[0].length);
assert.equal(plan_array11[3][10], '40% D / 60% R');
assert.equal(plan_array11[3][11], 'D+14');

assert.equal(plan_array11[4].length, plan_array11[0].length);
assert.equal(plan_array11[4][10], '33% D / 67% R');
assert.equal(plan_array11[4][11], 'D+16');

// Display preparation functions

var head1 = ['Democratic Votes', 'Republican Votes'];
plan.update_heading_titles(head1, undefined)
assert.deepEqual(head1, ['Predicted Democratic Vote Share', 'Predicted Republican Vote Share']);

var head2 = ['Citizen Voting-Age Population 2015', 'Asian Citizen Voting-Age Population 2015',
    'Black Citizen Voting-Age Population 2015', 'Hispanic Citizen Voting-Age Population 2015'];
plan.update_heading_titles(head2, undefined)
assert.deepEqual(head2, ['CVAP 2015', 'Non-Hisp. Asian CVAP 2015',
    'Non-Hisp. Black CVAP 2015', 'Hispanic CVAP 2015']);

var head3 = ['US President 2016 - DEM', 'US President 2016 - REP'];
plan.update_heading_titles(head3, undefined)
assert.deepEqual(head3, ['Clinton (D) 2016', 'Trump (R) 2016']);

var head4 = ['Democratic Wins'];
plan.update_heading_titles(head4, undefined)
assert.deepEqual(head4, ['Chance of Democratic Win']);

var head5 = ['Democratic Wins', 'Democratic Votes', 'Republican Votes'];
plan.update_heading_titles(head5, undefined)
assert.deepEqual(head5, ['Chance of Democratic Win', 'Predicted Vote Shares']);

var head6 = ['Population 2016', 'Black Population 2016', 'Hispanic Population 2016']
plan.update_heading_titles(head6, undefined)
assert.deepEqual(head6, ['Pop. 2016', 'Black Pop. 2016', 'Hispanic Pop. 2016']);

var head7 = ['US President 2020 - DEM', 'US President 2020 - REP']
plan.update_heading_titles(head7, undefined)
assert.deepEqual(head7, ['Biden (D) 2020', 'Trump (R) 2020']);

var head8 = ['US President 2016 - DEM', 'US President 2016 - REP', 'US President 2020 - DEM', 'US President 2020 - REP']
plan.update_heading_titles(head8, undefined)
assert.deepEqual(head8, [plan.SHY_COLUMN, plan.SHY_COLUMN, 'Biden (D) 2020', 'Trump (R) 2020']);

var head9 = ['US President 2024 - DEM', 'US President 2024 - REP']
plan.update_heading_titles(head9, undefined)
assert.deepEqual(head9, ['Harris (D) 2024', 'Trump (R) 2024']);

var head10 = ['US President 2020 - DEM', 'US President 2020 - REP', 'US President 2024 - DEM', 'US President 2024 - REP']
plan.update_heading_titles(head10, undefined)
assert.deepEqual(head10, [plan.SHY_COLUMN, plan.SHY_COLUMN, 'Harris (D) 2024', 'Trump (R) 2024']);

var head11 = ['US President 2016 - DEM', 'US President 2016 - REP', 'US President 2020 - DEM', 'US President 2020 - REP', 'US President 2024 - DEM', 'US President 2024 - REP']
plan.update_heading_titles(head11, 2020)
assert.deepEqual(head11, [plan.SHY_COLUMN, plan.SHY_COLUMN, 'Biden (D) 2020', 'Trump (R) 2020', plan.SHY_COLUMN, plan.SHY_COLUMN]);

var row1 = [4, 6];
plan.update_vote_percentages(['Democratic Votes', 'Republican Votes'], row1, {});
assert.deepEqual(row1, ['40.0%', '60.0%']);

var row2 = [4, 6];
plan.update_vote_percentages(['Democratic Votes', 'Republican Smokes'], row2, {});
assert.deepEqual(row2, [4, 6]);

var row3 = [4, 6];
plan.update_vote_percentages(['Democratic Jokes', 'Republican Votes'], row3, {});
assert.deepEqual(row3, [4, 6]);

var row4 = [10, 4, 6];
plan.update_acs2015_percentages(['Population 2015', 'Black Population 2015', 'Hispanic Population 2015'], row4);
assert.deepEqual(row4, [10, '40.0%', '60.0%']);

var row5 = [10, 4, 6];
plan.update_acs2015_percentages(['Population 2015', 'Black Population 1999', 'Hispanic Population 2015'], row5);
assert.deepEqual(row5, [10, 4, 6]);

var row6 = [10, 4, 6];
plan.update_acs2015_percentages(['Population 2015', 'Black Population 2015', 'No Population 2015'], row6);
assert.deepEqual(row6, [10, 4, 6]);

var row7 = [10, 4, 6];
plan.update_acs2015_percentages(['Population 2010', 'Black Population 2015', 'Hispanic Population 2015'], row7);
assert.deepEqual(row7, [10, 4, 6]);

var row8 = [10, 4, 6];
plan.update_cvap2015_percentages(['Citizen Voting-Age Population 2015',
    'Black Citizen Voting-Age Population 2015', 'Hispanic Citizen Voting-Age Population 2015'], row8);
assert.deepEqual(row8, [10, '40.0%', '60.0%']);

var row9 = [10, 4, 6];
plan.update_cvap2015_percentages(['Citizen Voting-Age Population 2015',
    'Black Population 1999', 'Hispanic Citizen Voting-Age Population 2015'], row9);
assert.deepEqual(row9, [10, 4, 6]);

var row10 = [10, 4, 6];
plan.update_cvap2015_percentages(['Citizen Voting-Age Population 2015',
    'Black Citizen Voting-Age Population 2015', 'No Population 2015'], row10);
assert.deepEqual(row10, [10, 4, 6]);

var row11 = [10, 4, 6];
plan.update_cvap2015_percentages(['Population 2010',
    'Black Citizen Voting-Age Population 2015', 'Hispanic Citizen Voting-Age Population 2015'], row11);
assert.deepEqual(row11, [10, 4, 6]);

var row12 = [10, 4, 6];
plan.update_acs2016_percentages(['Population 2016', 'Black Population 2016', 'Hispanic Population 2016'], row12);
assert.deepEqual(row12, [10, '40.0%', '60.0%']);

var row13 = [10, 4, 6];
plan.update_acs2016_percentages(['Population 2016', 'Black Population 1999', 'Hispanic Population 2016'], row13);
assert.deepEqual(row13, [10, 4, 6]);

var row14 = [10, 4, 6];
plan.update_acs2016_percentages(['Population 2016', 'Black Population 2016', 'No Population 2016'], row14);
assert.deepEqual(row14, [10, 4, 6]);

var row15 = [10, 4, 6];
plan.update_acs2016_percentages(['Population 2010', 'Black Population 2016', 'Hispanic Population 2016'], row15);
assert.deepEqual(row15, [10, 4, 6]);

var row16 = [4, 6];
plan.update_vote_percentages(['Democratic Votes', 'Republican Votes'], row16,
    {'Democratic Votes SD': 1, 'Republican Votes SD': 1});
assert.deepEqual(row16, ['40.0% (±20.0%)', '60.0% (±20.0%)']);

var row17 = [4, 6];
plan.update_vote_percentages(['Democratic Votes', 'Republican Votes'], row17,
    {'Democratic Votes SD': 0, 'Republican Votes SD': 0});
assert.deepEqual(row17, ['40.0% (±0.0%)', '60.0% (±0.0%)']);

var row18 = [4, 6];
plan.update_vote_percentages(['Democratic Votes', 'Republican Votes'], row18,
    {'Democratic Votes SD': 'no', 'Republican Votes SD': 'no'});
assert.deepEqual(row18, ['40.0%', '60.0%']);

var row19 = [.3149];
plan.update_vote_percentages(['Democratic Wins'], row19, {});
assert.deepEqual(row19, ['31%']);

var row20 = [.3142, .6180, .3820];
plan.update_vote_percentages(['Democratic Wins', 'Democratic Votes', 'Republican Votes'], row20, {});
assert.deepEqual(row20, ['31%', '62% D / 38% R']);

// Assorted functions

assert(plan.date_age(new Date('1970-01-01')) > 86400 * 365);
assert(plan.date_age(new Date('2017-10-01')) < 86400 * 365 * 10);
assert(plan.date_age(new Date()) < 1);
assert(annotate_new.date_age(new Date('1970-01-01')) > 86400 * 365);
assert(annotate_new.date_age(new Date('2017-10-01')) < 86400 * 365 * 10);
assert(annotate_new.date_age(new Date()) < 1);

assert.equal(plan.nice_count(7654321), '7,654,321', 'Should have a thousands separator');
assert.equal(plan.nice_count(654321), '654,321', 'Should have a thousands separator');
assert.equal(plan.nice_count(54321), '54,321', 'Should have a thousands separator');
assert.equal(plan.nice_count(4321), '4,321', 'Should have a thousands separator');
assert.equal(plan.nice_count(321), '321', 'Should see a literal integer');
assert.equal(plan.nice_count(21), '21.0', 'Should see one decimal place');
assert.equal(plan.nice_count(1), '1.00', 'Should see two decimal places');
assert.equal(plan.nice_count(-1), '–', 'Should not see a negative number');

assert.equal(plan.nice_percent(1), '100.0%', 'Should see one decimal place');
assert.equal(plan.nice_percent(.1), '10.0%', 'Should see one decimal place');
assert.equal(plan.nice_percent(.01), '1.0%', 'Should see one decimal place');
assert.equal(plan.nice_percent(.001), '0.1%', 'Should see one decimal place');
assert.equal(plan.nice_round_percent(.989), '99%', 'Should see no decimal places');
assert.equal(plan.nice_round_percent(.011), '1%', 'Should see no decimal places');
assert.equal(plan.nice_round_percent(.009), '<1%', 'Should see no decimal places and not-quite zero value');
assert.equal(plan.nice_round_percent(0.00), '<1%', 'Should see no decimal places and not-quite zero value');
assert.equal(plan.nice_round_percent(.991), '>99%', 'Should see no decimal places and not-quite zero value');
assert.equal(plan.nice_round_percent(1.00), '>99%', 'Should see no decimal places and not-quite zero value');

assert.equal(plan.nice_gap(.1), '+10.0% for Democrats', 'Positive gaps should be blue');
assert.equal(plan.nice_gap(-.1), '+10.0% for Republicans', 'Negative gaps should be red');

assert.equal(plan.nice_string('yo'), '&#121;&#111;');

assert.equal(plan.nice_margin_swing(-0.101 / 2), 'R+10');
assert.equal(plan.nice_margin_swing(-0.1 / 2), 'R+10');
assert.equal(plan.nice_margin_swing(-0.095 / 2), 'R+9.5');
assert.equal(plan.nice_margin_swing(-0.015 / 2), 'R+1.5');
assert.equal(plan.nice_margin_swing(0.0 / 2), '–');
assert.equal(plan.nice_margin_swing(0.101 / 2), 'D+10');
assert.equal(plan.nice_margin_swing(0.1 / 2), 'D+10');
assert.equal(plan.nice_margin_swing(0.095 / 2), 'D+9.5');
assert.equal(plan.nice_margin_swing(0.015 / 2), 'D+1.5');

assert.equal(plan.partisan_suffix(0), '');
assert.equal(plan.partisan_suffix(1), '&nbsp;D');
assert.equal(plan.partisan_suffix(-1), '&nbsp;R');

// Test swing_vote helper function
var swung1 = plan.swing_vote([1, 2, 3], [3, 2, 1], 0);
assert.equal(swung1[0][0], 1, 'Zero swing should not change red votes');
assert.equal(swung1[1][0], 3, 'Zero swing should not change blue votes');

var swung2 = plan.swing_vote([1, 2, 3], [3, 2, 1], 0.1);
assert.equal(Math.round(swung2[0][0] * 10) / 10, 0.6, 'Positive swing should decrease red votes');
assert.equal(Math.round(swung2[1][0] * 10) / 10, 3.4, 'Positive swing should increase blue votes');

var swung3 = plan.swing_vote([1, 2, 3], [3, 2, 1], -0.1);
assert.equal(Math.round(swung3[0][0] * 10) / 10, 1.4, 'Negative swing should increase red votes');
assert.equal(Math.round(swung3[1][0] * 10) / 10, 2.6, 'Negative swing should decrease blue votes');

// Test calculate_EG with fair election
var gap1 = plan.calculate_EG([2, 3, 5, 6], [6, 5, 3, 2]);
assert.equal(Math.round(gap1 * 1000) / 1000, 0, 'Should see zero EG for fair election');

var gap2 = plan.calculate_EG([2, 3, 5, 6, 0], [6, 5, 3, 2, 0]);
assert.equal(Math.round(gap2 * 1000) / 1000, 0, 'Should see zero EG with one district missing votes');

// Test calculate_EG with unfair election
var gap3 = plan.calculate_EG([1, 5, 5, 5], [7, 3, 3, 3]);
assert.equal(Math.round(gap3 * 100) / 100, -0.25, 'Should see -0.25 EG for unfair election');

// Test calculate_MMD with various scenarios
var mmd1 = plan.calculate_MMD([6, 6, 4, 4, 4], [5, 5, 5, 8, 8]);
assert.equal(Math.round(mmd1 * 100) / 100, 0, 'Should see zero MMD with 44% mean and median');

var mmd2 = plan.calculate_MMD([6, 6, 6, 6, 6], [4, 4, 4, 4, 4]);
assert.equal(Math.round(mmd2 * 100) / 100, 0, 'Should see zero MMD with 60% mean and median');

var mmd3 = plan.calculate_MMD([6, 6, 6, 1, 1], [5, 5, 5, 10, 10]);
assert.equal(Math.round(mmd3 * 100) / 100, -0.18, 'Should see -0.18 MMD with red bias');

var mmd4 = plan.calculate_MMD([6, 6, 6, 6, 1], [5, 5, 5, 5, 10]);
assert.equal(Math.round(mmd4 * 100) / 100, -0.09, 'Should see -0.09 MMD with red bias');

var mmd5 = plan.calculate_MMD([6, 6, 1, 1, 1], [5, 5, 7, 10, 10]);
assert.equal(Math.round(mmd5 * 100) / 100, 0.15, 'Should see +0.15 MMD with blue bias');

var mmd6 = plan.calculate_MMD([6, 6, 4, 4, 4, 0], [5, 5, 5, 8, 8, 0]);
assert.equal(Math.round(mmd6 * 100) / 100, 0, 'Should see defined MMD with one district missing votes');

// Test calculate_PB with various scenarios
var pb1 = plan.calculate_PB([6, 6, 4, 4], [4, 4, 6, 6]);
assert.equal(Math.round(pb1 * 100) / 100, 0, 'Should see zero PB with 50/50 election');

var pb2 = plan.calculate_PB([6, 6, 6, 3, 3], [2, 2, 2, 5, 5]);
assert.equal(Math.round(pb2 * 100) / 100, -0.1, 'Should see -0.1 PB with red bias');

var pb3 = plan.calculate_PB([6, 6, 6, 3, 3], [4, 4, 4, 12, 12]);
assert.equal(Math.round(pb3 * 100) / 100, -0.1, 'Should see -0.1 PB with red advantage');

var pb4 = plan.calculate_PB([4, 4, 4, 12, 12], [6, 6, 6, 3, 3]);
assert.equal(Math.round(pb4 * 100) / 100, 0.1, 'Should see +0.1 PB with blue advantage');

var pb5 = plan.calculate_PB([6, 6, 4, 4, 0], [4, 4, 6, 6, 0]);
assert.equal(Math.round(pb5 * 100) / 100, 0, 'Should see zero PB with one district missing votes');

// Test calculate_D2 with various scenarios
// Georgia 1972: 9 blue wins, 1 red win
var d2a_reds = [];
var d2a_blues = [];
for (var i = 0; i < 9; i++) {
    d2a_reds.push(1 - 0.584617612075026);
    d2a_blues.push(0.584617612075026);
}
d2a_reds.push(1 - 0.240871024240908);
d2a_blues.push(0.240871024240908);
var d2a = plan.calculate_D2(d2a_reds, d2a_blues);
assert.equal(Math.round(d2a * 1000) / 1000, 0.875, 'Should see high D2 in Georgia 1972');

// Louisiana 2020: 1 blue win, 5 red wins
var d2b_reds = [1 - 0.809097511747074];
var d2b_blues = [0.809097511747074];
for (var i = 0; i < 5; i++) {
    d2b_reds.push(1 - 0.27072066577579);
    d2b_blues.push(0.27072066577579);
}
var d2b = plan.calculate_D2(d2b_reds, d2b_blues);
assert.equal(Math.round(d2b * 1000) / 1000, -0.459, 'Should see low D2 in Louisiana 2020');

// North Carolina 1998: 5 blue wins, 7 red wins
var d2c_reds = [];
var d2c_blues = [];
for (var i = 0; i < 5; i++) {
    d2c_reds.push(1 - 0.598085862963535);
    d2c_blues.push(0.598085862963535);
}
for (var i = 0; i < 7; i++) {
    d2c_reds.push(1 - 0.357068466446836);
    d2c_blues.push(0.357068466446836);
}
var d2c = plan.calculate_D2(d2c_reds, d2c_blues);
assert.equal(Math.round(d2c * 1000) / 1000, 0.012, 'Should see near-zero D2 in North Carolina 1998');

var d2d = plan.calculate_D2([1, 2, 3, 4, 0], [4, 3, 2, 1, 0]);
assert.equal(Math.round(d2d * 1000) / 1000, 0, 'Should see zero D2 for balanced election');

var d2f = plan.calculate_D2([3, 4, 5], [2, 1, 0]);
assert.equal(Math.round(d2f * 1000) / 1000, -0.549, 'Should see low D2 when red wins all districts');

var d2g = plan.calculate_D2([2, 1, 0], [3, 4, 5]);
assert.equal(Math.round(d2g * 1000) / 1000, 0.549, 'Should see high D2 when blue wins all districts');

var CT_2021_water_seatshare = plan.get_seatshare_array(CT_2021_water_district);

assert.equal(CT_2021_water_seatshare.colors.length, 5, 'Should see the correct number of colors');
assert.equal(Math.round(CT_2021_water_seatshare.red_votes), 682129, 'Should see the correct number of red votes');
assert.equal(Math.round(CT_2021_water_seatshare.blue_votes), 814115, 'Should see the correct number of blue votes');
assert.equal(Math.round(CT_2021_water_seatshare.seat_share*1000)/1000, 0.747, 'Should see the correct share of blue seats');

// Annotate page

assert.equal(annotate_new.format_url('https://example.com/{id}.html', 'xyz'),
    'https://example.com/xyz.html', 'URL should format correctly');

var search = ("?bucket=planscore"
    + "&key=uploads%2F20191229T183809.446949066Z%2Fupload%2Fnull-plan.gpkg"
    + "&id=20191229T183809.446949066Z.zapI6N-eiLykEsa1QVj2TrmldZk");

assert.equal(annotate_new.getUrlParameter('bucket', search),
    'planscore', 'Should get correct URL bucket');

assert.equal(annotate_new.getUrlParameter('key', search),
    'uploads/20191229T183809.446949066Z/upload/null-plan.gpkg', 'Should get correct URL key');

assert.equal(annotate_new.getUrlParameter('id', search),
    '20191229T183809.446949066Z.zapI6N-eiLykEsa1QVj2TrmldZk', 'Should get correct URL id');

assert.equal(annotate_new.which_plan_districts_count({districts: 'no'}),
    null, 'Should return no defined count');

assert.equal(annotate_new.which_plan_districts_count(NC_2019_preread_start),
    0, 'Should return correct district count');

assert.equal(annotate_new.which_plan_districts_count(NC_2019_preread_end),
    13, 'Should return correct district count');

assert.equal(annotate_new.get_description(NC_2019_preread_end, undefined),
    'North Carolina U.S. House plan uploaded on 12/28/2019');

console.log('Tests pass.', new Date().toLocaleString());

// Adjust scenario statistics

assert.notEqual(NC_2025_scenarios.statistics['Democratic Votes'][1][1][1], 252495.57);
assert.notEqual(NC_2025_scenarios.statistics['Democratic Votes SD'][1][1][1], 12911.24);
assert.notEqual(NC_2025_scenarios.statistics['Democratic Wins'][1][1][1], 1);
assert.notEqual(NC_2025_scenarios.statistics['Republican Votes'][1][1][1], 148173.07);
assert.notEqual(NC_2025_scenarios.statistics['Republican Votes SD'][1][1][1], 12911.24);

plan.adjust_scenario_stats(NC_2025_scenarios);
plan.adjust_scenario_stats(NC_2025_incumbents_scenarios);

assert.equal(NC_2025_scenarios.statistics['Democratic Votes'][1][1][1], 252495.57);
assert.equal(NC_2025_scenarios.statistics['Democratic Votes SD'][1][1][1], 12911.24);
assert.equal(NC_2025_scenarios.statistics['Democratic Wins'][1][1][1], 1);
assert.equal(NC_2025_scenarios.statistics['Republican Votes'][1][1][1], 148173.07);
assert.equal(NC_2025_scenarios.statistics['Republican Votes SD'][1][1][1], 12911.24);

// Test create_scenario_plan

// Test: vote_swing 0.0 with unchanged incumbents should return a mutated plan with sensitivity properties
var result_zero = plan.create_scenario_plan(NC_2025_index, NC_2025_scenarios, 0.0, NC_2025_index.incumbents.slice());
assert.notStrictEqual(result_zero, NC_2025_index, 'Should return a new object even for 0.0 swing (to add sensitivity properties)');
assert.ok(typeof result_zero.summary['Efficiency Gap 0 Swing'] === 'number', 'Should have sensitivity properties even at 0.0 swing');

// Test: vote_swing -6.0 should mutate the plan
var result_neg6 = plan.create_scenario_plan(NC_2025_index, NC_2025_scenarios, -6.0, NC_2025_index.incumbents.slice());
assert.notStrictEqual(result_neg6, NC_2025_index, 'Should return a different object for non-zero swing');

// Verify that the first district (index 0) gets data from the correct incumbent scenario
var district_0_incumbent = NC_2025_index.incumbents[0];
var district_0_incumbent_index = 3; // hard code the entirely-open option
assert.equal(result_neg6.districts[0].totals['Democratic Votes'],
    NC_2025_scenarios.statistics['Democratic Votes'][0][district_0_incumbent_index][0],
    'Should update Democratic Votes for district 0 with correct incumbent');
assert.equal(result_neg6.districts[0].totals['Republican Votes'],
    NC_2025_scenarios.statistics['Republican Votes'][0][district_0_incumbent_index][0],
    'Should update Republican Votes for district 0 with correct incumbent');

// Verify second district (index 1)
var district_1_incumbent = NC_2025_index.incumbents[1];
var district_1_incumbent_index = 3; // hard code the entirely-open option
assert.equal(result_neg6.districts[1].totals['Democratic Votes'],
    NC_2025_scenarios.statistics['Democratic Votes'][0][district_1_incumbent_index][1],
    'Should update Democratic Votes for district 1 with correct incumbent');
assert.equal(result_neg6.districts[1].totals['Republican Votes'],
    NC_2025_scenarios.statistics['Republican Votes'][0][district_1_incumbent_index][1],
    'Should update Republican Votes for district 1 with correct incumbent');

// Test: vote_swing +6.0 should use different scenario data
var result_pos6 = plan.create_scenario_plan(NC_2025_index, NC_2025_scenarios, 6.0, NC_2025_index.incumbents.slice());
assert.equal(result_pos6.districts[0].totals['Democratic Votes'],
    NC_2025_scenarios.statistics['Democratic Votes'][24][district_0_incumbent_index][0],
    'Should update Democratic Votes for +6.0 swing');
assert.equal(result_pos6.districts[0].totals['Republican Votes'],
    NC_2025_scenarios.statistics['Republican Votes'][24][district_0_incumbent_index][0],
    'Should update Republican Votes for +6.0 swing');

// Test helper functions
// Test calculate_mean
var mean1 = plan.calculate_mean([1, 2, 3, 4, 5]);
assert.equal(mean1, 3, 'Mean of [1,2,3,4,5] should be 3');

var mean2 = plan.calculate_mean([10, 20, 30]);
assert.equal(Math.round(mean2 * 100) / 100, 20, 'Mean of [10,20,30] should be 20');

var mean3 = plan.calculate_mean([]);
assert.strictEqual(mean3, null, 'Mean of empty array should be null');

// Test calculate_stdev
var stdev1 = plan.calculate_stdev([2, 4, 4, 4, 5, 5, 7, 9]);
assert.equal(Math.round(stdev1 * 100) / 100, 2.14, 'Stdev should be approximately 2.14');

var stdev2 = plan.calculate_stdev([1, 2, 3, 4, 5]);
assert.equal(Math.round(stdev2 * 100) / 100, 1.58, 'Stdev should be approximately 1.58');

var stdev3 = plan.calculate_stdev([5]);
assert.strictEqual(stdev3, null, 'Stdev of single element should be null');

var stdev4 = plan.calculate_stdev([]);
assert.strictEqual(stdev4, null, 'Stdev of empty array should be null');

// Test calculate_positives
var pos1 = plan.calculate_positives([1, 2, 3, 4, 5]);
assert.equal(pos1, 1.0, 'All positive values should give 1.0');

var pos2 = plan.calculate_positives([-1, -2, -3, -4, -5]);
assert.equal(pos2, 0.0, 'All negative values should give 0.0');

var pos3 = plan.calculate_positives([-2, -1, 0, 1, 2]);
assert.equal(pos3, 0.4, 'Half positive should give 0.4 (2/5)');

var pos4 = plan.calculate_positives([0.001, -0.001]);
assert.equal(pos4, 0.5, 'Values near epsilon should be handled correctly');

var pos5 = plan.calculate_positives([]);
assert.strictEqual(pos5, null, 'Positives of empty array should be null');

// Test percentrank_abs function
// With values [-0.15, -0.10, -0.05, 0.00, 0.05, 0.10, 0.15] (7 values)
// Testing with 0.12: abs values are [0.15, 0.10, 0.05, 0.00, 0.05, 0.10, 0.15]
// Values with abs < 0.12: 0.10, 0.05, 0.00, 0.05, 0.10 = 5 values
// Percentrank = 5/7 = 0.714...
var prank_abs1 = plan.percentrank_abs('eg_adj_avg', 'ushouse', 0.12);
assert.equal(Math.round(prank_abs1 * 1000) / 1000, 0.714, 'Should calculate correct absolute percentrank for 0.12');

// Testing with -0.08: abs value is 0.08
// Values with abs < 0.08: 0.05, 0.00, 0.05 = 3 values
// Percentrank = 3/7 = 0.428...
var prank_abs2 = plan.percentrank_abs('eg_adj_avg', 'ushouse', -0.08);
assert.equal(Math.round(prank_abs2 * 1000) / 1000, 0.429, 'Should calculate correct absolute percentrank for -0.08');

// Testing with 0.00: abs value is 0.00
// Values with abs < 0.00: none = 0 values
// Percentrank = 0/7 = 0
var prank_abs3 = plan.percentrank_abs('eg_adj_avg', 'ushouse', 0.00);
assert.equal(prank_abs3, 0, 'Should return 0 percentrank for minimum absolute value');

// Test with localplan (should return null)
var prank_abs4 = plan.percentrank_abs('eg_adj_avg', 'localplan', 0.10);
assert.strictEqual(prank_abs4, null, 'Should return null for localplan');

// Test percentrank_rel function - matches server implementation in score.py
// With values [-0.15, -0.10, -0.05, 0.00, 0.05, 0.10, 0.15] (7 values)
// Testing with 0.12 (positive, favors D): count where 0.12 > historical = 6 values (all except 0.15)
// Percentrank = 6/7 = 0.857...
var prank_rel1 = plan.percentrank_rel('eg_adj_avg', 'ushouse', 0.12);
assert.equal(Math.round(prank_rel1 * 1000) / 1000, 0.857, 'Should calculate correct relative percentrank for 0.12');

// Testing with -0.12 (negative, favors R): count where -0.12 < historical = 6 values (all except -0.15)
// Percentrank = 6/7 = 0.857...
var prank_rel2 = plan.percentrank_rel('eg_adj_avg', 'ushouse', -0.12);
assert.equal(Math.round(prank_rel2 * 1000) / 1000, 0.857, 'Should calculate correct relative percentrank for -0.12');

// Testing with 0.00: count where 0.00 > historical = 3 values (-0.15, -0.10, -0.05)
// Percentrank = 3/7 = 0.428...
var prank_rel3 = plan.percentrank_rel('eg_adj_avg', 'ushouse', 0.00);
assert.equal(Math.round(prank_rel3 * 1000) / 1000, 0.429, 'Should calculate correct relative percentrank for 0.00');

// Testing with 0.05: count where 0.05 > historical = 4 values (all negatives + 0.00)
// Percentrank = 4/7 = 0.571...
var prank_rel4 = plan.percentrank_rel('eg_adj_avg', 'ushouse', 0.05);
assert.equal(Math.round(prank_rel4 * 1000) / 1000, 0.571, 'Should calculate correct relative percentrank for 0.05');

// Test with localplan (should return null)
var prank_rel5 = plan.percentrank_rel('eg_adj_avg', 'localplan', 0.10);
assert.strictEqual(prank_rel5, null, 'Should return null for localplan');

// Test that create_scenario_plan generates valid summary statistics
var result_sim = plan.create_scenario_plan(NC_2025_index, NC_2025_scenarios, -6.0, NC_2025_index.incumbents.slice());

// Check that all required summary statistics are present
assert.ok(typeof result_sim.summary['Efficiency Gap'] === 'number', 'Should have Efficiency Gap mean');
assert.ok(typeof result_sim.summary['Efficiency Gap SD'] === 'number', 'Should have Efficiency Gap SD');
assert.ok(typeof result_sim.summary['Efficiency Gap Positives'] === 'number', 'Should have Efficiency Gap Positives');
assert.ok(typeof result_sim.summary['Efficiency Gap Absolute Percent Rank'] === 'number', 'Should have Efficiency Gap Absolute Percent Rank as number');
assert.ok(typeof result_sim.summary['Efficiency Gap Relative Percent Rank'] === 'number', 'Should have Efficiency Gap Relative Percent Rank as number');

assert.ok(typeof result_sim.summary['Mean-Median'] === 'number', 'Should have Mean-Median mean');
assert.ok(typeof result_sim.summary['Mean-Median SD'] === 'number', 'Should have Mean-Median SD');
assert.ok(typeof result_sim.summary['Mean-Median Positives'] === 'number', 'Should have Mean-Median Positives');
assert.ok(typeof result_sim.summary['Mean-Median Absolute Percent Rank'] === 'number', 'Should have Mean-Median Absolute Percent Rank as number');
assert.ok(typeof result_sim.summary['Mean-Median Relative Percent Rank'] === 'number', 'Should have Mean-Median Relative Percent Rank as number');

assert.ok(typeof result_sim.summary['Partisan Bias'] === 'number', 'Should have Partisan Bias mean');
assert.ok(typeof result_sim.summary['Partisan Bias SD'] === 'number', 'Should have Partisan Bias SD');
assert.ok(typeof result_sim.summary['Partisan Bias Positives'] === 'number', 'Should have Partisan Bias Positives');
assert.ok(typeof result_sim.summary['Partisan Bias Absolute Percent Rank'] === 'number', 'Should have Partisan Bias Absolute Percent Rank as number');
assert.ok(typeof result_sim.summary['Partisan Bias Relative Percent Rank'] === 'number', 'Should have Partisan Bias Relative Percent Rank as number');

assert.ok(typeof result_sim.summary['Declination'] === 'number', 'Should have Declination mean');
assert.ok(typeof result_sim.summary['Declination SD'] === 'number', 'Should have Declination SD');
assert.ok(typeof result_sim.summary['Declination Positives'] === 'number', 'Should have Declination Positives');
assert.ok(typeof result_sim.summary['Declination Absolute Percent Rank'] === 'number', 'Should have Declination Absolute Percent Rank as number');
assert.ok(typeof result_sim.summary['Declination Relative Percent Rank'] === 'number', 'Should have Declination Relative Percent Rank as number');

// Verify that percentrank values are between 0 and 1
assert.ok(result_sim.summary['Efficiency Gap Absolute Percent Rank'] >= 0 && result_sim.summary['Efficiency Gap Absolute Percent Rank'] <= 1,
    'Efficiency Gap Absolute Percent Rank should be between 0 and 1');
assert.ok(result_sim.summary['Efficiency Gap Relative Percent Rank'] >= 0 && result_sim.summary['Efficiency Gap Relative Percent Rank'] <= 1,
    'Efficiency Gap Relative Percent Rank should be between 0 and 1');

// Test that positives are between 0 and 1
assert.ok(result_sim.summary['Efficiency Gap Positives'] >= 0 && result_sim.summary['Efficiency Gap Positives'] <= 1,
    'Efficiency Gap Positives should be between 0 and 1');
assert.ok(result_sim.summary['Mean-Median Positives'] >= 0 && result_sim.summary['Mean-Median Positives'] <= 1,
    'Mean-Median Positives should be between 0 and 1');
assert.ok(result_sim.summary['Partisan Bias Positives'] >= 0 && result_sim.summary['Partisan Bias Positives'] <= 1,
    'Partisan Bias Positives should be between 0 and 1');
assert.ok(result_sim.summary['Declination Positives'] >= 0 && result_sim.summary['Declination Positives'] <= 1,
    'Declination Positives should be between 0 and 1');

// Test that SD values are positive
assert.ok(result_sim.summary['Efficiency Gap SD'] > 0, 'Efficiency Gap SD should be positive');
assert.ok(result_sim.summary['Mean-Median SD'] > 0, 'Mean-Median SD should be positive');
assert.ok(result_sim.summary['Partisan Bias SD'] > 0, 'Partisan Bias SD should be positive');
assert.ok(result_sim.summary['Declination SD'] > 0, 'Declination SD should be positive');

// Test sensitivity sweep properties using incumbents plan (avoids early-return optimization)
var result_with_sens = plan.create_scenario_plan(
    NC_2025_incumbents_index,
    NC_2025_incumbents_scenarios,
    0.0,
    NC_2025_incumbents_index.incumbents.slice()
);
assert.ok(typeof result_with_sens.summary['Efficiency Gap 0 Swing'] === 'number', 'Should have Efficiency Gap 0 Swing');
assert.ok(typeof result_with_sens.summary['Efficiency Gap +5 Dem'] === 'number', 'Should have Efficiency Gap +5 Dem');
assert.ok(typeof result_with_sens.summary['Efficiency Gap +4 Dem'] === 'number', 'Should have Efficiency Gap +4 Dem');
assert.ok(typeof result_with_sens.summary['Efficiency Gap +3 Dem'] === 'number', 'Should have Efficiency Gap +3 Dem');
assert.ok(typeof result_with_sens.summary['Efficiency Gap +2 Dem'] === 'number', 'Should have Efficiency Gap +2 Dem');
assert.ok(typeof result_with_sens.summary['Efficiency Gap +1 Dem'] === 'number', 'Should have Efficiency Gap +1 Dem');
assert.ok(typeof result_with_sens.summary['Efficiency Gap +1 Rep'] === 'number', 'Should have Efficiency Gap +1 Rep');
assert.ok(typeof result_with_sens.summary['Efficiency Gap +2 Rep'] === 'number', 'Should have Efficiency Gap +2 Rep');
assert.ok(typeof result_with_sens.summary['Efficiency Gap +3 Rep'] === 'number', 'Should have Efficiency Gap +3 Rep');
assert.ok(typeof result_with_sens.summary['Efficiency Gap +4 Rep'] === 'number', 'Should have Efficiency Gap +4 Rep');
assert.ok(typeof result_with_sens.summary['Efficiency Gap +5 Rep'] === 'number', 'Should have Efficiency Gap +5 Rep');

// Test that Efficiency Gap 0 Swing is independent of the vote_swing parameter
// Use NC_2025_incumbents which has mixed D/R/O incumbents (not all 'U')
var result_swing_0 = plan.create_scenario_plan(
    NC_2025_incumbents_index,
    NC_2025_incumbents_scenarios,
    0.0,
    NC_2025_incumbents_index.incumbents.slice()
);
var result_swing_3 = plan.create_scenario_plan(
    NC_2025_incumbents_index,
    NC_2025_incumbents_scenarios,
    3.0,
    NC_2025_incumbents_index.incumbents.slice()
);
assert.equal(
    result_swing_0.summary['Efficiency Gap 0 Swing'],
    result_swing_3.summary['Efficiency Gap 0 Swing'],
    'Efficiency Gap 0 Swing should be the same regardless of vote_swing parameter'
);
// But regular Efficiency Gap should be different
assert.notEqual(
    result_swing_0.summary['Efficiency Gap'],
    result_swing_3.summary['Efficiency Gap'],
    'Regular Efficiency Gap should change with vote_swing parameter'
);

// Test incumbency scenario functionality with NC 2025 incumbents plan
// Plan has 14 districts with mixed incumbents (not all open)

// Test that changing incumbents changes the results
var result_original_inc = plan.create_scenario_plan(
    NC_2025_incumbents_index,
    NC_2025_incumbents_scenarios,
    0.0,
    NC_2025_incumbents_index.incumbents.slice()
);

// Create alternate incumbents (flip all to opposite party where applicable)
var alternate_incumbents = NC_2025_incumbents_index.incumbents.map(function(inc) {
    if (inc === 'D') return 'R';
    if (inc === 'R') return 'D';
    return inc;
});

var result_alternate_inc = plan.create_scenario_plan(
    NC_2025_incumbents_index,
    NC_2025_incumbents_scenarios,
    0.0,
    alternate_incumbents
);

// Verify that changing incumbents produces different results
assert.notEqual(
    result_original_inc.districts[1].totals['Democratic Votes'],
    result_alternate_inc.districts[1].totals['Democratic Votes'],
    'Different incumbents should produce different Democratic vote totals'
);

// Verify that the mutated plan has the correct incumbents
assert.deepEqual(result_original_inc.incumbents, NC_2025_incumbents_index.incumbents,
    'Result plan should have original incumbents');
assert.deepEqual(result_alternate_inc.incumbents, alternate_incumbents,
    'Result plan should have alternate incumbents');

// Test that vote_swing field is calculated relative to baseline with same incumbents
// This ensures that changing incumbents alone (with 0.0 vote swing) shows 0.0 vote_swing
var result_inc_no_swing = plan.create_scenario_plan(
    NC_2025_incumbents_index,
    NC_2025_incumbents_scenarios,
    0.0,
    alternate_incumbents  // Different incumbents but 0.0 vote swing
);

// Verify that all districts have 0.0 vote_swing when vote swing parameter is 0.0
// even though incumbents have changed
for (var i = 0; i < result_inc_no_swing.districts.length; i++) {
    assert.equal(
        result_inc_no_swing.districts[i].vote_swing,
        0.0,
        'District ' + i + ' should have 0.0 vote_swing when vote swing parameter is 0.0, regardless of incumbency changes'
    );
}

// Test that vote_swing field reflects actual vote swing, not incumbency changes
var result_inc_with_swing = plan.create_scenario_plan(
    NC_2025_incumbents_index,
    NC_2025_incumbents_scenarios,
    2.0,  // Positive vote swing
    alternate_incumbents  // Different incumbents
);

// Verify that vote_swing values are non-zero and positive when vote swing parameter is positive
var has_nonzero_swings = false;
for (var i = 0; i < result_inc_with_swing.districts.length; i++) {
    var swing = result_inc_with_swing.districts[i].vote_swing;
    if (swing !== 0.0) {
        has_nonzero_swings = true;
    }
    // Vote swing should be roughly around the 2% (0.02) parameter, allowing for district variation
    assert.ok(
        typeof swing === 'number' && !isNaN(swing),
        'District ' + i + ' vote_swing should be a valid number, got: ' + swing
    );
    assert.ok(
        Math.abs(swing) < 0.1,  // Sanity check: shouldn't be wildly off
        'District ' + i + ' vote_swing (' + swing + ') should be reasonable (< 10%) when vote swing parameter is 2.0'
    );
}
assert.ok(has_nonzero_swings, 'At least some districts should have non-zero vote_swing when vote swing parameter is non-zero');

// Test parse_scenario_hash function
// Mock window.location.hash for testing
global.window = { location: { hash: '#scenario=margin_swing:3.0;incumbents:RDRRRRRRRRDRR' } };
var hash_result = plan.parse_scenario_hash();
assert.equal(hash_result.vote_swing, 1.5, 'Should parse margin_swing from hash and convert to vote_swing');
assert.equal(hash_result.incumbents, 'RDRRRRRRRRDRR', 'Should parse incumbents from hash');

global.window.location.hash = '#scenario=margin_swing:-4.0';
hash_result = plan.parse_scenario_hash();
assert.equal(hash_result.vote_swing, -2.0, 'Should parse negative margin_swing from hash and convert');
assert.equal(hash_result.incumbents, null, 'Should return null incumbents when not in hash');

global.window.location.hash = '#scenario=incumbents:ORDORD';
hash_result = plan.parse_scenario_hash();
assert.equal(hash_result.vote_swing, 0.0, 'Should default to 0.0 when margin_swing not in hash');
assert.equal(hash_result.incumbents, 'ORDORD', 'Should parse incumbents-only hash');

global.window.location.hash = '#scenario';
hash_result = plan.parse_scenario_hash();
assert.equal(hash_result.vote_swing, 0.0, 'Should default to 0.0 for bare #scenario');
assert.equal(hash_result.incumbents, null, 'Should return null incumbents for bare #scenario');

global.window.location.hash = '';
hash_result = plan.parse_scenario_hash();
assert.equal(hash_result, null, 'Should return null when no scenario hash present');

// Test encode_incumbents_rle function
// Test encoding 15 consecutive O's
assert.equal(plan.encode_incumbents_rle('OOOOOOOOOOOOOOO'), '15O', 'Should encode 15 O\'s as "15O"');

// Test encoding with mixed runs - user's example (5 O's, 2 R's, 3 D's)
assert.equal(plan.encode_incumbents_rle('OOOOORRDDD'), '5ORR3D', 'Should encode 5 O\'s, 2 R\'s, 3 D\'s as "5ORR3D"');

// Test encoding with runs of 1, 2, and 3+
assert.equal(plan.encode_incumbents_rle('ORDDRRRDDD'), 'ORDD3R3D', 'Should encode runs of 1, 2, and 3+ correctly');

// Test encoding all single characters (no compression)
assert.equal(plan.encode_incumbents_rle('ORDORD'), 'ORDORD', 'Should not compress single characters');

// Test encoding empty string
assert.equal(plan.encode_incumbents_rle(''), '', 'Should handle empty string');

// Test encoding very long run
assert.equal(plan.encode_incumbents_rle('DDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD'), '32D', 'Should encode 32 D\'s as "32D"');

// Test encoding multiple runs
assert.equal(plan.encode_incumbents_rle('OOOOOOOOOOOOOOODDDDDDDDDDDDDDDRRRRRRRRRRRRRRR'), '15O15D15R', 'Should encode multiple long runs');

// Test decode_incumbents_rle function
// Test decoding compressed format
assert.equal(plan.decode_incumbents_rle('15O'), 'OOOOOOOOOOOOOOO', 'Should decode "15O" to 15 O\'s');

// Test decoding user's example
assert.equal(plan.decode_incumbents_rle('5ORR3D'), 'OOOOORRDDD', 'Should decode "5ORR3D" correctly');

// Test decoding uncompressed format (backward compatibility)
assert.equal(plan.decode_incumbents_rle('ORDORD'), 'ORDORD', 'Should handle uncompressed format for backward compatibility');

// Test decoding empty string
assert.equal(plan.decode_incumbents_rle(''), '', 'Should handle empty string');

// Test decoding multiple runs
assert.equal(plan.decode_incumbents_rle('15O15D15R'), 'OOOOOOOOOOOOOOODDDDDDDDDDDDDDDRRRRRRRRRRRRRRR', 'Should decode multiple long runs');

// Test round-trip encoding/decoding
var original1 = 'OOOOOOOOOOOOOOO';
assert.equal(plan.decode_incumbents_rle(plan.encode_incumbents_rle(original1)), original1, 'Round-trip should preserve 15 O\'s');

var original2 = 'OOOOORRDDD';
assert.equal(plan.decode_incumbents_rle(plan.encode_incumbents_rle(original2)), original2, 'Round-trip should preserve "OOOOORRDDD"');

var original3 = 'ORDORD';
assert.equal(plan.decode_incumbents_rle(plan.encode_incumbents_rle(original3)), original3, 'Round-trip should preserve "ORDORD"');

// Test that compression actually reduces length for long runs
var long_string = 'O'.repeat(50);
var encoded = plan.encode_incumbents_rle(long_string);
assert.ok(encoded.length < long_string.length, 'Encoding should reduce length for long runs');
assert.equal(encoded, '50O', 'Should encode 50 O\'s as "50O"');

// Test parse_scenario_hash with compressed incumbents
global.window.location.hash = '#scenario=margin_swing:3.0;incumbents:15O';
hash_result = plan.parse_scenario_hash();
assert.equal(hash_result.vote_swing, 1.5, 'Should parse margin_swing with compressed incumbents');
assert.equal(hash_result.incumbents, 'OOOOOOOOOOOOOOO', 'Should decode compressed incumbents from hash');

global.window.location.hash = '#scenario=incumbents:5ORR3D';
hash_result = plan.parse_scenario_hash();
assert.equal(hash_result.incumbents, 'OOOOORRDDD', 'Should decode "5ORR3D" from hash');

// Test backward compatibility with old uncompressed hash
global.window.location.hash = '#scenario=incumbents:ORDORD';
hash_result = plan.parse_scenario_hash();
assert.equal(hash_result.incumbents, 'ORDORD', 'Should handle old uncompressed format in hash');
