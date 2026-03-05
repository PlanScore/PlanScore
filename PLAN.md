# Fix for Scenario Generation and Frontend Display Issues

## Problem Summary

Two related bugs are preventing correct scenario functionality:

1. **Backend Issue**: Plans uploaded with pre-applied per-district vote swings incorrectly generate scenarios with those swings already baked into the scenario data.
2. **Frontend Issue**: Plans with `null` vote_swing values in invalid districts are incorrectly flagged as having "margin swing adjustments applied", preventing scenario controls from displaying.

## Affected Plans

- **Plan with pre-applied swings**: https://planscore.org/plan.html?20260305T180634.417430779Z
  - Has non-zero vote_swing values (-0.029 to -0.056)
  - Backend incorrectly generated scenarios with swings baked in
  - Frontend correctly shows "This plan already has margin swing adjustments applied"

- **Plan with null swings**: https://planscore.org/plan.html?20260305T181521.750964899Z
  - Has vote_swing: 0.0 for valid districts, null for invalid districts
  - Backend correctly generated scenarios
  - Frontend incorrectly shows "This plan already has margin swing adjustments applied" due to null check bug

## Root Cause Analysis

### Backend Issue (score.py)

In `calculate_district_biases()` (line 1071-1288):

1. Line 1132: Applies per-district vote swings via `swing_vote_matrix(model_output, upload.vote_swings)`
2. Lines 1141-1150: Generates additional swing scenarios from this already-swung data
3. Lines 1169-1182: Creates scenarios dict with statistics from swung data
4. Line 1285: Attaches scenarios to plan

**Problem**: When `upload.vote_swings` contains non-zero values, scenarios are generated from data that already has those swings applied, making the scenario data incorrect.

**Expected**: Scenarios should only be generated for plans without pre-applied swings, since:
- Plans with pre-applied swings represent a specific scenario, not a baseline
- Interactive scenario exploration doesn't make sense with pre-applied swings
- The frontend correctly disables scenario controls when it detects pre-applied swings

### Frontend Issue (plan.js)

In `check_scenarios_available()` (line 1067-1086):

Line 1080 checks:
```javascript
if ('vote_swing' in plan.districts[i] && plan.districts[i].vote_swing !== 0.0) {
    return { available: false, reason: 'This plan already has margin swing adjustments applied' };
}
```

**Problem**: Invalid districts have `vote_swing: null` (set in score.py:1231). In JavaScript, `null !== 0.0` evaluates to `true`, causing the function to incorrectly return false for plans where all *valid* districts have zero swings.

**Expected**: The check should only consider numeric vote_swing values.

## Proposed Solution

### Backend Fix (planscore/score.py)

Around line 1169, conditionally generate scenarios only when no pre-applied swings exist:

```python
# Only generate scenarios if no per-district vote swings were applied
if not upload.vote_swings or not any(s != 0 for s in upload.vote_swings):
    scenarios = dict(
        model_years=scenario_keys,
        vote_swings=list(swing_range),
        incumbents=list(INCUMBENCY.keys()),
        districts=list(range(1, 1 + district_count)),
        dimensions=["model_years", "vote_swings", "incumbents", "districts"],
        statistics={
            "Democratic Wins": vote_stats_diff[:, :, :, :, 0, 0].tolist(),
            "Democratic Votes": vote_stats_diff[:, :, :, :, 0, 1].tolist(),
            "Republican Votes": vote_stats_diff[:, :, :, :, 1, 1].tolist(),
            "Democratic Votes SD": vote_stats_diff[:, :, :, :, 0, 2].tolist(),
            "Republican Votes SD": vote_stats_diff[:, :, :, :, 1, 2].tolist(),
        }
    )
else:
    scenarios = None
```

Update line 1285 to handle the None case:
```python
return upload.clone(
    districts=copied_districts,
    summary=summary_dict,
    scenarios=scenarios,  # Will be None if pre-applied swings exist
    pvote_year=pvote_years[chosen_version_idx],
    model_year=model_years[chosen_version_idx],
)
```

### Frontend Fix (planscore/website/static/plan.js)

Line 1080, add type check before comparison:

```javascript
// Change from:
if ('vote_swing' in plan.districts[i] && plan.districts[i].vote_swing !== 0.0) {

// To:
if (typeof plan.districts[i].vote_swing === 'number' && plan.districts[i].vote_swing !== 0.0) {
```

This ensures only numeric vote_swing values are checked, ignoring null values from invalid districts.

## Expected Outcomes

After applying both fixes:

