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
    ['Population 2015', 'Black Population 2015', 'Democratic Votes', 'Republican Votes', 'Polsby-Popper', 'Reock'],
    'Should pick out the right column names');

assert.equal(plan.which_district_color(NC_multisim_index.districts[0], NC_multisim_index),
    '#D45557', 'Should return the red district color');

assert.equal(plan.which_district_color(NC_multisim_index.districts[7], NC_multisim_index),
    '#4D90D1', 'Should return the blue district color');

var plan_array4 = plan.plan_array(NC_multisim_index);
assert.equal(plan_array4.length, 14, 'Should have a header with 13 districts');

assert.deepEqual(plan_array4[0],
    ['District', 'Democratic Votes', 'Republican Votes'],
    'Should pick out the right column names');

assert.deepEqual(plan_array4[1],
    ['1', 1028053.906695856, 1140266.0413978184],
    'Should pick out the right column values');

assert.deepEqual(plan_array4[13],
    ['13', 841420.1306598457, 1149160.4424367815],
    'Should pick out the right column values');

// North Carolina plan in proposed final form

var plan_array5 = plan.plan_array(NC_public_index);
assert.equal(plan_array5.length, 14, 'Should have a header with 13 districts');

assert.deepEqual(plan_array5[0],
    ['District', 'Population 2015', 'Black Population 2015', 'Democratic Votes', 'Republican Votes', 'Polsby-Popper', 'Reock'],
    'Should pick out the right column names');

assert.deepEqual(plan_array5[1],
    ['1', 734814, 339971, 226503, 115999, 0.199, 0.346],
    'Should pick out the right column values');

assert.deepEqual(plan_array5[13],
    ['13', 747501, 170567, 155381, 198285, 0.227, 0.355],
    'Should pick out the right column values');

// Assorted functions

assert(plan.date_age(new Date('1970-01-01')) > 86400 * 365);
assert(plan.date_age(new Date('2017-10-01')) < 86400 * 365 * 5);
assert(plan.date_age(new Date()) < 1);

assert.equal(plan.nice_count(7654321), '7654.3k', 'Should not have a thousands separator');
assert.equal(plan.nice_count(4321), '4.3k', 'Should show numbers in thousands');
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
