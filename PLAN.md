# Plan: Add model_year as First Dimension in Scenarios Matrix

## Status

**✓ Backend (Python) - COMPLETED** (commit 966c91f1 on migurski/support-all-pvote-scenarios)
- All backend changes implemented and tested
- 186 Python tests passing
- 4D scenarios matrix successfully generating from multiple model versions

**✓ Frontend (JavaScript) - COMPLETED** (commit a02d6f44 on migurski/support-all-pvote-scenarios)
- All frontend changes implemented and tested
- Backwards compatibility helpers for 3D/4D scenarios working
- Model year selection UI with radio buttons functional
- JavaScript tests passing
- Radio button initialization bug fixed (using plan.model_year as default)

## Overview

Currently, the scenarios matrix is 3-dimensional: `[vote_swing, incumbent, district]`. We need to add `model_year` as a new first dimension, making it 4-dimensional: `[model_year, vote_swing, incumbent, district]`.

### Context

- **Current State**: Each upload processes a single model version (e.g., '2025A' or '2025B')
- **Goal**: Process ALL versions from `upload.model.versions` to generate scenarios across multiple model years
- **Model.versions**: A list like `['2025A', '2025B']` where each version has different prediction characteristics:
  - `'2025A'`: Uses 2020 pvote data, predicts for 2024
  - `'2025B'`: Uses 2024 pvote data, predicts for 2024
  - Each version has a `VersionParameters.year` (the prediction year)
- **Backwards Compatibility**: Must support older uploads that don't have this dimension
- **Negative Indexing**: Code already uses negative indexing (e.g., `shape[-2]`) in anticipation of this change

## Backend Changes (Python)

### 1. planscore/score.py - calculate_district_biases()

**Location**: Lines 1100-1258

**Current Behavior**:
- Processes only one model version: `upload.model_version or upload.model.versions[0]`
- Generates 4D `model_output`: `(incumbency=4, sims, districts, 2)`
- Creates 5D `all_votes`: `(swing_count, incumbency=4, sims, districts, 2)`
- Produces 6D `vote_stats`: `(swing_count, incumbency=4, sims, districts, 2, 3)`
- Outputs 3D scenarios statistics: `[swing][incumbent][district]`

**Required Changes**:

1. **Loop through all model versions** (around line 1106-1112):
2. **Update swing_vote_matrix call** (around line 1117):
3. **Update dimension extraction** (around line 1124):
4. **Update all_votes creation** (around line 1130-1133):
5. **Update vote_stats creation** (around line 1135-1143):
6. **Update scenarios dict** (around line 1144-1156):
7. **Update chosen scenario extraction** (around line 1160-1173):
8. **Update pvote_year and model_year** (around line 1252-1258):

### 2. planscore/matrix.py

**No changes needed** - All helper functions already use negative indexing:
- `swing_vote_matrix()` uses `votes.shape[-2]` for district_count
- Functions are designed to handle arbitrary leading dimensions

### 3. planscore/score.py - Helper Functions

**Verification needed** - These should work as-is but test carefully:

- `select_incumbency_stats()` (line 990): Uses `values.shape[-3]` for districts
- `select_incumbency_votes()` (line 1008): Uses `values.shape[-2]` for districts
- `swing_vote_matrix()` (line 176): Uses `votes.shape[-2]` for districts
- `vectorized_vote_statistics()`: Should handle 6D input automatically

## Frontend Changes (JavaScript)

### 4. planscore/website/static/plan.js - Backwards Compatibility

**Key Principle**: Detect format by checking `scenarios.dimensions` array

#### 4.1 Add Compatibility Helper Function

Add at top of file (after line 100):

```javascript
/**
 * Get a statistic value from scenarios, handling both 3D (old) and 4D (new) formats
 *
 * @param {Object} scenarios - The scenarios object
 * @param {string} stat_name - Name of statistic (e.g., 'Democratic Votes')
 * @param {number} model_year_idx - Model year index (ignored for 3D format)
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

    // Check if this is the new 4D format (has model_years dimension)
    if (scenarios.dimensions && scenarios.dimensions[0] === 'model_years') {
        // 4D: [model_year][swing][incumbent][district]
        return statistic[model_year_idx][swing_idx][inc_idx][dist_idx];
    } else {
        // 3D (legacy): [swing][incumbent][district]
        return statistic[swing_idx][inc_idx][dist_idx];
    }
}

/**
 * Check if scenarios use the new 4D format
 */
function is_4d_scenarios(scenarios)
{
    return scenarios.dimensions && scenarios.dimensions[0] === 'model_years';
}
```

#### 4.2 Update create_scenario_plan()

**Location**: Line 575