1. **Plans with non-zero pre-applied vote swings**:
   - Backend: No scenarios generated (scenarios = None)
   - Frontend: Shows "This plan already has margin swing adjustments applied"
   - Frontend: Displays Margin Swing column in districts table
   - Frontend: Scenario controls disabled

2. **Plans with zero swings (or no swings)**:
   - Backend: Scenarios generated normally
   - Frontend: Shows interactive scenario controls
   - Frontend: No Margin Swing column initially (appears when user adjusts swings)
   - Frontend: Full scenario interactivity available

3. **Old plans without model support**:
   - Backend: No scenarios generated (no presidential votes to model)
   - Frontend: Shows "PlanScore did not calculate alternative outcomes for this plan"
   - Frontend: Scenario controls disabled

## Testing Plan

1. Test backend fix with plan that has pre-applied swings:
   - Upload plan with non-zero vote_swings
   - Verify scenarios field is None in output JSON
   - Verify vote_swing values are preserved in districts

2. Test frontend fix with plan that has null swings:
   - Load plan with null vote_swing values in some districts
   - Verify scenario controls display correctly
   - Verify null values don't trigger "already applied" message

3. Regression testing:
   - Test normal plan with scenarios (no pre-applied swings)
   - Verify interactive scenarios work correctly
   - Verify Margin Swing column appears when adjusting scenarios

## Unit Test Specifications

### Backend Tests (planscore/tests/test_score.py)

#### Test 1: `test_calculate_district_biases_with_vote_swings`
**Purpose**: Verify that scenarios are NOT generated when upload has non-zero vote_swings

**Setup**:
- Create an Upload object with presidential vote data
- Set `upload.vote_swings = [0.05, 0.08, 0.07, 0.05]` (non-zero values)
- Mock `matrix.prepare_district_data` and `matrix.model_votes` to return test data

**Assertions**:
```python
result = score.calculate_district_biases(upload)
assert result.scenarios is None, "Scenarios should not be generated for plans with pre-applied swings"
assert result.districts[0]['vote_swing'] == 0.05, "vote_swing values should be preserved in districts"
assert result.districts[1]['vote_swing'] == 0.08
assert 'Democratic Votes' in result.districts[0]['totals'], "District totals should still be calculated"
```

#### Test 2: `test_calculate_district_biases_without_vote_swings`
**Purpose**: Verify that scenarios ARE generated when upload has no vote_swings or all zeros

**Setup**:
- Create an Upload object with presidential vote data
- Set `upload.vote_swings = None` (or `[0.0, 0.0, 0.0, 0.0]`)
- Mock `matrix.prepare_district_data` and `matrix.model_votes` to return test data

**Assertions**:
```python
result = score.calculate_district_biases(upload)
assert result.scenarios is not None, "Scenarios should be generated for plans without pre-applied swings"
assert 'model_years' in result.scenarios
assert 'vote_swings' in result.scenarios
assert 'incumbents' in result.scenarios
assert 'statistics' in result.scenarios
assert result.districts[0]['vote_swing'] == 0.0, "vote_swing should be 0.0 for all districts"
```

#### Test 3: `test_calculate_district_biases_with_zero_vote_swings`
**Purpose**: Verify that explicit zero vote_swings are treated as no pre-applied swings

**Setup**:
- Create an Upload object with presidential vote data
- Set `upload.vote_swings = [0.0, 0.0, 0.0, 0.0]` (explicit zeros)
- Mock `matrix.prepare_district_data` and `matrix.model_votes` to return test data

**Assertions**:
```python
result = score.calculate_district_biases(upload)
assert result.scenarios is not None, "Scenarios should be generated even with explicit zero swings"
assert result.districts[0]['vote_swing'] == 0.0
```

#### Test 4: `test_calculate_district_biases_mixed_vote_swings`
**Purpose**: Verify that ANY non-zero vote_swing prevents scenario generation

**Setup**:
- Create an Upload object with presidential vote data
- Set `upload.vote_swings = [0.0, 0.01, 0.0, 0.0]` (only one non-zero)
- Mock `matrix.prepare_district_data` and `matrix.model_votes` to return test data

**Assertions**:
```python
result = score.calculate_district_biases(upload)
assert result.scenarios is None, "Even one non-zero vote_swing should prevent scenario generation"
assert result.districts[1]['vote_swing'] == 0.01
```

#### Test 5: `test_invalid_districts_get_null_vote_swing`
**Purpose**: Verify that invalid districts receive null vote_swing values

