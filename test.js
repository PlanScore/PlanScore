assert = require('assert');
planscore = { plan: require('planscore/website/static/plan.js') };

assert.equal(planscore.plan.format_url('https://example.com/{id}.html', 'xyz'),
    'https://example.com/xyz.html', 'URL should format correctly');

assert.equal(planscore.plan.nice_count(7654321), '7654.3k', 'Should not have a thousands separator');
assert.equal(planscore.plan.nice_count(4321), '4.3k', 'Should show numbers in thousands');
assert.equal(planscore.plan.nice_count(321), '321', 'Should see a literal integer');
assert.equal(planscore.plan.nice_count(21), '21.0', 'Should see one decimal place');
assert.equal(planscore.plan.nice_count(1), '1.00', 'Should see two decimal places');
assert.equal(planscore.plan.nice_count(-1), '–', 'Should not see a negative number');

assert.equal(planscore.plan.nice_percent(1), '100.0%', 'Should see one decimal place');
assert.equal(planscore.plan.nice_percent(.1), '10.0%', 'Should see one decimal place');
assert.equal(planscore.plan.nice_percent(.01), '1.0%', 'Should see one decimal place');
assert.equal(planscore.plan.nice_percent(.001), '0.1%', 'Should see one decimal place');

assert.equal(planscore.plan.nice_gap(.1), '+10.0% for Democrats', 'Positive gaps should be blue');
assert.equal(planscore.plan.nice_gap(-.1), '+10.0% for Republicans', 'Negative gaps should be red');
