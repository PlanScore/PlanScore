# Plan: Remove calculate_EG() and its tests

User request: "In ~/Sites/PlanScore/planscore/score.py I want to get rid of calculate_EG() and its tests because we have vectorized_EG(). Plan that."

## Current state

- `calculate_EG()` exists at planscore/score.py:430-460
- `vectorized_EG()` exists at planscore/score.py:462-537 and is the modern replacement
- `calculate_EG()` is used in `calculate_fva_biases()` at line 1112
- Two test methods exist:
  - `test_calculate_EG_fair()` at planscore/tests/test_score.py:375-395
  - `test_calculate_EG_unfair()` at planscore/tests/test_score.py:451-464

## Steps

1. **Remove calculate_EG() function** from planscore/score.py (lines 430-460)

2. **Replace calculate_EG() usage in calculate_fva_biases()** (line 1112)
   - Convert list inputs to numpy array format
   - Call vectorized_EG() instead
   - Extract scalar result from returned array

3. **Remove test_calculate_EG_fair()** from planscore/tests/test_score.py (lines 375-395)

4. **Remove test_calculate_EG_unfair()** from planscore/tests/test_score.py (lines 451-464)

Note: `test_vectorized_EG_fair()` and `test_vectorized_EG_unfair()` already exist and provide comprehensive test coverage, so no new tests are needed.