**Setup**:
- Create an Upload object where some districts have insufficient data (trigger `valid_mask[i] == False`)
- Set `upload.vote_swings = [0.05, 0.08]` or `None`

**Assertions**:
```python
result = score.calculate_district_biases(upload)
# Assuming district 1 is invalid (valid_mask[1] == False)
assert result.districts[1]['vote_swing'] is None, "Invalid districts should have null vote_swing"
assert result.districts[1]['is_counted'] is False
assert result.districts[0]['vote_swing'] is not None, "Valid districts should have numeric vote_swing"
```

### Frontend Tests (tests.js)

#### Test 6: `test_check_scenarios_available_with_null_vote_swings`
**Purpose**: Verify that null vote_swing values don't trigger "already applied" message

**Setup**:
```javascript
var plan_with_null_swings = {
    scenarios: "/uploads/test/scenarios.json",
    districts: [
        { vote_swing: 0.0, totals: { 'Democratic Votes': 1000 } },
        { vote_swing: 0.0, totals: { 'Democratic Votes': 1000 } },
        { vote_swing: null, totals: { 'Democratic Votes': 0 } },  // Invalid district
        { vote_swing: null, totals: { 'Democratic Votes': 0 } }   // Invalid district
    ]
};
```

**Assertions**:
```javascript
var availability = plan.check_scenarios_available(plan_with_null_swings);
assert.strictEqual(availability.available, true,
    "Scenarios should be available when only null vote_swings are present");
assert.strictEqual(availability.reason, null, "No reason should be given");
```

#### Test 7: `test_check_scenarios_available_with_nonzero_vote_swings`
**Purpose**: Verify that non-zero numeric vote_swings prevent scenario availability

**Setup**:
```javascript
var plan_with_nonzero_swings = {
    scenarios: "/uploads/test/scenarios.json",
    districts: [
        { vote_swing: 0.05, totals: { 'Democratic Votes': 1000 } },
        { vote_swing: 0.08, totals: { 'Democratic Votes': 1000 } },
        { vote_swing: null, totals: { 'Democratic Votes': 0 } }
    ]
};
```

**Assertions**:
```javascript
var availability = plan.check_scenarios_available(plan_with_nonzero_swings);
assert.strictEqual(availability.available, false,
    "Scenarios should not be available with non-zero vote_swings");
assert.strictEqual(availability.reason, 'This plan already has margin swing adjustments applied',
    "Should show the correct reason message");
```

#### Test 8: `test_check_scenarios_available_with_zero_vote_swings`
**Purpose**: Verify that explicit zero vote_swings allow scenario availability

**Setup**:
```javascript
var plan_with_zero_swings = {
    scenarios: "/uploads/test/scenarios.json",
    districts: [
        { vote_swing: 0.0, totals: { 'Democratic Votes': 1000 } },
        { vote_swing: 0.0, totals: { 'Democratic Votes': 1000 } },
        { vote_swing: 0.0, totals: { 'Democratic Votes': 1000 } }
    ]
};
```

**Assertions**:
```javascript
var availability = plan.check_scenarios_available(plan_with_zero_swings);
assert.strictEqual(availability.available, true,
    "Scenarios should be available with all zero vote_swings");
assert.strictEqual(availability.reason, null);
```

#### Test 9: `test_check_scenarios_available_no_scenarios_field`
**Purpose**: Verify that plans without scenarios field are handled correctly

**Setup**:
```javascript
var plan_without_scenarios = {
    districts: [
        { vote_swing: 0.0, totals: { 'Democratic Votes': 1000 } }
    ]
};
```

**Assertions**:
```javascript
var availability = plan.check_scenarios_available(plan_without_scenarios);
assert.strictEqual(availability.available, false,
    "Scenarios should not be available without scenarios field");
assert.strictEqual(availability.reason,
    'PlanScore did not calculate alternative outcomes for this plan');
```

#### Test 10: `test_check_scenarios_available_mixed_null_and_zero`
**Purpose**: Verify that mix of null and 0.0 values works correctly

**Setup**:
```javascript
var plan_mixed_swings = {
    scenarios: "/uploads/test/scenarios.json",
    districts: [
        { vote_swing: 0.0, totals: { 'Democratic Votes': 1000 } },
        { vote_swing: null, totals: { 'Democratic Votes': 0 } },
        { vote_swing: 0.0, totals: { 'Democratic Votes': 1000 } },
        { vote_swing: null, totals: { 'Democratic Votes': 0 } }
    ]
};
```

