assert = require('assert');
plan = require('./planscore/website/static/plan.js');
annotate_new = require('./planscore/website/static/annotate-new.js');

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
    FL_2020_declination = require('./data/sample-FL-declination/index.json'),
    CT_2021_water_district = require('./data/sample-CT-mostly-water-district/index.json');

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
        'Democratic Wins',
        'Democratic Votes',
        'Republican Votes',
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
    ['District', 'Candidate Scenario', 'Pop. 2010', 'Pop. 2016',
    'Black Pop. 2016', 'Hispanic Pop. 2016',
    'Predicted Democratic Vote Share', 'Predicted Republican Vote Share'],
    'Should pick out the right column names');

assert.deepEqual(plan_array7[1],
    ['1', 'Open Seat', 730943, 738237.35, '46.3%', '8.7%', '72.2% (±4.3%)', '27.8% (±2.3%)'],
    'Should pick out the right column values');

assert.deepEqual(plan_array7[2],
    ['2', 'Democratic Incumbent', 734253, 824484.63, '21.3%', '9.7%', '50.8% (±3.0%)', '49.2% (±2.9%)'],
    'Should pick out the right column values');

assert.deepEqual(plan_array7[3],
    ['3', 'Republican Incumbent', 732416, 708958.98, '23.2%', '7.9%', '44.1% (±3.2%)', '55.9% (±3.7%)'],
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

// Display preparation functions

var head1 = ['Democratic Votes', 'Republican Votes'];
plan.update_heading_titles(head1)
assert.deepEqual(head1, ['Predicted Democratic Vote Share', 'Predicted Republican Vote Share']);

var head2 = ['Citizen Voting-Age Population 2015', 'Asian Citizen Voting-Age Population 2015',
    'Black Citizen Voting-Age Population 2015', 'Hispanic Citizen Voting-Age Population 2015'];
plan.update_heading_titles(head2)
assert.deepEqual(head2, ['CVAP 2015', 'Non-Hisp. Asian CVAP 2015',
    'Non-Hisp. Black CVAP 2015', 'Hispanic CVAP 2015']);

var head3 = ['US President 2016 - DEM', 'US President 2016 - REP'];
plan.update_heading_titles(head3)
assert.deepEqual(head3, ['Clinton (D) 2016', 'Trump (R) 2016']);

var head4 = ['Democratic Wins'];
plan.update_heading_titles(head4)
assert.deepEqual(head4, ['Chance of Democratic Win']);

var head5 = ['Democratic Wins', 'Democratic Votes', 'Republican Votes'];
plan.update_heading_titles(head5)
assert.deepEqual(head5, ['Chance of Democratic Win', 'Predicted Vote Shares']);

var head6 = ['Population 2016', 'Black Population 2016', 'Hispanic Population 2016']
plan.update_heading_titles(head6)
assert.deepEqual(head6, ['Pop. 2016', 'Black Pop. 2016', 'Hispanic Pop. 2016']);

var head7 = ['US President 2020 - DEM', 'US President 2020 - REP']
plan.update_heading_titles(head7)
assert.deepEqual(head7, ['Biden (D) 2020', 'Trump (R) 2020']);

var head8 = ['US President 2016 - DEM', 'US President 2016 - REP', 'US President 2020 - DEM', 'US President 2020 - REP']
plan.update_heading_titles(head8)
assert.deepEqual(head8, [plan.SHY_COLUMN, plan.SHY_COLUMN, 'Biden (D) 2020', 'Trump (R) 2020']);

var head9 = ['US President 2024 - DEM', 'US President 2024 - REP']
plan.update_heading_titles(head9)
assert.deepEqual(head9, ['Harris (D) 2024', 'Trump (R) 2024']);

var head10 = ['US President 2020 - DEM', 'US President 2020 - REP', 'US President 2024 - DEM', 'US President 2024 - REP']
plan.update_heading_titles(head10)
assert.deepEqual(head10, [plan.SHY_COLUMN, plan.SHY_COLUMN, 'Harris (D) 2024', 'Trump (R) 2024']);

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

assert.equal(plan.partisan_suffix(0), '');
assert.equal(plan.partisan_suffix(1), '&nbsp;D');
assert.equal(plan.partisan_suffix(-1), '&nbsp;R');

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

assert.equal(annotate_new.missing_execution({}),
    true, 'Should see that no execution_id or token is set');

assert.equal(annotate_new.missing_execution({execution_id: null, execution_token: null}),
    true, 'Should see that execution_id and token are null');

assert.equal(annotate_new.missing_execution({execution_id: 'foo', execution_token: 'bar'}),
    false, 'Should see that execution_id and token are set');

assert.equal(annotate_new.which_plan_districts_count({districts: 'no'}),
    null, 'Should return no defined count');

assert.equal(annotate_new.which_plan_districts_count(NC_2019_preread_start),
    0, 'Should return correct district count');

assert.equal(annotate_new.which_plan_districts_count(NC_2019_preread_end),
    13, 'Should return correct district count');

assert.equal(annotate_new.get_description(NC_2019_preread_end, undefined),
    'North Carolina U.S. House plan uploaded on 12/28/2019');

console.log('Tests pass.', new Date().toLocaleString());
