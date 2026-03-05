# Fix for Scenario Generation and Frontend Display Issues

## Problem Summary

Four related bugs are preventing correct scenario functionality:

1. **Backend Issue #1**: Plans uploaded with pre-applied per-district vote swings incorrectly generate scenarios with those swings already baked into the scenario data.
2. **Backend Issue #2**: Plans with invalid districts generate scenarios containing NaN values, which are serialized as the literal string "NaN" (invalid JSON), causing parse errors in the frontend.
3. **Frontend Issue #1**: Plans with `null` vote_swing values in invalid districts are incorrectly flagged as having "margin swing adjustments applied", preventing scenario controls from displaying.
4. **Frontend Issue #2**: Plans with pre-applied swings that also have scenarios data (from backend bug #1) show the correct warning message but fail to keep the form disabled, allowing users to interact with invalid scenario controls.
5. **Frontend Issue #3**: Plans with invalid scenarios JSON (containing NaN values) cause uncaught parse errors, preventing the scenario form from being displayed at all.

## Affected Plans

- **Plan with pre-applied swings**: https://planscore.org/plan.html?20260305T180634.417430779Z
  - Has non-zero vote_swing values (-0.029 to -0.056)
  - Backend incorrectly generated scenarios with swings baked in
  - Frontend correctly shows "This plan already has margin swing adjustments applied"
  - **BUG**: Form is NOT disabled - class `scenario-adjustments-disabled` is not applied to form#scenario-adjustments

- **Plan with null swings and NaN in scenarios**: https://planscore.org/plan.html?20260305T181521.750964899Z
  - Has vote_swing: 0.0 for valid districts, null for invalid districts (district 139)
  - Backend generated scenarios but included NaN values for invalid districts
  - scenarios.json contains 48 instances of literal "NaN" string (invalid JSON)
  - **BUG**: Frontend throws "SyntaxError: JSON Parse error: Unexpected identifier 'NaN'" at plan.js:3653
  - **BUG**: Scenario form never appears due to uncaught parse error
  - Frontend incorrectly shows "This plan already has margin swing adjustments applied" due to null check bug (before the parse error was fixed)

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

### Frontend Issue #1 (plan.js - check_scenarios_available)

In `check_scenarios_available()` (line 1067-1086):

Line 1080 checks:
```javascript
if ('vote_swing' in plan.districts[i] && plan.districts[i].vote_swing !== 0.0) {
    return { available: false, reason: 'This plan already has margin swing adjustments applied' };
}
```

**Problem**: Invalid districts have `vote_swing: null` (set in score.py:1231). In JavaScript, `null !== 0.0` evaluates to `true`, causing the function to incorrectly return false for plans where all *valid* districts have zero swings.

**Expected**: The check should only consider numeric vote_swing values.

### Frontend Issue #2 (plan.js - setup_scenario_interactivity)

In `setup_scenario_interactivity()` (line 1380):

Line 1380 unconditionally removes the disabled class:
```javascript
// Show the form now that it's fully initialized
scenario_adjustments_form.classList.remove('scenario-adjustments-hidden');
scenario_adjustments_form.classList.remove('scenario-adjustments-disabled');
```

**Problem**: This function is called from `load_plan_scenarios()` which is triggered whenever `plan.scenarios` exists (line 3577-3581). Due to backend bug #1, plans with pre-applied vote swings may have scenarios data, causing this code path to execute. The function unconditionally removes the `scenario-adjustments-disabled` class that was correctly added by `update_form_visibility()` at line 1097.

**Call sequence**:
1. Line 1091: `update_form_visibility()` calls `check_scenarios_available()`
2. Line 1094-1097: Correctly adds `scenario-adjustments-disabled` class when scenarios aren't available
3. Line 3577: If `plan.scenarios !== undefined`, calls `load_plan_scenarios()`
4. Line 3653: `load_plan_scenarios()` calls `setup_scenario_interactivity()`
5. Line 1380: Unconditionally removes `scenario-adjustments-disabled` class

**Expected**: `setup_scenario_interactivity()` should not remove the disabled class if scenarios are not actually available for this plan (i.e., if the plan has pre-applied vote swings).

### Backend Issue #2 (score.py and observe.py - NaN serialization)

In `calculate_district_biases()` (lines 1179-1183) and `put_upload_index()` (line 39):

1. Lines 1179-1183: Converts numpy arrays to Python lists via `.tolist()`
2. Invalid districts have NaN values in vote_stats arrays (from insufficient data)
3. `.tolist()` converts numpy NaN to Python `float('nan')`
4. Line 39 (observe.py): `json.dumps(upload.scenarios)` serializes the scenarios dict
5. Python's json module (with default `allow_nan=True`) writes `float('nan')` as literal string "NaN"

