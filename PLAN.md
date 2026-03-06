# Plan: Implement Logit Shift for Vote Swings

## Background

Currently, `planscore/score.py` uses `vectorized_swing()` to apply uniform vote shifts across all districts. This means every district gets the same percentage point shift (e.g., +2% for Democrats, -2% for Republicans).

However, real electoral swings tend to follow logit (log-odds) patterns, where districts with different baseline partisanship respond differently to national trends. This is more realistic and is already implemented in `~/Sites/PlanScore-FrontPage/update-ushouse-vote-swings.py`.

## Analysis of calculate_district_shifts()

The existing function in `update-ushouse-vote-swings.py` (lines 66-107):
- Uses scipy's `expit()` (logistic sigmoid) and `root_scalar()` with Brent's method
- Transforms vote shares to log-odds space
- Finds a shift parameter that achieves a target national vote share
- Applies per-district shifts based on each district's log-odds

### Mathematical Properties

The objective function has excellent properties:
1. **Strictly monotonic**: Weighted average of expit(log_odds + shift) increases monotonically with shift
2. **Bounded**: Output is between 0 and 1 (weighted average of probabilities)
3. **Smooth and differentiable**: Logistic function is infinitely differentiable
4. **Known derivative**: d/dx expit(x) = expit(x) * (1 - expit(x))

These properties make this an ideal case for simple bisection - no need for fancy root-finding.

## Implementation Strategy

### Phase 1: Numpy-only Implementation (No scipy)

Replace scipy dependencies with simple implementations:

1. **expit(x)**: Replace with `1.0 / (1.0 + numpy.exp(-x))`
   - Add clipping to avoid overflow: `numpy.clip(x, -20, 20)`

2. **root_scalar()**: Replace with simple bisection
   - Start with bracket `[-10.0, 10.0]`
   - Tolerance: `1e-6`
   - Maximum ~24 iterations needed
   - Guaranteed convergence due to monotonicity

### Phase 2: Adapt to vectorized_swing() Pattern

The function needs to match the API of `vectorized_swing()`:
- **Input**: `(leading_dims, districts, 2)` array where `leading_dims` can be any number of dimensions
- **Convention**: `votes[..., 0]` = blue/Democratic, `votes[..., 1]` = red/Republican
- **Output**: Same shape array with shifted votes

### Implementation Approach

```python
def vectorized_logit_shift(votes, target_diff):
    '''
    Apply logit-based vote shift to achieve target national swing.

    Unlike vectorized_swing() which applies uniform shifts, this calculates
    per-district shifts using log-odds transformation to better model real
    electoral swing patterns.
    '''
    # 1. Flatten leading dimensions to (N, districts, 2)
    # 2. Loop over N scenarios (each model_version × incumbency × simulation)
    # 3. For each scenario:
    #    a. Calculate current national vote share
    #    b. Use bisection to find shift parameter
    #    c. Apply per-district shifts based on log-odds
    # 4. Reshape back to original dimensions
```

### Performance Considerations

**Current Implementation (Non-optimized)**:
- Nested loops: 25 swings × ~40,000 scenarios × ~24 bisection iterations
- Python loops are slow but acceptable for initial implementation
- Focus on correctness first

**Future Optimizations** (if needed):
1. Vectorize bisection across all scenarios simultaneously
2. Cache results for similar vote patterns
3. Use multiprocessing for swing loop
4. Consider approximate solutions for real-time use cases

## Integration Plan

### Location: planscore/score.py lines 1141-1150

Current code:
```python
all_votes = numpy.concatenate(
    [vectorized_swing(model_output, a/100).reshape(
        (model_output.shape[0], 1, *model_output.shape[1:])
    ) for a in swing_range],
    axis=1,
)
```

Replace with:
```python
all_votes = numpy.concatenate(
    [vectorized_logit_shift(model_output, a/100).reshape(
        (model_output.shape[0], 1, *model_output.shape[1:])
    ) for a in swing_range],
    axis=1,
)
```

### Testing

Run `python setup.py test` and verify:
- Tests pass with minor adjustments to expected swing values
- Results are mathematically sound
- No NaN or inf values
- Shifts sum to approximately zero per scenario

## Key Differences from Uniform Swing

1. **Per-district variation**: Districts shift by different amounts based on baseline partisanship
2. **More realistic**: Matches empirical patterns from real elections
3. **Preserves log-odds structure**: Competitive districts tend to swing more than safe districts
4. **Computational cost**: More expensive but more accurate

## Questions to Address

1. Should we keep both methods and make it configurable?
2. What tolerance should we use for bisection? (proposed: 1e-6)
3. Should we add validation/warnings for edge cases?
4. Do we need to preserve backward compatibility with existing test expectations?
