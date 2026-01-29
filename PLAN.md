# Refactoring Plan: Keep Incumbency Dimension Until Line 1033

- Our local python virtualenv is in .venv-py39, use it
- A useful way to test this code is with `planscore-score-locally https://planscore--dev.s3.amazonaws.com/uploads/20260129T041903.684277570Z/index.json` which calls planscore.score:main().
- Test as you go, checking before and after you make changes that behavior is as expected

## Overview
Move incumbency selection from line 988-995 to line 1033, keeping the full `(incumbency, sims, districts, 2)` shape through all vote calculations and selecting the appropriate incumbency per district only when writing to JSON or calculating metrics.

## Changes Required

### 1. Remove early incumbency selection (planscore/score.py lines 988-995)
- **Delete** the current incumbency selection logic at lines 988-995
- Keep `model_output` with shape `(incumbency=3, sims, districts, 2)`
- Remove the `swing_vote_matrix()` call (will be applied later)

### 2. Update `vectorized_swing()` (planscore/score.py lines 138-170)
- **Make dimension-agnostic** to handle `(*leading_dims, districts, 2)` where `*leading_dims` could be any number of dimensions
- Update docstring: "Input array shape is (*leading_dims, districts, 2) where leading_dims can be any number of dimensions"
- Use negative indexing for reliable dimension handling:
  - `axis=-1` for the parties dimension (last axis)
  - `axis=-2` for the districts dimension (second to last axis)
- Change array indexing to use ellipsis: `swung_shares[..., 0]` and `swung_shares[..., 1]` instead of specific dimension counts
- This allows the function to work with current `(incumbency, sims, districts, 2)` and future shapes like `(extra_dim, incumbency, sims, districts, 2)`

### 3. Update `swing_vote_matrix()` (planscore/score.py lines 172-205)
- **Make dimension-agnostic** to handle `(*leading_dims, districts, 2)` input shape
- Update docstring: "Input array shape is (*leading_dims, districts, 2) where leading_dims can be any number of dimensions"
- Use `votes.shape[-2]` to get `district_count` (second to last dimension)
- Use `votes[..., i, :]` to extract district i across all leading dimensions
- Use `new_votes[..., i, 0]` and `new_votes[..., i, 1]` for assignment
- This preserves all leading dimensions automatically

### 4. Apply per-district vote swings (planscore/score.py after line 985)
- **NEW CODE**: Apply `swing_vote_matrix()` to the 4D model output
```python
# Apply per-district vote swings to all incumbency scenarios
model_output = swing_vote_matrix(model_output, upload.vote_swings)
# model_output shape remains (incumbency=3, sims, districts, 2)
```

### 5. Update swing expansion (planscore/score.py lines 1004-1010)
- Input: `model_output` with shape `(incumbency=3, sims, districts, 2)`
- Use ellipsis to preserve dimensions: `output_votes.reshape((1, *output_votes.shape))`
- After concatenation: `(swing_count=11, incumbency=3, sims, districts, 2)`

### 6. Update zero-swing extraction (planscore/score.py lines 1018-1020)
- Extract with updated indexing: `output_votes[zero_swing]`
- Result: `zero_swing_votes` with shape `(incumbency=3, sims, districts, 2)`

### 7. Update vote statistics calculations (planscore/score.py lines 1022-1028)
- Input: `zero_swing_votes` shape `(incumbency=3, sims, districts, 2)`
- Extract Dem/Rep votes: `dem_votes = zero_swing_votes[..., 0]` → `(incumbency, sims, districts)`
- Calculate means along sims axis: `numpy.nanmean(dem_votes, axis=1)` → `(incumbency, districts)`
- Calculate stds along sims axis: `numpy.nanstd(dem_votes, axis=1, ddof=1)` → `(incumbency, districts)`
- Calculate wins: `numpy.sum(dem_votes > rep_votes, axis=1) / sim_count` → `(incumbency, districts)`

### 8. Add incumbency selection at line 1033
- **NEW CODE** before the loop: Select appropriate incumbency per district
```python
# Select appropriate incumbency scenario per district for JSON output
selected_dem_votes_mean = numpy.array([dem_votes_mean[INCUMBENCY[inc], i] for i, inc in enumerate(upload.incumbents)])
selected_rep_votes_mean = numpy.array([rep_votes_mean[INCUMBENCY[inc], i] for i, inc in enumerate(upload.incumbents)])
selected_dem_votes_std = numpy.array([dem_votes_std[INCUMBENCY[inc], i] for i, inc in enumerate(upload.incumbents)])
selected_rep_votes_std = numpy.array([rep_votes_std[INCUMBENCY[inc], i] for i, inc in enumerate(upload.incumbents)])
selected_dem_wins = numpy.array([dem_wins[INCUMBENCY[inc], i] for i, inc in enumerate(upload.incumbents)])
```
- Update the loop to use `selected_*` arrays instead of directly indexing the `*_mean`, `*_std`, `*_wins` arrays

### 9. Add incumbency selection for metrics (planscore/score.py before line 1054)
- **NEW CODE**: Select appropriate incumbency per district from `zero_swing_votes`
```python
# Select appropriate incumbency scenario per district for metrics
selected_zero_swing_votes = numpy.zeros((sim_count, district_count, 2))
for i, incumbency in enumerate(upload.incumbents):
    idx = INCUMBENCY[incumbency]
    selected_zero_swing_votes[:, i, :] = zero_swing_votes[idx, :, i, :]
```
- Use `selected_zero_swing_votes` (shape `(sims, districts, 2)`) for MMD, PB, D2 calculations

### 10. Update EG calculations (planscore/score.py lines 1063-1066)
- For each swing scenario, select appropriate incumbency per district before passing to `vectorized_EG()`
```python
EGs = {}
for (i, swing) in enumerate(swing_range):
    # Select appropriate incumbency per district for this swing
    swing_votes = numpy.zeros((sim_count, district_count, 2))
    for j, incumbency in enumerate(upload.incumbents):
        idx = INCUMBENCY[incumbency]
        swing_votes[:, j, :] = output_votes[i, idx, :, j, :]
    EGs[swing] = vectorized_EG(swing_votes)
```

### 11. Update tests
- Test mocks remain with `(incumbency, sims, districts, 2)` shape
- No changes needed to test mocks since they already provide the full incumbency dimension
- May need to update some assertions if they check intermediate values

## Expected Shape Evolution
```
model_votes() → (3, sims, districts, 2)
                ↓ (NO selection yet)
swing_vote_matrix() → (3, sims, districts, 2)  [dimension-agnostic function]
                ↓
vectorized swings → (11, 3, sims, districts, 2)  [using dimension-agnostic function]
                ↓
extract zero-swing → (3, sims, districts, 2)
                ↓
calculate stats → (3, districts) for means/stds/wins
                ↓
SELECT at line 1033 → (districts,) for JSON
SELECT before metrics → (sims, districts, 2) for calculations
```

## Key Design Decisions
- **Dimension-agnostic vote functions**: Both `vectorized_swing()` and `swing_vote_matrix()` use negative indexing and ellipsis (`...`) to handle arbitrary leading dimensions, making them future-proof
- **Selection happens twice**: Once for JSON output (line 1033), once for metrics (line 1054)
- **per-district vote swings applied early**: Before swing expansion, so swings are preserved across all incumbency scenarios

## Testing Strategy
1. Run existing tests to ensure dimension-agnostic functions work correctly
2. Add test to verify `vectorized_swing()` works with 3D, 4D, and 5D inputs
3. Test with `planscore-score-locally` to verify end-to-end behavior
