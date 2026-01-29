# Refactoring Plan: Move Incumbency Selection from `model_votes()` to `calculate_district_biases()`

- Our local python virtualenv is in .venv-py39, use it
- A useful way to test this code is with `planscore-score-locally https://planscore--dev.s3.amazonaws.com/uploads/20260127T042257.547602478Z/index.json` which calls planscore.score:main().
- Test as you go, checking before and after you make changes that behavior is as expected
- The Recommended sequence of work, repeated below, looks like:
    1. Add `INCUMBENCY` constant to score.py (after line 26)
    2. Modify `model_votes()` to generate all 3 incumbency scenarios in order [-1, 0, 1]
    3. Add incumbency selection logic to `calculate_district_biases()` using `INCUMBENCY`
    4. Update all test mocks to use `(incumbency, sims, districts, 2)` shape
    5. Update test assertions in `test_model_votes()` to verify 3 scenarios exist
    6. Update test assertions in `test_calculate_gap_unified_incumbents()` to verify correct selection
    7. Run full test suite: `python setup.py test`

## Overview
Currently, `model_votes()` assigns individual incumbency scenarios to each district and returns `(sims, districts, 2)`. After changes, it will generate votes for ALL three incumbency scenarios and return `(incumbency, sims, districts, 2)`, with `calculate_district_biases()` selecting the appropriate scenario per district.

## Files Requiring Changes

### CORE CHANGES (The main refactoring)

#### 1. **planscore/score.py** - Add new constant (after line 26)
**New constant:** Add mapping for incumbency scenario to array index

```python
# After line 26 (after COLUMN_MMD definition):
INCUMBENCY = {
    data.Incumbency.Republican.value: 0,  # 'R' -> index 0 (model value -1)
    data.Incumbency.Open.value: 1,        # 'O' -> index 1 (model value 0)
    data.Incumbency.Democrat.value: 2,    # 'D' -> index 2 (model value 1)
}
```

**Rationale:**
- Mirrors the style of `matrix.INCUMBENCY` constant
- Array stacked in order [-1, 0, 1] matching model incumbency values
- Placed in score.py since that's where it's used for selection
- Makes the mapping explicit and maintainable in one place

#### 2. **planscore/matrix.py::model_votes()** (lines 165-203)
**Current behavior:** Takes districts with per-district incumbency, returns `(sims, districts, 2)`

**Required changes:**
- Remove use of incumbency from input districts tuple
- Call `apply_model()` **three times** with incumbency values in order `[-1, 0, 1]` (Republican/Open/Democrat)
- Stack results into shape `(incumbency, sims, districts, 2)` where dimension 0 indexes incumbency scenario
- Update docstring to reflect new return shape

**Key line references:**
- Line 171-175: Docstring "Return is a SxDx2 matrix" → Change to "Return is an IxSxDx2 matrix where first dimension is incumbency scenario (Republican=-1, Open=0, Democrat=1)"
- Lines 184-191: Currently processes `(dem, rep, inc)` per district → Change to only use `(dem, rep)` and loop over 3 incumbency scenarios
- Line 201: Return statement needs to stack all 3 scenarios along new first axis

**Detailed implementation:**
```python
# Build votes for all three incumbency scenarios
incumbency_scenarios = [-1, 0, 1]  # Republican, Open, Democrat (matches INCUMBENCY order)
all_fractions = []

for inc_value in incumbency_scenarios:
    fractions = apply_model(
        [(dem / ((dem + rep) or numpy.nan), inc_value) for (dem, rep, _) in districts],
        load_model(params.path_suffix, STATE[state], params.year, has_incumbents, is_congress),
        params,
    )
    all_fractions.append(fractions)

# Stack: (incumbency, sims, districts)
all_fractions = numpy.stack(all_fractions, axis=0)

# Create SxD scale array (same for all incumbency scenarios)
total_votes = sum([dem + rep for (dem, rep, _) in districts])
one_district_votes = total_votes / len(districts)
scale = numpy.full(all_fractions.shape[1:], one_district_votes)  # (sims, districts)

# Build IxSxDx2 array with per-party vote totals for each incumbency, simulation, district, and party
votes_dem = (all_fractions * scale).round(1)  # (incumbency, sims, districts)
votes_rep = ((1 - all_fractions) * scale).round(1)  # (incumbency, sims, districts)
votes = numpy.stack([votes_dem, votes_rep], axis=3)  # (incumbency, sims, districts, 2)

return votes
```