```javascript
function create_scenario_plan(original_plan, scenarios, vote_swing, scenario_incumbents)
{
    // Default to first model year (index 0)
    var model_year_idx = 0;

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
        baseline_vote_swing_index = vote_swing_index;
    }

    var mutated_plan = JSON.parse(JSON.stringify(original_plan));
    mutated_plan.incumbents = scenario_incumbents.slice();

    var dem_votes_mean = [];
    var rep_votes_mean = [];
    var dem_votes_sd = [];
    var rep_votes_sd = [];

    var all_open_seats = check_all_open_seats(scenario_incumbents);

    // Update each district with scenario data
    for (var district_index = 0; district_index < mutated_plan.districts.length; district_index++) {
        var incumbent_code = all_open_seats ? 'U' : scenario_incumbents[district_index];
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

        var current_total = dem_mean + rep_mean;
        var baseline_total = (baseline_dem || 0) + (baseline_rep || 0);

        if (current_total > 0 && baseline_total > 0) {
            // ... rest of vote_swing calculation (lines 674-680)
```

#### 4.3 Update populate_swing_metrics()

**Location**: Around line 742-790

Replace all direct scenarios.statistics access with `get_scenario_statistic()` calls:

```javascript
// OLD:
var dem_mean = scenarios.statistics['Democratic Votes'][sensitivity_index][incumbent_index][d];

// NEW:
var dem_mean = get_scenario_statistic(
    scenarios, 'Democratic Votes',
    0, sensitivity_index, incumbent_index, d
);
```

#### 4.4 Model Year Selection UI

Support model year display and selection in UI

- Add dropdown/selector in scenario adjustment form to choose model year
- Pass selected model_year_idx through `create_scenario_plan()`
- Update hash parameters to include model year selection

## Testing Updates

### 5. planscore/tests/test_score.py

**Required Test Updates**:

1. **Update existing tests** that check scenarios structure:
   - Look for assertions like `assertEqual(scenarios['dimensions'], ...)`
   - Update to expect 4D dimensions

2. **Add new test**: `test_calculate_district_biases_multiple_versions()`
   ```python
   def test_calculate_district_biases_multiple_versions(self):
       input = data.Upload(id=None, key=None,
           model=data.Model(data.State.XX, data.House.ushouse, 4, False,
                           ['2025A', '2025B'], None),
           districts=[...],
           incumbents=['D', 'R', 'O', 'D'],
       )

       output = score.calculate_district_biases(input)

       # Check 4D scenarios structure
       self.assertEqual(
           output.scenarios['dimensions'],
           ['model_years', 'vote_swings', 'incumbents', 'districts']
       )
       self.assertEqual(len(output.scenarios['model_years']), 2)
       self.assertEqual(output.scenarios['model_years'], [2024, 2024])

       # Check statistics are 4D
       dem_votes = output.scenarios['statistics']['Democratic Votes']
       self.assertEqual(len(dem_votes), 2)  # 2 model years
       self.assertEqual(len(dem_votes[0]), 25)  # 25 vote swings
       self.assertEqual(len(dem_votes[0][0]), 4)  # 4 incumbency scenarios
       self.assertEqual(len(dem_votes[0][0][0]), 4)  # 4 districts
   ```

3. **Add backwards compatibility test**: Verify single-version models still work
   ```python
   def test_calculate_district_biases_single_version(self):
       input = data.Upload(id=None, key=None,
           model=data.Model(data.State.XX, data.House.ushouse, 4, False,
                           ['2025A'], None),
           # ...
       )

       output = score.calculate_district_biases(input)

       # Should still produce 4D structure but with single model year
       self.assertEqual(len(output.scenarios['model_years']), 1)
   ```

### 6. tests.js - JavaScript Tests

**Required Test Updates**:

1. **Test backwards compatibility** with 3D scenarios:
   ```javascript
   test('create_scenario_plan handles 3D scenarios (legacy format)', function() {
       var scenarios_3d = {
           dimensions: ['vote_swings', 'incumbents', 'districts'],
           vote_swings: [-6.0, 0.0, 6.0],
           incumbents: ['O', 'D', 'R', 'U'],
           statistics: {
               'Democratic Votes': [/* 3D array */]
           }
       };

       var result = get_scenario_statistic(scenarios_3d, 'Democratic Votes', 0, 1, 2, 3);
       // Should access [1][2][3] ignoring model_year_idx
   });
   ```

2. **Test 4D scenarios** (new format):
   ```javascript
   test('create_scenario_plan handles 4D scenarios (new format)', function() {
       var scenarios_4d = {
           dimensions: ['model_years', 'vote_swings', 'incumbents', 'districts'],
           model_years: [2024, 2024],
           vote_swings: [-6.0, 0.0, 6.0],
           incumbents: ['O', 'D', 'R', 'U'],
           statistics: {
               'Democratic Votes': [/* 4D array */]
           }
       };

       var result = get_scenario_statistic(scenarios_4d, 'Democratic Votes', 1, 1, 2, 3);
       // Should access [1][1][2][3] including model_year_idx
   });
   ```

## Implementation Checklist

### Backend (Python) - COMPLETED ✓

