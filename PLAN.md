# Refactoring Plan: Making Plan Scores Interactive with Scenarios

## Overview

This document outlines opportunities to refactor `plan.js:on_loaded_score()` to support interactive scenario updates. Currently, the code constructs DOM elements and populates them with data in a single pass. To enable interactive updates based on vote swing scenarios, we need to separate construction from population.

## Current Architecture Analysis

### Location: `planscore/website/static/plan.js:1613-1817`

The `on_loaded_score()` function performs one-shot rendering by mixing:
- **Document construction**: Creating DOM elements, building HTML structures
- **Document population**: Setting numeric values, vote counts, percentages

### Key Code Sections

#### 1. Description Area (lines 1636-1669)
```javascript
// Intermingles construction and population
const desc_el = document.createElement('h1');
desc_el.textContent = plan.description;  // Population happens immediately
description_el.append(desc_el);
```
- Creates info boxes dynamically
- Immediately sets state, legislative house, date values
- **Impact**: Low priority for scenarios (metadata doesn't change)

#### 2. Districts Table (lines 1684-1758)
```javascript
// Builds HTML string with structure AND data
tags = ['<thead>', '<tr>'];
for(var j = 0; j < table_array[0].length; j++) {
    tags = tags.concat([`<th>`, headingTitle, '</th>']);
}
// Later: adds data rows with vote counts
tags = tags.concat([`<td>`, value, '</td>']);
districts_table.innerHTML = tags.join('');
```
- Constructs entire table as HTML string
- Embeds vote counts, district numbers directly
- Sets `innerHTML` once with complete table
- **Impact**: **HIGHEST PRIORITY** - This table contains all the scenario-dependent data

#### 3. Score Cards (lines 1778-1807)
```javascript
show_efficiency_gap_score(plan, score_EG);
show_sensitivity_test(plan, score_sense);
show_partisan_bias_score(plan, score_PB);
show_mean_median_score(plan, score_MM);
```

Each `show_*` function (defined earlier in the file):
- Modifies `innerHTML` on H3 headers to add numeric values
- Calls `drawBiasBellChart()` to create SVG visualizations
- Updates paragraph descriptions with computed text
- **Impact**: **HIGH PRIORITY** - All metrics change with scenarios

#### 4. Metrics Table (line 1806)
```javascript
show_metrics_table(plan, metrics_table);
```
- Similar to districts table
- Builds structure and populates in one operation
- **Impact**: **HIGH PRIORITY** - Summary statistics change with scenarios

#### 5. Seatshare Graphic (line 1759)
```javascript
show_seatshare_graphic(plan, districts_table);
```
- Creates colored span elements for seat visualization
- **Impact**: **MEDIUM PRIORITY** - Visual representation of outcomes

## Data Structure Support

### Scenarios File: `data/sample-NC2025/scenarios.json`

The scenarios data is well-structured for interactive updates:

```json
{
  "dimensions": ["vote_swings", "incumbents", "districts"],
  "vote_swings": [-6.0, -5.5, -5.0, ..., 5.0, 5.5, 6.0],
  "incumbents": ["O", "D", "R", "U"],
  "statistics": {
    "Democratic Votes": [
      // [vote_swing_index][incumbency_index][district_index]
      [[158295.3, 241891.84, ...], ...]
    ],
    "Democratic Votes SD": [...],
    "Democratic Wins": [...],
    "Republican Votes": [...],
    "Republican Votes SD": [...]
  }
}
```

**Key observations**:
- 25 vote swing scenarios from -6% to +6%
- 4 incumbency scenarios (Open, Democrat, Republican, Uncertain)
- 14 districts in the NC example
- Pre-computed statistics for all combinations

### Vote Swing Form: `plan.html:36-62`

Radio button form already exists:
```html
<form id="scenario-adjustments">
    <input type="radio" name="vote-swing" value="-6.0"> D+6.0
    <input type="radio" name="vote-swing" value="0.0"> 0.0
    <input type="radio" name="vote-swing" value="6.0"> R+6.0
</form>
```

## Refactoring Opportunities

### 1. Districts Table (HIGHEST PRIORITY)

**Current State**: Lines 1684-1758 build complete HTML string

**Refactoring Strategy**:

**Construction Phase** (run once on load):
```javascript
function construct_districts_table(plan) {
  const table = document.createElement('table');
  const thead = document.createElement('thead');
  const tbody = document.createElement('tbody');

  // Build header row with column names
  const headerRow = document.createElement('tr');
  const columns = get_table_columns(plan);
  columns.forEach(col => {
    const th = document.createElement('th');
    th.textContent = col.name;
    th.dataset.field = col.field;
    headerRow.appendChild(th);
  });
  thead.appendChild(headerRow);

  // Build data rows with empty cells
  plan.districts.forEach((district, i) => {
    const row = document.createElement('tr');
    row.dataset.district = i;
    row.className = district.is_counted ? 'has-votes' : 'no-votes';

    columns.forEach(col => {
      const cell = document.createElement(col.field === 'number' ? 'th' : 'td');
      cell.dataset.field = col.field;
      row.appendChild(cell);
    });
    tbody.appendChild(row);
  });

  table.appendChild(thead);
  table.appendChild(tbody);
  districts_table.appendChild(table);
}
```

**Population Phase** (run on scenario change):
```javascript
function populate_districts_table(plan, scenario_data) {
  const rows = districts_table.querySelectorAll('tbody tr');

  rows.forEach((row, i) => {
    const district = scenario_data.districts[i];

    // Update each cell with new values
    row.querySelectorAll('td, th').forEach(cell => {
      const field = cell.dataset.field;
      const value = get_district_value(district, field);
      cell.textContent = format_value(value, field);
    });

    // Update row styling if needed
    row.className = district.is_counted ? 'has-votes' : 'no-votes';
  });
}
```

**Benefits**:
- DOM structure persists across updates
- Only text content changes (very fast)
- Row/cell references stable for event handlers
- Enables smooth transitions/animations

### 2. Score Cards (HIGH PRIORITY)

**Current State**: Functions like `show_efficiency_gap_score()` modify innerHTML and create charts

**Refactoring Strategy**:

**Construction Phase**:
```javascript
function construct_score_cards() {
  // Efficiency Gap
  construct_score_card(score_EG, {
    metric: 'eg',
    title: 'Efficiency Gap',
    hasChart: true,
    hasDescription: true
  });

  // Partisan Bias
  construct_score_card(score_PB, {
    metric: 'pb',
    title: 'Partisan Bias',
    hasChart: true,
    hasDescription: true
  });

  // Mean-Median
  construct_score_card(score_MM, {
    metric: 'mm',
    title: 'Mean-Median Difference',
    hasChart: true,
    hasDescription: true
  });

  // Declination
  construct_score_card(score_DEC2, {
    metric: 'd2',
    title: 'Declination',
    hasChart: true,
    hasDescription: true
  });
}

function construct_score_card(element, config) {
  // Find H3 and add data attribute
  const h3 = element.querySelector('h3');
  h3.dataset.metric = config.metric;

  // Add span for value
  const valueSpan = document.createElement('span');
  valueSpan.className = 'metric-value';
  valueSpan.dataset.metric = config.metric;
  h3.appendChild(document.createTextNode(': '));
  h3.appendChild(valueSpan);

  // Store chart reference
  if (config.hasChart) {
    element.dataset.hasChart = 'true';
  }

  // Mark description paragraph
  if (config.hasDescription) {
    const p = element.querySelector('p');
    p.dataset.metric = config.metric;
  }
}
```

**Population Phase**:
```javascript
function populate_score_cards(plan, summary_data) {
  // Update Efficiency Gap
  const egGap = summary_data['Efficiency Gap'];
  update_score_card(score_EG, 'eg', egGap, plan);

  // Update other metrics...
}

function update_score_card(element, metric, value, plan) {
  // Update value in header
  const valueSpan = element.querySelector(`span[data-metric="${metric}"]`);
  valueSpan.textContent = nice_percent(Math.abs(value)) + partisan_suffix(value);

  // Update chart without recreating
  if (element.dataset.hasChart === 'true') {
    const chartDiv = element.querySelector('.metric-bellchart');
    update_bell_chart(metric, value, chartDiv.id);
  }

  // Update description text
  const p = element.querySelector(`p[data-metric="${metric}"]`);
  p.innerHTML = generate_description_text(metric, value, plan);
}

function update_bell_chart(metric, value, chartId) {
  // Instead of recreating, update existing chart
  const chart = Highcharts.charts.find(c => c && c.renderTo.id === chartId);
  if (chart) {
    // Update marker position
    chart.series[1].setData([{x: value, y: ...}]);
  } else {
    // First time: create chart
    drawBiasBellChart(metric, value, chartId, ...);
  }
}
```

**Benefits**:
- Avoid full innerHTML replacement
- Chart updates instead of recreation (smoother)
- Consistent DOM structure
- Easier to add transitions

### 3. Sensitivity Chart (MEDIUM PRIORITY)

**Current State**: `show_sensitivity_test()` creates Highcharts chart with data

**Refactoring Strategy**:

**Construction Phase**:
```javascript
function construct_sensitivity_chart(element) {
  // Create chart structure with empty data
  const chart = Highcharts.chart(element, {
    chart: { type: 'line' },
    legend: { enabled: false },
    credits: { enabled: false },
    title: { text: null },
    series: [{
      name: 'Expected Efficiency Gap',
      data: [] // Empty initially
    }],
    xAxis: {
      categories: ['+5 D', '+4 D', '+3 D', '+2 D', '+1 D',
                   '0', '+1 R', '+2 R', '+3 R', '+4 R', '+5 R'],
      title: { text: 'Possible Vote Swing' }
    },
    yAxis: {
      title: { text: null },
      labels: {
        formatter: function() {
          return this.value.toFixed(0) + '%';
        }
      }
    }
  });

  // Store chart reference
  element._highchartsChart = chart;
}
```

**Population Phase**:
```javascript
function populate_sensitivity_chart(element, summary_data) {
  const chart = element._highchartsChart;

  const newData = [
    100 * summary_data['Efficiency Gap +5 Dem'],
    100 * summary_data['Efficiency Gap +4 Dem'],
    100 * summary_data['Efficiency Gap +3 Dem'],
    100 * summary_data['Efficiency Gap +2 Dem'],
    100 * summary_data['Efficiency Gap +1 Dem'],
    100 * summary_data['Efficiency Gap'],
    100 * summary_data['Efficiency Gap +1 Rep'],
    100 * summary_data['Efficiency Gap +2 Rep'],
    100 * summary_data['Efficiency Gap +3 Rep'],
    100 * summary_data['Efficiency Gap +4 Rep'],
    100 * summary_data['Efficiency Gap +5 Rep']
  ];

  // Update data without redrawing entire chart
  chart.series[0].setData(newData, true);
}
```

**Benefits**:
- Smooth data transitions
- Preserved chart interactivity
- Better performance

### 4. Seatshare Graphic (MEDIUM PRIORITY)

**Current State**: `show_seatshare_graphic()` (lines 407-458) builds HTML spans

**Refactoring Strategy**:

**Option A: Maintain Span Approach**
```javascript
function construct_seatshare_graphic(plan) {
  const container = document.createElement('div');
  container.className = 'seatshare-container';

  plan.districts.forEach((district, i) => {
    const span = document.createElement('span');
    span.className = 'seatshare-box';
    span.dataset.district = i;
    container.appendChild(span);
  });

  districts_table.parentNode.insertBefore(container, districts_table.nextSibling);
}

function populate_seatshare_graphic(seatshare_array) {
  const boxes = document.querySelectorAll('.seatshare-box');

  boxes.forEach((box, i) => {
    const color = seatshare_array.colors[i];
    box.style.backgroundColor = color;

    if (color === LEAN_BLUE_COLOR_HEX) {
      box.style.backgroundImage = 'url("/static/lean-blue-pattern.png")';
    } else if (color === LEAN_RED_COLOR_HEX) {
      box.style.backgroundImage = 'url("/static/lean-red-pattern.png")';
    }
  });
}
```

**Option B: SVG Approach** (cleaner for animations)
```javascript
function construct_seatshare_svg(plan) {
  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  svg.setAttribute('viewBox', '0 0 100 10');
  svg.setAttribute('preserveAspectRatio', 'none');

  const seatWidth = 100 / plan.districts.length;

  plan.districts.forEach((district, i) => {
    const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
    rect.setAttribute('x', i * seatWidth);
    rect.setAttribute('y', 0);
    rect.setAttribute('width', seatWidth);
    rect.setAttribute('height', 10);
    rect.dataset.district = i;
    svg.appendChild(rect);
  });

  return svg;
}

function populate_seatshare_svg(seatshare_array) {
  const rects = document.querySelectorAll('svg rect');

  rects.forEach((rect, i) => {
    const color = seatshare_array.colors[i];
    rect.setAttribute('fill', color);
    // Can add transition CSS for smooth color changes
  });
}
```

### 5. Description/Info Boxes (LOWER PRIORITY)

**Current State**: Lines 1636-1669 create description and info boxes

**Analysis**:
- State, legislative house, and upload date are **scenario-independent**
- These values come from `plan.model` which doesn't change
- Reconstruction on scenario change is unnecessary but also harmless

**Recommendation**:
- Leave as-is initially
- If needed, cache the constructed elements and skip reconstruction
- Very low impact on performance

## Recommended Implementation Strategy

### Phase 1: Refactor Districts Table ✅ COMPLETED

**Status**: Completed 2026-02-17

**What was done**:
1. Created `construct_districts_table(plan)` function (lines 1613-1695):
   - Builds DOM structure using createElement APIs
   - Creates thead with column headers from plan_array()
   - Creates tbody with rows and cells for each district
   - Attaches data-* attributes (districtIndex, columnIndex) for identification
   - Sets table classes ('table', 'table-hover') and id ('districts')
   - Uses innerHTML for headers to support HTML tags like `<sup>`

2. Created `populate_districts_table(plan)` function (lines 1697-1774):
   - Queries existing cells by data attributes
   - Fills in values using existing formatters (nice_count, nice_string)
   - Sets row classes ('has-votes', 'no-votes') and titles
   - Uses innerHTML for string values to handle HTML entities from nice_string()
   - Uses textContent for numbers and other values

3. Updated `on_loaded_score()` (line 1841-1843):
   - Replaced 74 lines of HTML string building code with two function calls
   - Maintains identical visual output and behavior

**Benefits achieved**:
- Clear separation of construction from population
- Foundation for future scenarios: construction runs once, population can run multiple times
- More maintainable code with modern DOM APIs
- All existing tests pass

### Phase 2: Refactor All Display Components ✅ COMPLETED

**Status**: Completed 2026-02-17

**What was done**:
Refactored all remaining display functions in `on_loaded_score()` between the districts table (line 1852) and the map (line 1909) to separate DOM construction from data population.

1. **Seatshare Graphic** (lines 459-547):
   - `construct_seatshare_graphic(plan, districts_table)` - Creates span elements and text container
   - `populate_seatshare_graphic(plan)` - Updates colors, widths, and seat share text

2. **Score Cards** - All follow same pattern of adding data attributes during construction, updating values during population:
   - **Efficiency Gap** (lines 598-673): `construct_efficiency_gap_score()` / `populate_efficiency_gap_score()`
   - **Declination** (lines 716-783): `construct_declination2_score()` / `populate_declination2_score()`
   - **Partisan Bias** (lines 832-905): `construct_partisan_bias_score()` / `populate_partisan_bias_score()`
   - **Mean-Median** (lines 969-1042): `construct_mean_median_score()` / `populate_mean_median_score()`

3. **Sensitivity Test Chart** (lines 1093-1157):
   - `construct_sensitivity_test(score_sense)` - Creates Highcharts structure with empty data
   - `populate_sensitivity_test(plan, score_sense)` - Uses `.setData()` to update chart without recreation

4. **Metrics Table** (lines 1327-1498):
   - `construct_metrics_table(metrics_table)` - Builds complete table structure using createElement
   - `populate_metrics_table(plan, metrics_table)` - Updates cell values, handles conditional columns/rows

5. **FTVA Race Scores** (lines 1732-1800):
   - `construct_ftva_race_scores(scores_FTVA)` - Marks elements for population
   - `populate_ftva_race_scores(plan, scores_FTVA)` - Updates race-specific efficiency gap data

6. **Library Metadata** (lines 1565-1641):
   - `construct_library_metadata(metadata_el)` - Marks existing HTML structure
   - `populate_library_metadata(plan, metadata_el, geom_prefix)` - Populates links and notes

7. **Updated `on_loaded_score()`** (lines 2623-2692):
   - Replaced all `show_*()` calls with paired `construct_*()` and `populate_*()` calls
   - Maintains identical visual output and behavior

**Fixes applied**:
- Changed `.textContent` to `.innerHTML` for score values containing HTML entities from `partisan_suffix()` to prevent `&nbsp;` from appearing as literal text

**Benefits achieved**:
- All display functions now follow consistent construct/populate pattern
- DOM structures persist across updates (ready for scenarios)
- Construction runs once, population can run multiple times
- All existing tests pass
- Foundation complete for interactive scenario updates

### Phase 3: Scenario Infrastructure (NEXT)
1. **Add scenario state management**
   ```javascript
   const ScenarioManager = {
     currentScenarioIndex: 12, // 0.0 vote swing
     scenariosData: null,

     load(scenariosUrl) {
       // Load scenarios.json
     },

     getScenarioData(voteSwing) {
       // Return adjusted plan object for given swing
     },

     setScenario(index) {
       // Update current scenario and trigger updates
     }
   };
   ```

2. **Wire up radio buttons**
   ```javascript
   function init_scenario_controls() {
     const form = document.getElementById('scenario-adjustments');
     const radios = form.querySelectorAll('input[name="vote-swing"]');

     radios.forEach(radio => {
       radio.addEventListener('change', (e) => {
         const voteSwing = parseFloat(e.target.value);
         const scenarioIndex = ScenarioManager.getIndexForVoteSwing(voteSwing);
         ScenarioManager.setScenario(scenarioIndex);
         updateAllDisplays();
       });
     });
   }
   ```

3. **Create data adjustment function**
   ```javascript
   function adjust_scenario_stats(plan, scenariosData, voteSwingIndex) {
     // Take base plan and overlay scenario statistics
     const adjustedPlan = JSON.parse(JSON.stringify(plan));

     // Update district totals
     adjustedPlan.districts.forEach((district, i) => {
       district.totals['Democratic Votes'] =
         scenariosData.statistics['Democratic Votes'][voteSwingIndex][0][i];
       district.totals['Republican Votes'] =
         scenariosData.statistics['Republican Votes'][voteSwingIndex][0][i];
       // ... other fields
     });

     // Recalculate summary statistics
     adjustedPlan.summary = calculate_summary_from_districts(adjustedPlan.districts);

     return adjustedPlan;
   }
   ```

4. **Test scenario switching with all components**
   - Call all `populate_*()` functions with adjusted plan data
   - Verify all values update correctly
   - Test performance (target < 100ms)

### Phase 4: Polish
1. Add loading states during scenario switches
2. Add transitions/animations for value changes
3. Update URL hash to preserve scenario selection
4. Add keyboard shortcuts for scenario navigation

## Code Organization

Current file structure:

```
plan.js
├── Scenario Management
│   ├── load_plan_scenarios() [existing]
│   └── adjust_scenario_stats() [existing stub]
│
├── Construction Functions (run once) ✅ IMPLEMENTED
│   ├── construct_districts_table()
│   ├── construct_seatshare_graphic()
│   ├── construct_efficiency_gap_score()
│   ├── construct_declination2_score()
│   ├── construct_partisan_bias_score()
│   ├── construct_mean_median_score()
│   ├── construct_sensitivity_test()
│   ├── construct_metrics_table()
│   ├── construct_ftva_race_scores()
│   └── construct_library_metadata()
│
├── Population Functions (run on updates) ✅ IMPLEMENTED
│   ├── populate_districts_table()
│   ├── populate_seatshare_graphic()
│   ├── populate_efficiency_gap_score()
│   ├── populate_declination2_score()
│   ├── populate_partisan_bias_score()
│   ├── populate_mean_median_score()
│   ├── populate_sensitivity_test()
│   ├── populate_metrics_table()
│   ├── populate_ftva_race_scores()
│   └── populate_library_metadata()
│
└── Existing Functions
    ├── on_loaded_score() [refactored to use construct/populate pattern]
    ├── show_*_score() [kept for reference, still functional]
    └── utility functions
```

## Testing Strategy

1. **Unit tests** for data transformation:
   - `adjust_scenario_stats()` produces correct values
   - Scenario index calculation correct

2. **Integration tests** for rendering:
   - Initial load matches current behavior
   - Scenario switch updates all displays
   - Multiple switches work correctly

3. **Performance tests**:
   - Measure time for scenario switch
   - Target: < 100ms for smooth UX
   - Compare construction vs. population approaches

4. **Browser compatibility**:
   - Test in Chrome, Firefox, Safari
   - Test on mobile devices

## Migration Path

To avoid breaking existing functionality:

1. **Create new functions alongside old ones**
   - `construct_districts_table()` alongside existing code
   - `populate_districts_table()` as new function

2. **Add feature flag**
   ```javascript
   const USE_INTERACTIVE_SCENARIOS =
     location.hash.includes('interactive') ||
     plan.scenarios !== undefined;
   ```

3. **Conditional logic in `on_loaded_score()`**
   ```javascript
   if (USE_INTERACTIVE_SCENARIOS) {
     construct_districts_table(plan);
     populate_districts_table(plan, initialScenario);
   } else {
     // Existing code
     tags = ['<thead>', '<tr>'];
     // ...
   }
   ```

4. **Gradual migration**
   - Start with districts table
   - Add score cards
   - Add remaining components
   - Remove feature flag once stable

## Success Metrics

- [ ] User can switch between vote swing scenarios
- [ ] All metrics update within 100ms
- [ ] No visual flicker or layout shift
- [ ] Works in all supported browsers
- [ ] Code is more maintainable (construction/population separate)
- [ ] No regression in initial page load time

## Next Steps

1. Review this plan with team
2. Create GitHub issues for each phase
3. Set up test environment with sample data
4. Begin Phase 1 implementation
5. Iterate based on testing feedback