#### 3. **planscore/score.py::calculate_district_biases()** (lines 937-1081)
**Current behavior:** Receives `(sims, districts, 2)` with pre-selected incumbency

**Required changes:**
- After line 982, receive `(incumbency, sims, districts, 2)` from `model_votes()`
- Add incumbency selection logic using `upload.incumbents` and `INCUMBENCY` constant
- Apply `swing_vote_matrix()` to selected votes

**Implementation location:** Between lines 982-983

**Detailed implementation:**
```python
# Line 974-982: Call model_votes
output_votes = swing_vote_matrix(
    matrix.model_votes(
        upload.model_version or upload.model.versions[0],
        upload.model.state,
        upload.model.house,
        matrix.filter_district_data(matrix.prepare_district_data(upload)),
    ),
    upload.vote_swings,
)
# output_votes shape is now (incumbency, sims, districts, 2)

# NEW CODE: Select appropriate incumbency scenario per district
incumbency_count, sim_count, district_count, _ = output_votes.shape

# Select the correct incumbency scenario for each district using INCUMBENCY
selected_votes = numpy.zeros((sim_count, district_count, 2))
for i, incumbency in enumerate(upload.incumbents):
    idx = INCUMBENCY[incumbency]
    selected_votes[:, i, :] = output_votes[idx, :, i, :]

# Continue with selected votes
output_votes = selected_votes
# output_votes shape is now back to (sims, districts, 2)

# Line 983+: Rest of function continues unchanged
sim_count, district_count, _ = output_votes.shape
```

**Alternative implementation (more vectorized):**
```python
# Select incumbency scenarios using fancy indexing
incumbency_indices = numpy.array([INCUMBENCY[inc] for inc in upload.incumbents])
# Select: for each district i, take output_votes[incumbency_indices[i], :, i, :]
selected_votes = output_votes[incumbency_indices, :, numpy.arange(district_count), :]
# This needs transpose to get (sims, districts, 2)
selected_votes = numpy.transpose(selected_votes, (1, 0, 2))
```

**Key line references:**
- Line 974-982: Call to `model_votes()` - output shape changes here
- Line 983: Insert incumbency selection logic before continuing

### UPSTREAM CHANGES (Functions that prepare data)

#### 4. **planscore/matrix.py::prepare_district_data()** (lines 205-231)
**Current behavior:** Returns `list[tuple[float, float, str]]` with incumbency in third position

**Required changes:**
- **No changes needed to function implementation**
- Incumbency is still returned for use by `calculate_district_biases()`
- `model_votes()` will simply ignore the third tuple element (can access with `_`)

**Note:** Could optionally update to return `list[tuple[float, float]]` but keeping incumbency maintains backwards compatibility and is still needed by the score.py caller.

### TEST CHANGES (All tests need updating for new return shape)

#### 5. **planscore/tests/test_matrix.py::test_model_votes()** (lines 286-317)
**Current changes:**
- Line 290-293: Mock `apply_model.return_value` stays as `(sims, districts)`
- Line 314-317: Update expected result shape from `(2, 3, 2)` to `(3, 2, 3, 2)`:
```python
# Expected shape is (incumbency_scenarios, sims, districts, parties)
self.assertEqual(R.shape, (3, 2, 3, 2))
# Verify each incumbency scenario
self.assertEqual(R[0].tolist(), [...])  # Republican incumbent (idx 0)
self.assertEqual(R[1].tolist(), [...])  # Open seat (idx 1)
self.assertEqual(R[2].tolist(), [...])  # Democrat incumbent (idx 2)
```

#### 6. **planscore/tests/test_matrix.py::test_model_votes_with_zeros()** (lines 319-353)
**Current changes:**
- Line 348-353: Update shape expectations to `(incumbency, sims, districts, 2)`
- Verify NaN handling works across all 3 incumbency scenarios