**Assertions**:
```javascript
var availability = plan.check_scenarios_available(plan_mixed_swings);
assert.strictEqual(availability.available, true,
    "Scenarios should be available with mix of 0.0 and null values");
assert.strictEqual(availability.reason, null);
```

### Integration Test Data

Create new test fixtures in `/data/` directory:

#### Test Fixture 1: `sample-MS-nonzero-vote-swings/`
- Copy from `sample-MS-vote-swings/` but ensure:
  - `index.json` has non-zero `vote_swing` values in all valid districts
  - No `scenarios.json` file (or scenarios field points to null)
  - Used to verify backend doesn't generate scenarios

#### Test Fixture 2: `sample-MS-null-vote-swings/`
- Create plan with:
  - Some districts with `vote_swing: 0.0`
  - Some districts with `vote_swing: null` (invalid districts)
  - Valid `scenarios.json` file with scenario data
  - Used to verify frontend shows scenarios correctly

#### Test Fixture 3: `sample-MS-all-zero-swings/`
- Already exists as `sample-MS-zero-vote-swings/`
- Verify it has scenarios.json and all valid districts have `vote_swing: 0.0`

## Implementation Progress

### Backend Tests - ✅ COMPLETED
Added 3 tests to `planscore/tests/test_score.py`:

1. **test_calculate_district_biases_with_vote_swings** (lines 2044-2098)
   - Status: ✅ PASSING
   - Tests that scenarios are NOT generated with non-zero vote_swings
   - Verifies scenarios is None when upload has pre-applied swings

2. **test_calculate_district_biases_mixed_vote_swings** (lines 2100-2146)
   - Status: ✅ PASSING
   - Tests that even ONE non-zero vote_swing prevents scenario generation
   - Verifies any non-zero swing prevents scenarios

3. **test_invalid_districts_get_null_vote_swing** (lines 2148-2215)
   - Status: ✅ PASSING
   - Tests that invalid districts receive null vote_swing values
   - Verifies invalid districts are properly marked with None

All backend tests now passing.

### Backend Implementation - ✅ COMPLETED

**File: planscore/score.py** (lines 1169-1187)
- Added conditional check before generating scenarios
- Scenarios only generated when `upload.vote_swings` is None or all zeros
- When non-zero swings exist, scenarios is set to None
- Preserves vote_swing values in district output regardless of scenario generation

**File: planscore/data.py** (line 238)
- Modified Upload.__init__ to preserve explicit None for scenarios
- Changed from `scenarios or {}` to `scenarios` (direct assignment)
- Allows scenarios=None to be stored without conversion to empty dict
- Maintains backward compatibility for other Upload creation patterns

**File: planscore/tests/test_score.py** (line 2193-2199)
- Fixed test mock to return NaN values for invalid districts
- Changed district 1 mock data from [0, 0] to [numpy.nan, numpy.nan]
- Ensures valid_mask correctly identifies invalid districts

### Frontend Tests - ✅ COMPLETED (Tests added and failing as expected)

Added 2 failing tests to `tests.js` that demonstrate the bug:

1. **test_check_scenarios_available_with_null_vote_swings** (lines 1256-1270)
   - Status: ❌ FAILING (demonstrates the bug)
   - Tests that null vote_swing values should not prevent scenario availability
   - Currently fails because `null !== 0.0` is true in JavaScript
   - The bug: Invalid districts have `vote_swing: null` but the check treats null as non-zero

2. **test_check_scenarios_available_mixed_null_and_zero** (lines 1272-1286)
   - Status: ❌ FAILING (demonstrates the bug)
   - Tests that mix of null and 0.0 values should allow scenario availability
   - Currently fails because null values are incorrectly treated as non-zero
   - The bug: When some districts have 0.0 and others have null, scenarios should still be available

**Export Update**: Added `check_scenarios_available` to plan.js module.exports (line 3976) to enable testing.

### Next Steps
1. ✅ ~~Implement backend fix in `planscore/score.py`~~
2. ✅ ~~Verify all 3 backend tests pass after fix~~
3. ✅ ~~Add failing frontend tests to `tests.js`~~
4. Implement frontend fix in `planscore/website/static/plan.js`
5. Verify all frontend tests pass after fix

## Implementation Notes

- Both fixes are independent and can be applied separately
- Frontend fix is simpler and lower risk - consider deploying first
- Backend fix requires regenerating plans with pre-applied swings to get correct scenario data
- Existing plans with incorrect scenario data will need to be re-scored after backend fix
- All new tests should be added to existing test files (`test_score.py` and `tests.js`)
- Test fixtures should follow existing naming conventions in `/data/` directory
