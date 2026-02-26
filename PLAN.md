# Plan: Switch Scenario Keys from Integer to Combined String Format

## Problem Statement
Currently, scenario keys use only `model_year` (integer like `2024`). This doesn't distinguish between scenarios with the same model year but different presidential vote years (e.g., model 2025A uses pvote 2020, model 2025B uses pvote 2024). This causes incorrect presidential vote column selection in `update_heading_titles`.

## Solution
Change scenario keys from single integer to combined string format: `"{model_year} ({pvote_year})"` (e.g., `"2024 (2020)"`, `"2024 (2024)"`).

---

## Backend Changes (Python)

### 1. **planscore/score.py** - Line ~1164
**Current:**
```python
scenarios = dict(
    model_years=model_years,  # [2024, 2024]
    ...
)
```

**Change to:**
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

### 2. **planscore/tests/test_score.py**
- Update test assertions that check `scenarios['model_years']` to expect string format
- Verify string keys like `"2024 (2020)"` in test outputs
- Test backward compatibility for plans without 4D scenarios

---

## Frontend Changes (JavaScript)

### 3. **planscore/website/static/plan.js** - Add parsing helper function (after line 598)

```javascript
/**
 * Parse a scenario key in format "model_year (pvote_year)"
 * Returns {model_year: int, pvote_year: int} or null if not parseable
 * Handles both old integer format and new string format for compatibility
 */
function parse_scenario_key(key) {
    if (typeof key === 'number') {
        // Legacy integer format: use as both model_year and pvote_year
        return {model_year: key, pvote_year: key};
    }

    // New string format: "2024 (2020)"
    var match = String(key).match(/^(\d{4})\s*\((\d{4})\)$/);
    if (match) {
        return {
            model_year: parseInt(match[1]),
            pvote_year: parseInt(match[2])
        };
    }

    // Try simple integer string
    var year = parseInt(key);
    if (!isNaN(year)) {
        return {model_year: year, pvote_year: year};
    }

    return null;
}
```

### 4. **planscore/website/static/plan.js** - Update `create_scenario_plan` (line 631)

Add pvote_year extraction and pass it through to the returned plan:

```javascript
function create_scenario_plan(original_plan, scenarios, vote_swing, scenario_incumbents, model_year_idx) {
    // ... existing code ...

    // Extract pvote_year from scenario key if available
    var pvote_year = original_plan.pvote_year; // default
    if (is_4d_scenarios(scenarios) && scenarios.model_years[model_year_idx]) {
        var parsed = parse_scenario_key(scenarios.model_years[model_year_idx]);
        if (parsed) {
            pvote_year = parsed.pvote_year;
        }
    }

    // ... create mutated_plan ...

    // Add pvote_year to mutated plan so update_heading_titles can use it
    mutated_plan.pvote_year = pvote_year;

    return mutated_plan;
}
```

### 5. **planscore/website/static/plan.js** - Update radio button setup (lines 1254-1284)

Change integer matching to string matching with model_year extraction:

```javascript
// First pass: uncheck all and show/hide based on availability
for (var i = 0; i < radio_buttons.length; i++) {
    var radio_year = parseInt(radio_buttons[i].value);
    var radio_label = radio_buttons[i].parentElement;

    radio_buttons[i].checked = false;

    // Find if this radio_year matches any scenario key
    var found = false;
    var label_text = String(radio_year);

    for (var j = 0; j < scenarios.model_years.length; j++) {
        var parsed = parse_scenario_key(scenarios.model_years[j]);
        if (parsed && parsed.model_year === radio_year) {
            found = true;
            // Use full scenario key as label if multiple scenarios for same model_year
            var count_same_year = scenarios.model_years.filter(function(k) {
                var p = parse_scenario_key(k);
                return p && p.model_year === radio_year;
            }).length;

            if (count_same_year > 1) {
                label_text = scenarios.model_years[j];
            }
            break;
        }
    }

    if (found) {
        radio_label.style.display = '';
        // Update label text to show full scenario key if needed
        var label_span = radio_label.childNodes[1]; // text after input
        if (label_span) {
            label_span.nodeValue = ' ' + label_text;
        }
    } else {
        radio_label.style.display = 'none';
    }
}
```

### 6. **planscore/website/static/plan.js** - Update `get_selected_model_year_idx` (lines 1122-1137)

Match by model_year extracted from scenario keys:

```javascript
function get_selected_model_year_idx() {
    var checked_radio = scenario_adjustments_form.querySelector('input[name="model-year"]:checked');
    if (!checked_radio) {
        return 0;
    }

    if (is_4d_scenarios(scenarios)) {
        var selected_year = parseInt(checked_radio.value);

        // Find index where model_year matches
        for (var i = 0; i < scenarios.model_years.length; i++) {
            var parsed = parse_scenario_key(scenarios.model_years[i]);
            if (parsed && parsed.model_year === selected_year) {
                return i;
            }
        }
    }

    return 0;
}
```

### 7. **planscore/website/static/plan.js** - Update hash parsing (lines 975-979)

Parse model_year from hash and match against scenario keys:

```javascript
// Look for model_year parameter
var model_year_match = hash.match(/model_year:(\d+)/);
if (model_year_match) {
    result.model_year = parseInt(model_year_match[1]);
}

// NEW: Also try parsing full scenario key format
var scenario_key_match = hash.match(/model_year:(\d{4})\s*\((\d{4})\)/);
if (scenario_key_match) {
    result.model_year = parseInt(scenario_key_match[1]);
    result.pvote_year = parseInt(scenario_key_match[2]);
}
```

### 8. **planscore/website/static/plan.js** - Update hash encoding (lines 1000-1004)

Encode full scenario key in hash:

```javascript
// Add model_year if it's a 4D scenario and not the default (index 0)
if (scenarios && is_4d_scenarios(scenarios) && model_year_idx > 0) {
    var scenario_key = scenarios.model_years[model_year_idx];
    parts.push('model_year:' + encodeURIComponent(scenario_key));
}
```

---

## Testing

### 9. **Python tests** - Update test_score.py
- Find tests checking `scenarios['model_years']` format
- Update assertions to expect string format: `["2024 (2020)", "2024 (2024)"]`
- Add test for backward compatibility (3D scenarios without model_years)

### 10. **JavaScript tests** - Update tests.js
- Test `parse_scenario_key()` with various inputs:
  - `"2024 (2020)"` → `{model_year: 2024, pvote_year: 2020}`
  - `2024` (integer) → `{model_year: 2024, pvote_year: 2024}`
  - Invalid strings → `null`
- Test `create_scenario_plan` correctly sets pvote_year
- Test radio button matching logic

---

## Backward Compatibility Strategy

1. **Old plans without model_year dimension (3D scenarios)**: No changes needed - they don't use model_years array
2. **Plans with pvote_year but no model_year**: Will continue to work as plan.pvote_year is unchanged
3. **New plans with 4D scenarios**: Will use combined string format
4. **Parser handles both formats**: `parse_scenario_key()` accepts both integers and strings for robustness

---

## Success Criteria

✓ Scenario keys combine model_year and pvote_year: `"2024 (2020)"`
✓ Radio buttons show correct labels when multiple scenarios exist for same model year
✓ `update_heading_titles` receives correct pvote_year from selected scenario
✓ Presidential vote columns display correct year (e.g., 2020 data for model 2025A)
✓ URL hash correctly encodes/decodes scenario keys
✓ All Python tests pass
✓ All JavaScript tests pass
✓ Backward compatibility maintained for plans without 4D scenarios