- [x] Backend: Update `calculate_district_biases()` to loop through all model versions
- [x] Backend: Update `all_votes` and `vote_stats` creation for 5D/6D/7D arrays
- [x] Backend: Update scenarios dict with 4D statistics
- [x] Backend: Update chosen scenario extraction to use user-specified model version
- [x] Backend: Verify helper functions work with new dimensions
- [x] Backend: Fix vectorized_vote_statistics() axis bug (axis=-1 for dimension-agnostic stacking)
- [x] Tests: Update Python tests for 4D scenarios structure
- [x] Tests: Add multi-version test case (test_calculate_district_biases_multiple_versions)
- [x] Tests: Add single-version backwards compatibility test (test_calculate_district_biases_single_version)
- [x] Tests: Verify all existing tests still pass (186 tests passing)
- [x] Run full test suite: `python setup.py test`
- [x] Backend changes committed to git (commit 966c91f1)

### Frontend (JavaScript) - COMPLETED ✓

- [x] Frontend: Add `get_scenario_statistic()` and `is_4d_scenarios()` helpers
- [x] Frontend: Update `adjust_scenario_stats()` to handle both 3D and 4D formats
- [x] Frontend: Update `create_scenario_plan()` to accept model_year_idx parameter and use compatibility helpers
- [x] Frontend: Update all direct scenarios.statistics access to use compatibility helpers
- [x] Frontend: Add model year selection UI with radio buttons (using stubbed form from ee023a7e)
- [x] Frontend: Update `parse_scenario_hash()` to handle model_year parameter
- [x] Frontend: Update `update_scenario_hash()` to persist model_year parameter
- [x] Frontend: Fix radio button initialization to use plan.model_year as default
- [x] Frontend: Add `get_selected_model_year_idx()` helper function
- [x] Frontend: Update all callbacks to pass model_year_idx through the chain
- [x] Tests: Verify JavaScript tests still pass
- [x] Run JavaScript tests: `node tests.js`
- [x] Manual testing with real 4D scenarios data
- [x] Frontend changes committed to git (commit a02d6f44)

## Edge Cases to Consider

1. **Single model version**: Should produce 4D scenarios with length-1 model_years array
2. **Empty model.versions list**: Should fall back gracefully (unlikely in practice)
3. **Mixed pvote years**: Different model versions use different pvote data - track separately
4. **Frontend with old cached scenarios**: Compatibility layer handles this
5. **API consumers**: External tools reading scenarios.json need to check dimensions array

## Rollout Strategy

1. **Phase 1 - COMPLETED ✓**: Implement backend changes, all new uploads get 4D scenarios (commit 966c91f1)
2. **Phase 2 - COMPLETED ✓**: Deploy frontend with backwards compatibility and model year selection UI (commit a02d6f44)
3. **Phase 3 - READY**: Monitor for issues with old vs new scenarios in production
4. **Phase 4 - FUTURE**: Additional UI enhancements as needed

## Success Criteria

### Backend - COMPLETED ✓

- [x] New uploads with multi-version models generate 4D scenarios
- [x] New uploads with single-version models generate 4D scenarios (length-1)
- [x] All metrics calculations use user-specified model version
- [x] Test suite passes completely (186 tests passing)
- [x] No regression in existing functionality

### Frontend - COMPLETED ✓

- [x] Old uploads with 3D scenarios continue to work in frontend (backwards compatibility)
- [x] New uploads with 4D scenarios work correctly with model year selection
- [x] JavaScript tests pass
- [x] Manual testing confirms correct behavior in UI
- [x] Radio button initialization uses plan.model_year as default
- [x] Model year selection persists in URL hash
- [x] All visualizations update correctly when model year changes

## Implementation Summary

### Key Changes Implemented

1. **Backend (commit 966c91f1)**:
   - Extended `calculate_district_biases()` to loop through all model versions
   - Changed scenarios structure from 3D to 4D: `[model_years, vote_swings, incumbents, districts]`
   - All 186 Python tests passing

2. **Frontend (commit a02d6f44)**:
   - Added `get_scenario_statistic()` helper for backwards-compatible array access
   - Added `is_4d_scenarios()` helper to detect format
   - Updated `adjust_scenario_stats()` to handle both 3D and 4D decompression
   - Updated `create_scenario_plan()` to accept `model_year_idx` parameter
   - Integrated model year selection UI with existing radio buttons from ee023a7e
   - Added hash parameter support: `#scenario=margin_swing:3.0;incumbents:ORDORD;model_year:2024`
   - Fixed radio button initialization to use `plan.model_year` as default (similar to `plan.incumbents`)
   - All JavaScript tests passing

### Architecture Decisions

1. **Backwards Compatibility**: Detection via `scenarios.dimensions[0]` check
   - If `'model_years'`: Use 4D indexing `[model_year_idx][swing_idx][inc_idx][dist_idx]`
   - Otherwise: Use 3D indexing `[swing_idx][inc_idx][dist_idx]`

2. **Default Model Year**: Uses `plan.model_year` from backend (like `plan.incumbents`)
   - Backend populates this from `VersionParameters.year` during scoring
   - Frontend reads it on page load and checks the appropriate radio button

3. **Hash Parameter Persistence**: Model year only saved to hash if:
   - Scenarios are 4D format
   - Selected model year index is non-zero (not the default)

### Known Limitations

- UI currently shows years 2016, 2020, 2024 as radio buttons
- Only available years for the specific plan are shown (hidden otherwise)
- Model year selection affects all scenarios simultaneously (expected behavior)