**Problem**: The literal string "NaN" is not valid JSON per RFC 8259. While JavaScript allows it, strict JSON parsers (including JavaScript's JSON.parse()) will throw a SyntaxError. Plans with invalid districts (e.g., district 139 in plan 20260305T181521.750964899Z) end up with 48+ NaN values in scenarios.json.

**Expected**: Either:
- Filter out invalid districts from scenarios entirely, OR
- Replace NaN values with `None` (serializes to JSON `null`) before calling json.dumps(), OR
- Use a custom JSON encoder that handles NaN values

### Frontend Issue #3 (plan.js - load_plan_scenarios)

In `load_plan_scenarios()` (line 3653):

Line 3653 directly parses the response:
```javascript
var data = JSON.parse(request.responseText);
```

**Problem**: When scenarios.json contains literal "NaN" strings (from Backend Issue #2), JSON.parse() throws a SyntaxError. This uncaught error prevents the scenario form from being displayed at all, leaving users with no feedback about why scenarios aren't working.

**Expected**: Catch parse errors and display the scenario form in a disabled state with an appropriate error message.

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

### Frontend Fix #1 (planscore/website/static/plan.js - check_scenarios_available)

Line 1080, add type check before comparison:

```javascript
// Change from:
if ('vote_swing' in plan.districts[i] && plan.districts[i].vote_swing !== 0.0) {

// To:
if (typeof plan.districts[i].vote_swing === 'number' && plan.districts[i].vote_swing !== 0.0) {
```

This ensures only numeric vote_swing values are checked, ignoring null values from invalid districts.

### Frontend Fix #2 (planscore/website/static/plan.js - setup_scenario_interactivity)

Line 1380, conditionally remove the disabled class only if scenarios are actually available:

```javascript
// Change from:
// Show the form now that it's fully initialized
scenario_adjustments_form.classList.remove('scenario-adjustments-hidden');
scenario_adjustments_form.classList.remove('scenario-adjustments-disabled');

// To:
// Show the form now that it's fully initialized
scenario_adjustments_form.classList.remove('scenario-adjustments-hidden');
// Only remove disabled class if scenarios are actually available for this plan
var availability = check_scenarios_available(plan);
if (availability.available) {
    scenario_adjustments_form.classList.remove('scenario-adjustments-disabled');
}
```

This ensures the form stays disabled when the plan has pre-applied vote swings, even if scenarios data exists (from backend bug #1).

### Frontend Fix #3 (planscore/website/static/plan.js - load_plan_scenarios)

Line 3653, wrap JSON.parse() in try-catch and handle parse errors:

```javascript
// Change from:
var data = JSON.parse(request.responseText);
console.log('Loaded scenarios:', data);
adjust_scenario_stats(data);
console.log('New scenarios:', data);
setup_scenario_interactivity(plan, data, scenario_adjustments_form, districts_table, map_div, metrics_table, score_EG, score_sense, score_PB, score_MM, score_DEC2, scores_FTVA);

// To:
try {
    var data = JSON.parse(request.responseText);
    console.log('Loaded scenarios:', data);
    adjust_scenario_stats(data);
    console.log('New scenarios:', data);
    setup_scenario_interactivity(plan, data, scenario_adjustments_form, districts_table, map_div, metrics_table, score_EG, score_sense, score_PB, score_MM, score_DEC2, scores_FTVA);
} catch (e) {
    // Handle invalid JSON (e.g., scenarios containing NaN values)
    console.error('Failed to parse scenarios JSON:', e);
    // Show the form in disabled state with error message
    scenario_adjustments_form.classList.remove('scenario-adjustments-hidden');
    scenario_adjustments_form.classList.add('scenario-adjustments-disabled');
    var caption_el = scenario_adjustments_form.querySelector('.caption');
    if (caption_el) {
        caption_el.textContent = 'This plan did not have scenarios correctly calculated';
    }
}
```

This ensures that when scenarios.json contains invalid JSON (like NaN values), the user sees a clear error message instead of a blank page with console errors.

## Expected Outcomes

After applying all three fixes:

1. **Plans with non-zero pre-applied vote swings**:
   - Backend: No scenarios generated (scenarios = None)
   - Frontend: Shows "This plan already has margin swing adjustments applied"
   - Frontend: Displays Margin Swing column in districts table
   - Frontend: Scenario controls disabled (class `scenario-adjustments-disabled` applied and retained)
   - Frontend: Form remains disabled even if old scenarios data exists from before backend fix

2. **Plans with zero swings (or no swings)**:
   - Backend: Scenarios generated normally
   - Frontend: Shows interactive scenario controls
   - Frontend: No Margin Swing column initially (appears when user adjusts swings)
   - Frontend: Full scenario interactivity available

3. **Old plans without model support**:
   - Backend: No scenarios generated (no presidential votes to model)
   - Frontend: Shows "PlanScore did not calculate alternative outcomes for this plan"
   - Frontend: Scenario controls disabled

4. **Plans with invalid scenarios (containing NaN)**:
   - Backend: With Backend Fix #2: Invalid districts filtered out or NaN replaced with null
   - Frontend: With Frontend Fix #3: JSON parse errors caught gracefully
   - Frontend: Shows "This plan did not have scenarios correctly calculated"
   - Frontend: Form displayed with `scenario-adjustments-disabled` class
   - Frontend: User sees clear error message instead of blank page with console errors

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

### Frontend Tests - ✅ COMPLETED

Added 5 tests to `tests.js` to verify correct scenario availability behavior:

1. **test_check_scenarios_available_with_null_vote_swings** (lines 1256-1270)
   - Status: ✅ PASSING
   - Tests that null vote_swing values should not prevent scenario availability
   - Verifies invalid districts with null swings don't block scenarios

2. **test_check_scenarios_available_mixed_null_and_zero** (lines 1272-1286)
   - Status: ✅ PASSING
   - Tests that mix of null and 0.0 values should allow scenario availability
   - Verifies correct handling of mixed null and zero values

3. **test_check_scenarios_available_with_nonzero_vote_swings** (lines 1288-1302)
   - Status: ✅ PASSING
   - Tests that non-zero numeric vote_swings prevent scenario availability
   - Verifies pre-applied swings correctly disable scenarios

4. **test_check_scenarios_available_with_zero_vote_swings** (lines 1304-1317)
   - Status: ✅ PASSING
   - Tests that explicit zero vote_swings allow scenario availability
   - Verifies all-zero plans can use scenarios

5. **test_check_scenarios_available_no_scenarios_field** (lines 1319-1331)
   - Status: ✅ PASSING
   - Tests that plans without scenarios field are handled correctly
   - Verifies appropriate message for plans without scenarios

**Export Update**: Added `check_scenarios_available` to plan.js module.exports (line 3976) to enable testing.

### Frontend Implementation #1 - ✅ COMPLETED

**File: planscore/website/static/plan.js** (line 1080)
- Added type check before comparing vote_swing to 0.0
- Changed from: `if ('vote_swing' in plan.districts[i] && plan.districts[i].vote_swing !== 0.0)`
- Changed to: `if (typeof plan.districts[i].vote_swing === 'number' && plan.districts[i].vote_swing !== 0.0)`
- Only numeric vote_swing values are now checked, null values are ignored
- Invalid districts with null vote_swing no longer incorrectly block scenarios

All frontend tests now passing for issue #1.

### Frontend Implementation #2 - ✅ COMPLETED

**File: planscore/website/static/plan.js** (lines 1380-1384 in `setup_scenario_interactivity`)
- Added conditional check before removing `scenario-adjustments-disabled` class
- Calls `check_scenarios_available(plan)` to verify scenarios are actually available
- Only removes disabled class if `availability.available === true`
- This prevents the form from being incorrectly enabled when plans have pre-applied swings but also have scenarios data (from backend bug #1)
- All tests still pass after this change

### Frontend Implementation #3 - ✅ COMPLETED

**File: planscore/website/static/plan.js** (lines 3656-3671 in `load_plan_scenarios`)
- Wrapped `JSON.parse()` in try-catch block to handle invalid JSON
- Catches parse errors (e.g., scenarios containing literal "NaN" strings)
- On error, displays form in disabled state with class `scenario-adjustments-disabled`
- Shows error message "This plan did not have scenarios correctly calculated"
- Logs error to console for debugging
- Try-catch scope narrowed to ONLY wrap JSON.parse() (not subsequent function calls)
- Added early return on parse error to prevent executing subsequent code
- All tests still pass after this change
- Bug fix: Changed `plan` to `original_plan` at line 1381 in setup_scenario_interactivity to fix ReferenceError

### Frontend Implementation #4 - ✅ COMPLETED

**File: planscore/website/static/plan.js** (lines 3581-3590 in main plan loading)
- Added check for scenario availability BEFORE checking if `plan.scenarios` field exists
- Prevents attempting to load scenarios.json when plan has pre-applied vote swings
- Fixes regression where plans with pre-applied swings would attempt to load scenarios
- Now correctly shows "This plan already has margin swing adjustments applied" instead of attempting to load scenarios and showing parse error message
- This ensures the proper message is displayed based on the actual reason scenarios are unavailable

### Backend Implementation #2 - ✅ COMPLETED (NaN Serialization Fix)

**File: planscore/score.py** (lines 1169-1177, 1193-1198)

Added `numpy_to_list_with_nulls()` helper function to replace NaN values with None before JSON serialization:

```python
def numpy_to_list_with_nulls(arr):
    """
    Convert numpy array to list, replacing NaN with None for valid JSON.
    Water districts and other invalid districts may have NaN values.
    """
    # Replace NaN in the numpy array before converting to list
    arr_copy = arr.copy()
    arr_copy = numpy.where(numpy.isnan(arr_copy), None, arr_copy)
    return arr_copy.tolist()
```

Applied this function to all statistics arrays when generating scenarios:
- "Democratic Wins", "Democratic Votes", "Republican Votes", etc.
- Converts NaN values at the numpy level before .tolist() conversion
- Results in valid JSON with null values instead of literal "NaN" strings
- More efficient than recursive post-processing of nested Python lists

**Impact**: Plans with invalid/water districts now generate valid JSON scenarios with null values instead of causing parse errors.

### Frontend Implementation #5 - ✅ COMPLETED (Null Value Handling in adjust_scenario_stats)

**File: planscore/website/static/plan.js** (lines 522-568 in `adjust_scenario_stats`)

Updated the scenario statistics adjustment logic to handle null values gracefully:

**Legacy format (3 dimensions)**:
```javascript
var base = stat[0][0][k];
var diff = stat[i][j][k];
// Handle null values from invalid districts (e.g., water districts)
stat[i][j][k] = (base === null || diff === null) ? null : base + diff;
```

**New format (4 dimensions with model_year)**:
```javascript
var base = stat[0][0][0][m];
var diff = stat[i][j][k][m];
// Handle null values from invalid districts (e.g., water districts)
stat[i][j][k][m] = (base === null || diff === null) ? null : base + diff;
```

**Changes**:
- Added null checks before performing arithmetic operations
- If either base or diff value is null, result is null (not NaN)
- Prevents propagation of NaN through scenario calculations
- Invalid districts retain null values throughout all scenarios

**Impact**: Plans with null values in scenarios (from water districts) now process correctly without generating NaN in calculations.

### Next Steps
1. ✅ ~~Implement backend fix #1 in `planscore/score.py`~~
2. ✅ ~~Verify all 3 backend tests pass after fix~~
3. ✅ ~~Add failing frontend tests to `tests.js`~~
4. ✅ ~~Implement frontend fix #1 in `planscore/website/static/plan.js`~~
5. ✅ ~~Verify all frontend tests pass after fix~~
6. ✅ ~~Implement frontend fix #2 in `planscore/website/static/plan.js`~~
7. ✅ ~~Implement frontend fix #3 for NaN parse error handling~~
8. ✅ ~~Implement frontend fix #4 to prevent loading scenarios with pre-applied swings~~
9. ✅ ~~Implement backend fix #2 for NaN serialization in `planscore/score.py`~~
10. ✅ ~~Implement frontend fix #5 for null value handling in `adjust_scenario_stats()`~~
11. ✅ ~~Run all backend and frontend tests~~
12. ⏳ **Deploy and test fixes** - After deployment:
   - Verify plan 20260305T180634.417430779Z shows "This plan already has margin swing adjustments applied" (not parse error)
   - Verify new uploads with invalid/water districts generate valid JSON with null values (not literal "NaN")
   - Verify plans with null values in scenarios display and calculate correctly
13. ⏳ **Commit all changes**

## Implementation Notes

- All three fixes are independent and can be applied separately
- Frontend fixes #1 and #2 are simpler and lower risk - can be deployed immediately
- Frontend fix #2 is especially important for existing plans that have both pre-applied swings AND scenarios data (from backend bug #1)
- Backend fix requires regenerating plans with pre-applied swings to get correct scenario data
- Existing plans with incorrect scenario data will need to be re-scored after backend fix
- Once backend fix is deployed, frontend fix #2 will still be necessary for backward compatibility with old plans
- All new tests should be added to existing test files (`test_score.py` and `tests.js`)
- Test fixtures should follow existing naming conventions in `/data/` directory