#### 7. **planscore/tests/test_score.py::test_calculate_gap_unified()** (lines 1334-1432)
**Current changes:**
- Line 1355-1359: Mock return shape changes to `(incumbency, sims, districts, 2)`:
```python
model_votes.return_value = numpy.array([
    [[[5.3, 2.7], [3.9, 4.1], [2.8, 5.2], [1.9, 6.1]]],  # R incumbent (idx 0)
    [[[5.3, 2.7], [3.9, 4.1], [2.8, 5.2], [1.9, 6.1]]],  # Open (idx 1)
    [[[5.3, 2.7], [3.9, 4.1], [2.8, 5.2], [1.9, 6.1]]],  # D incumbent (idx 2)
])  # Shape: (3, 1, 4, 2) -> reduced to (1, 4, 2) after selection
```
- No assertions about incumbency passed to `model_votes` (it's ignored now)

#### 8. **planscore/tests/test_score.py::test_calculate_gap_unified_vote_swing()** (lines 1447-1549)
**Current changes:**
- Line 1469-1473: Update mock return shape to `(incumbency, sims, districts, 2)`

#### 9. **planscore/tests/test_score.py::test_calculate_gap_unified_incumbents()** (lines 1559-1590)
**Current changes:**
- Line 1580-1584: Update mock return shape to `(incumbency, sims, districts, 2)` with **different values per scenario**
- Lines 1587-1590: **Remove** these assertions - they checked incumbency passed to `model_votes`
- **Add** new assertions to verify correct incumbency scenario selection using `INCUMBENCY`

**New test logic:**
```python
# Mock with distinguishable values per incumbency scenario
model_votes.return_value = numpy.array([
    [[[5.0, 3.0], [4.0, 4.0], [3.0, 5.0], [2.0, 6.0]]],  # R scenario (idx 0)
    [[[6.0, 2.0], [5.0, 3.0], [4.0, 4.0], [3.0, 5.0]]],  # O scenario (idx 1)
    [[[7.0, 1.0], [6.0, 2.0], [5.0, 3.0], [4.0, 4.0]]],  # D scenario (idx 2)
])
# With incumbents = ['R', 'D', 'R', 'D'], verify:
# - District 0 uses R scenario (idx 0): [5.0, 3.0]
# - District 1 uses D scenario (idx 2): [6.0, 2.0]
# - District 2 uses R scenario (idx 0): [3.0, 5.0]
# - District 3 uses D scenario (idx 2): [4.0, 4.0]
```

#### 10. **planscore/tests/test_score.py::test_calculate_fva_votes()** (lines 1601-1658)
**Current changes:**
- Line 1641-1645: Update mock return shape to `(incumbency, sims, districts, 2)`

#### 11. **planscore/tests/test_score.py::test_calculate_gap_with_zeros()** (lines 1668-1762)
**Current changes:**
- Line 1689-1693: Update mock return shape to `(incumbency, sims, districts, 2)`
- Ensure NaN districts work across all incumbency scenarios

## Implementation Order

**Recommended sequence:**
1. Add `INCUMBENCY` constant to score.py (after line 26)
2. Modify `model_votes()` to generate all 3 incumbency scenarios in order [-1, 0, 1]
3. Add incumbency selection logic to `calculate_district_biases()` using `INCUMBENCY`
4. Update all test mocks to use `(incumbency, sims, districts, 2)` shape
5. Update test assertions in `test_model_votes()` to verify 3 scenarios exist
6. Update test assertions in `test_calculate_gap_unified_incumbents()` to verify correct selection
7. Run full test suite: `python setup.py test`

## Summary

**Files to modify:**
- **Core:** 2 files (matrix.py, score.py)
- **Tests:** 2 files (test_matrix.py, test_score.py)

**Functions/constants to modify:**
- **Core:** 1 new constant (INCUMBENCY), 2 functions (model_votes, calculate_district_biases)
- **Tests:** 8 test functions

**Breaking changes:** Yes - `model_votes()` return shape changes from `(sims, districts, 2)` to `(incumbency, sims, districts, 2)`

**Key design decisions:**
- Array stacking order matches model incumbency values: [-1, 0, 1] → Republican, Open, Democrat
- `INCUMBENCY` constant placed in score.py where it's used, mirrors matrix.INCUMBENCY pattern
- `prepare_district_data()` unchanged - still returns incumbency for downstream use

**No changes needed:**
- `matrix.py::main()` - excluded per request, may be deleted
- `matrix.py::prepare_district_data()` - still returns incumbency for use by calculate_district_biases()
