assert = require('assert');
plan = require('planscore/website/static/plan.js');

var NC_index = require('data/sample-NC-1-992/index.json'),
    NC_incomplete_index = require('data/sample-NC-1-992-incomplete/index.json'),
    NC_simple_index = require('data/sample-NC-1-992-simple/index.json'),
    NC_multisim_index = require('data/sample-NC-simulations/index.json'),
    NC_public_index = require('data/sample-NC5.1/index.json');

// Old-style red vs. blue plan

assert.equal(plan.what_score_description_html(NC_simple_index),
    '<i>No description provided</i>', 'Should find the right description');

assert.equal(plan.which_score_summary_name(NC_simple_index),
    'Efficiency Gap', 'Should pick out the right summary name');

assert.deepEqual(plan.which_score_column_names(NC_simple_index),
    ['Voters', 'Blue Votes', 'Red Votes'], 'Should pick out the right column names');

assert.equal(plan.which_district_color(NC_simple_index.districts[0], NC_simple_index),
    '#D45557', 'Should return the red district color');

assert.equal(plan.which_district_color(NC_simple_index.districts[7], NC_simple_index),
    '#4D90D1', 'Should return the blue district color');

var plan_array1 = plan.plan_array(NC_simple_index);
assert.equal(plan_array1.length, 14, 'Should have a header with 13 districts');

// Incomplete plan, seen just after upload but before scoring is complete

assert.equal(plan.what_score_description_html(NC_incomplete_index),
    '<i>No description provided</i>', 'Should find the right description');

assert.strictEqual(plan.which_score_summary_name(NC_incomplete_index),
    null, 'Should return a null summary name');

assert.deepEqual(plan.which_score_column_names(NC_incomplete_index),
    [], 'Should return an empty list of column names');

var plan_array2 = plan.plan_array(NC_incomplete_index);
assert.equal(plan_array2, undefined, 'Should have an undefined table');

// North Carolina plan with named house and parties

assert.equal(plan.what_score_description_html(NC_index),
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

var plan_array3 = plan.plan_array(NC_index);
assert.equal(plan_array3.length, 14, 'Should have a header with 13 districts');

// New-style North Carolina plan with confidence intervals from simulations

assert.equal(plan.what_score_description_html(NC_multisim_index),
    '<i>No description provided</i>', 'Should find the right description');

assert.equal(plan.which_score_summary_name(NC_multisim_index),
    'Efficiency Gap', 'Should pick out the right summary name');

assert.deepEqual(plan.which_score_column_names(NC_multisim_index),
    ['Population 2010', 'Population 2015', 'Black Population 2015', 'Hispanic Population 2015',
    'Population 2016', 'Black Population 2016', 'Hispanic Population 2016',
    'Citizen Voting-Age Population 2015', 'Black Citizen Voting-Age Population 2015',
    'Hispanic Citizen Voting-Age Population 2015', 'Democratic Votes',
    'Republican Votes'/*, 'Polsby-Popper', 'Reock'*/],
    'Should pick out the right column names');

assert.equal(plan.which_district_color(NC_multisim_index.districts[0], NC_multisim_index),
    '#D45557', 'Should return the red district color');

assert.equal(plan.which_district_color(NC_multisim_index.districts[7], NC_multisim_index),
    '#4D90D1', 'Should return the blue district color');

var plan_array4 = plan.plan_array(NC_multisim_index);
assert.equal(plan_array4.length, 14, 'Should have a header with 13 districts');

assert.deepEqual(plan_array4[0],
    ['District', 'Predicted Democratic Vote Share', 'Predicted Republican Vote Share'],
    'Should pick out the right column names');

assert.deepEqual(plan_array4[1],
    ['1', '47.4%', '52.6%'],
    'Should pick out the right column values');

assert.deepEqual(plan_array4[13],
    ['13', '42.3%', '57.7%'],
    'Should pick out the right column values');

assert.equal(plan.get_description(NC_multisim_index, new Date(2018, 0, 14)),
    'Plan uploaded on 1/14/2018');

// North Carolina plan in proposed final form

var plan_array5 = plan.plan_array(NC_public_index);
assert.equal(plan_array5.length, 14, 'Should have a header with 13 districts');

assert.deepEqual(plan_array5[0],
    ['District', 'Population 2010', 'Population 2015', 'Black Population 2015',
    'Hispanic Population 2015', 'Predicted Democratic Vote Share',
    'Predicted Republican Vote Share'/*, 'Polsby-Popper', 'Reock'*/],
    'Should pick out the right column names');

assert.deepEqual(plan_array5[1],
    ['1', 733460.0, 734814.32, '46.3%', '8.3%', '66.1%', '33.9%'/*, 0.1992, 0.3469*/],
    'Should pick out the right column values');

assert.deepEqual(plan_array5[13],
    ['13', 733505.0, 747501.53, '22.8%', '7.5%', '43.9%', '56.1%'/*, 0.2274, 0.3557*/],
    'Should pick out the right column values');

assert.equal(plan.get_description(NC_public_index, undefined),
    'North Carolina U.S. House plan uploaded on 1/14/2018');

// Display preparation functions

var head1 = ['Democratic Votes', 'Republican Votes'];
plan.update_heading_titles(head1)
assert.deepEqual(head1, ['Predicted Democratic Vote Share', 'Predicted Republican Vote Share']);

var head2 = ['Citizen Voting-Age Population 2015',
    'Black Citizen Voting-Age Population 2015', 'Hispanic Citizen Voting-Age Population 2015'];
plan.update_heading_titles(head2)
assert.deepEqual(head2, ['Citizen Voting-Age Population 2015',
    'Black Non-Hispanic CVAP 2015', 'Hispanic CVAP 2015']);

var row1 = [4, 6];
plan.update_vote_percentages(['Democratic Votes', 'Republican Votes'], row1);
assert.deepEqual(row1, ['40.0%', '60.0%']);

var row2 = [4, 6];
plan.update_vote_percentages(['Democratic Votes', 'Republican Smokes'], row2);
assert.deepEqual(row2, [4, 6]);

var row3 = [4, 6];
plan.update_vote_percentages(['Democratic Jokes', 'Republican Votes'], row3);
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

// Assorted functions

assert(plan.date_age(new Date('1970-01-01')) > 86400 * 365);
assert(plan.date_age(new Date('2017-10-01')) < 86400 * 365 * 5);
assert(plan.date_age(new Date()) < 1);

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

assert.equal(plan.nice_gap(.1), '+10.0% for Democrats', 'Positive gaps should be blue');
assert.equal(plan.nice_gap(-.1), '+10.0% for Republicans', 'Negative gaps should be red');

assert.equal(plan.nice_string('yo'), '&#121;&#111;');
