# Plan: Switch Scenario Keys from Integer to Combined String Format

## Problem Statement
Currently, scenario keys use only `model_year` (integer like `2024`). This doesn't distinguish between scenarios with the same model year but different presidential vote years (e.g., model 2025A uses pvote 2020, model 2025B uses pvote 2024). This causes incorrect presidential vote column selection in `update_heading_titles`.

## Solution
Change scenario keys from single integer to combined string format: `"{model_year} ({pvote_year})"` (e.g., `"2024 (2020)"`, `"2024 (2024)"`).

---

## Backend Changes (Python) ✅ COMPLETED

### 1. **planscore/score.py** - Line ~1164 ✅ DONE (commit e8270627)

**Implemented:**
```python
# Combine model_year and pvote_year into scenario keys
scenario_keys = [
    f"{model_year} ({pvote_year})"
    for model_year, pvote_year in zip(model_years, pvote_years)
]

scenarios = dict(
    model_years=scenario_keys,  # ["2024 (2020)", "2024 (2024)"]
    ...
)
```

**Result:** Backend now generates combined scenario keys that include both model year and presidential vote year.

### 2. **planscore/tests/test_score.py** ✅ DONE (commit e8270627)
- ✅ Updated test assertions to expect string format: `["2020 (2020)", "2024 (2020)"]`
- ✅ Added verification for `test_calculate_district_biases_multiple_versions`
- ✅ Added verification for `test_calculate_district_biases_single_version`
- ✅ All 147 Python tests pass

---

## Frontend Changes (JavaScript) ✅ COMPLETED

### 3. **planscore/website/static/plan.js** - Add parsing helper function ✅ DONE (commit b5398f77)

**Implemented:** Added `parse_scenario_year_key()` function that:
- Parses new string format: `"2024 (2020)"` → `{model_year: 2024, pvote_year: 2020}`
- Handles legacy integer format: `2024` → `{model_year: 2024, pvote_year: 2024}`
- Handles integer strings and extra whitespace
- Returns `null` for invalid input
- Provides backward compatibility with old plans

### 4. **planscore/website/static/plan.js** - Update `create_scenario_plan` ✅ DONE (commit b5398f77)

**Implemented:** Function now:
- Extracts pvote_year from scenario keys using `parse_scenario_year_key()`
- Defaults to `original_plan.pvote_year` if parsing fails
- Adds `pvote_year` to mutated plan so `update_heading_titles()` can use correct presidential vote year
- Ensures presidential vote columns display correct year for each scenario

### 5. **planscore/website/static/plan.js** - Update radio button setup ✅ DONE (commit b5398f77)

**Implemented:** Radio button logic now:
- Parses scenario keys to extract model_year for matching
- Shows/hides radio buttons based on parsed model_year
- Checks appropriate radio button on page load based on initial model year
- Maintains backward compatibility with integer-based scenarios

### 6. **planscore/website/static/plan.js** - Update `get_selected_model_year_idx` ✅ DONE (commit b5398f77)

**Implemented:** Function now:
- Parses each scenario key to find matching model_year
- Returns correct index for selected scenario
- Handles both new string format and legacy integer format

### 7. **planscore/website/static/plan.js** - Hash parsing ✅ DONE (commit b5398f77)

**Implemented:** Hash parsing continues to:
- Extract only model_year from hash (not full scenario key)
- Match parsed model_year against scenario keys
- Maintain existing URL structure

### 8. **planscore/website/static/plan.js** - Hash encoding ✅ DONE (commits b5398f77, 362f048f)

**Implemented:** `update_scenario_hash()` now:
- Accepts `default_model_year` parameter from plan
- Parses scenario key to extract model_year
- Only includes model_year in hash if different from plan's default
- Prevents unnecessary URL clutter when using default model year

### 9. **planscore/website/static/plan.js** - Column header updates ✅ DONE (commit ec6f3ac9)

**Implemented:** `populate_districts_table()` now:
- Updates thead headers when pvote_year changes
- Ensures presidential vote column headers show correct year
- Fixes display issue when switching between scenarios with different pvote years

### 10. **planscore/website/static/plan.js** - Function renaming ✅ DONE (commit 75f62481)

**Implemented:** Renamed `is_4d_scenarios()` to `has_model_year_dimension()`:
- Provides clearer semantic meaning
- Better describes what the function checks
- Updated all references throughout codebase

---

## Testing

### 11. **Python tests** - Update test_score.py ✅ DONE (commit e8270627)
- ✅ Found tests checking `scenarios['model_years']` format
- ✅ Updated assertions to expect string format: `["2020 (2020)", "2024 (2020)"]`
- ✅ Tests verify correct format for both multi-version and single-version scenarios
- ✅ All 147 Python tests pass

### 12. **JavaScript tests** - Update tests.js ✅ DONE (commit b5398f77)
- ✅ Added comprehensive tests for `parse_scenario_year_key()` covering:
  - New string format: `"2024 (2020)"` → `{model_year: 2024, pvote_year: 2020}`
  - Legacy integer format: `2024` → `{model_year: 2024, pvote_year: 2024}`
  - Integer strings: `"2024"` → `{model_year: 2024, pvote_year: 2024}`
  - Different years: `"2024 (2016)"`
  - Extra whitespace handling
  - Invalid input returns `null`
- ✅ All JavaScript tests pass

---

## Backward Compatibility Strategy

1. **Old plans without model_year dimension (3D scenarios)**: No changes needed - they don't use model_years array
2. **Plans with pvote_year but no model_year**: Will continue to work as plan.pvote_year is unchanged
3. **New plans with 4D scenarios**: Will use combined string format
4. **Parser handles both formats**: `parse_scenario_key()` accepts both integers and strings for robustness

---

## Success Criteria

### Backend (Python) ✅ COMPLETE
✅ Scenario keys combine model_year and pvote_year: `"2024 (2020)"` (commit e8270627)
✅ All Python tests pass (147 tests passing)

### Frontend (JavaScript) ✅ COMPLETE
✅ Radio buttons show/hide based on parsed model_year from scenario keys (commit b5398f77)
✅ `update_heading_titles` receives correct pvote_year from selected scenario (commit b5398f77)
✅ Presidential vote columns display correct year via column header updates (commits b5398f77, ec6f3ac9)
✅ URL hash correctly encodes/decodes model years, omits default values (commits b5398f77, 362f048f)
✅ All JavaScript tests pass (commit b5398f77)
✅ Backward compatibility maintained for plans without model_year dimension (commit b5398f77)
✅ Function naming improved for clarity (commit 75f62481)

---

## Implementation Status

✅ **ALL WORK COMPLETE!**

**Backend (commit e8270627):**
- ✅ Python backend generates combined scenario keys: `"2024 (2020)"`
- ✅ All 147 Python tests passing

**Frontend (commits b5398f77, ec6f3ac9, 362f048f, 75f62481):**
- ✅ JavaScript parses and uses combined scenario keys
- ✅ Column headers update correctly when scenario changes
- ✅ URL hash handling optimized to omit default values
- ✅ Function naming improved for clarity
- ✅ All JavaScript tests passing
- ✅ Backward compatibility maintained

**Ready for Production:**
All backend and frontend changes are complete. The system now correctly:
- Distinguishes scenarios with same model year but different presidential vote years
- Displays correct presidential vote data for each scenario
- Maintains backward compatibility with older plans
- Provides clean URL structure

**Key Commits:**
- `e8270627` - Backend implementation
- `b5398f77` - Frontend JavaScript implementation
- `ec6f3ac9` - Column header updates
- `362f048f` - URL hash optimization
- `75f62481` - Function renaming for clarity
