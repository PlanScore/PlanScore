assert = require('assert');
plan = require('planscore/website/static/plan.js');

var sample_nc_1_992 = require('data/sample-NC-1-992/index.json'),
    sample_nc_1_992_simple = require('data/sample-NC-1-992-simple/index.json');

assert.equal(plan.which_score_summary_name(sample_nc_1_992_simple),
    'Efficiency Gap', 'Should pick out the right summary name');

assert.deepEqual(plan.which_score_column_names(sample_nc_1_992_simple),
    ['Voters', 'Blue Votes', 'Red Votes'], 'Should pick out the right column names');

assert.equal(plan.which_district_color(sample_nc_1_992_simple.districts[0], sample_nc_1_992_simple),
    '#D45557', 'Should return the red district color');

assert.equal(plan.which_district_color(sample_nc_1_992_simple.districts[7], sample_nc_1_992_simple),
    '#4D90D1', 'Should return the blue district color');

assert.equal(plan.which_score_summary_name(sample_nc_1_992),
    'US House Efficiency Gap', 'Should pick out the right summary name');

assert.deepEqual(plan.which_score_column_names(sample_nc_1_992),
    ['Population', 'Voting-Age Population', 'Black Voting-Age Population',
     'US House Dem Votes', 'US House Rep Votes'], 'Should pick out the right column names');

assert.equal(plan.format_url('https://example.com/{id}.html', 'xyz'),
    'https://example.com/xyz.html', 'URL should format correctly');

assert.equal(plan.which_district_color(sample_nc_1_992.districts[0], sample_nc_1_992),
    '#D45557', 'Should return the red district color');

assert.equal(plan.which_district_color(sample_nc_1_992.districts[7], sample_nc_1_992),
    '#4D90D1', 'Should return the blue district color');

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
