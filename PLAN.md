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

## Implementation Notes

- Both fixes are independent and can be applied separately
- Frontend fix is simpler and lower risk - consider deploying first
- Backend fix requires regenerating plans with pre-applied swings to get correct scenario data
- Existing plans with incorrect scenario data will need to be re-scored after backend fix
