# Plan: Add "source_district" Property to Track Original District Field Values

Based on commit 8ca2c0cc where district ordering was implemented, we need to track the original source field and values used for ordering districts.

---

## PHASE 1: Write Failing Unit Tests ✅ COMPLETED

### 1. Add tests to `planscore/tests/test_postread_calculate.py`

**Test 1: `test_put_district_geometries_with_census_field()`**
- Use existing `tl_2025_09_sldu.geojson` (has SLDUST="028", "029", etc.)
- Call `put_district_geometries()` and verify it returns `(keys, source_districts)`
- Assert `source_districts[0] == 'SLDUST="028"'` (first after sorting)
- Assert `source_districts[1] == 'SLDUST="029"'`

**Test 2: `test_put_district_geometries_with_numeric_field()`**
- Use existing `null-plan.geojson` (has numeric district field)
- Call `put_district_geometries()` and verify tuple return
- Assert source_districts contain proper format like `'District=1'`, `'District=2'`

**Test 3: `test_put_district_geometries_without_district_field()`**
- Use a test file with no valid district column
- Verify source_districts list contains None values

**Test 4: `test_put_district_assignments_returns_none_source_districts()`**
- Modify existing `test_put_district_assignments()`
- Verify it returns `(keys, source_districts)` where all source_districts are None

### 2. Add tests to `planscore/tests/test_data.py`

**Test 5: `test_upload_plaintext_with_source_district()`** (in `test_upload_plaintext()`)
- Create upload with districts that have `source_district` property
- Example: `{"totals": {...}, "compactness": {...}, "source_district": 'SLDUST="001"'}`
- Assert header includes: `'District\tSource District\tDemocratic Votes\t...'`
- Assert rows include source district values in correct position

**Test 6: `test_upload_plaintext_with_none_source_district()`**
- Create upload with `source_district=None` in districts
- Assert Source District column shows empty string

### Phase 1 Results

All 6 tests have been written and verified to fail:
- ✅ Test 1-3 added to `test_postread_calculate.py` - fail with "not enough values to unpack"
- ✅ Test 4 added to `test_postread_calculate.py` - fails with "not enough values to unpack"
- ✅ Test 5-6 added to `test_data.py` - fail with missing "Source District" column

---

## PHASE 2: Implementation Changes ✅ COMPLETED

### 3. Modify `planscore/postread_calculate.py:put_district_geometries()` (lines 260-330)

```python
def put_district_geometries(s3, bucket, upload, path):
    # ... existing code ...

    field_name, features = util.ordered_districts(ds.GetLayer(0))  # Line 277 change
    source_districts = []

    for (index, feature) in enumerate(features):
        # Extract source_district value before processing geometry
        if field_name:
            field_value = feature.GetField(field_name)
            source_district = f'{field_name}={json.dumps(field_value)}'
        else:
            source_district = None
        source_districts.append(source_district)

        # ... rest of existing geometry processing ...

    # ... existing code ...

    return keys, source_districts  # Changed from just 'keys'
```

### 4. Update `planscore/postread_calculate.py:commence_geometry_upload_scoring()` (lines 57-101)

```python
def commence_geometry_upload_scoring(s3, athena, bucket, upload, ds_path):
    # ... existing code ...
    keys, source_districts = put_district_geometries(...)  # Line 61 change

    # ... existing code through line 68 ...

    districts = observe.populate_compactness(geometries)  # Line 68

    # Add source_district to each district
    for i, district in enumerate(districts):
        district['source_district'] = source_districts[i]

    upload3 = upload2.clone(districts=districts)  # Line 69
    # ... rest unchanged ...
```

### 5. Update `planscore/postread_calculate.py:put_district_assignments()` (lines 332-396)

```python
def put_district_assignments(s3, bucket, upload, path):
    # ... existing code ...

    # Build source_districts list of None values (BAF files don't have field info)
    source_districts = [None] * len(keys)

    return keys, source_districts  # Changed from just 'keys'
```

### 6. Update `planscore/postread_calculate.py:commence_blockassign_upload_scoring()` (lines 103-150)

```python
def commence_blockassign_upload_scoring(context, s3, athena, bucket, upload, file_path):
    # ... existing code ...
    keys, source_districts = put_district_assignments(...)  # Line 107 change

    # ... existing code through line 117 ...

    districts = observe.populate_compactness(geometries)  # Line 117

    # Add source_district to each district
    for i, district in enumerate(districts):
        district['source_district'] = source_districts[i]

    upload4 = upload3.clone(districts=districts)  # Line 118
    # ... rest unchanged ...
```

### 7. Modify `planscore/data.py:to_plaintext()` (lines 293-327)

```python
def to_plaintext(self):
    # ... existing code through line 308 ...

    out = io.StringIO()
    rows = csv.DictWriter(out,
        ['District', 'Source District'] + extra_columns + column_names,  # Line 313 change
        dialect='excel-tab')
    rows.writeheader()
    for (index, district) in enumerate(self.districts):
        totals, compactness = district['totals'], district['compactness']
        extra_values = {'Candidate Scenario': self.incumbents[index]} if has_incumbency else {}
        rows.writerow(dict(
            District = district.get('number', index+1),
            **{'Source District': district.get('source_district', '')},  # New line
            **dict(totals, **dict(compactness, **extra_values)),
        ))
    # ... rest unchanged ...
```

---

## Expected Test Results

**Before implementation:** All 6 new tests fail
**After implementation:** All tests pass

**Output Examples:**
- Census text column: `'SLDUST="028"'`
- Census int column: `'CD119FP="01"'`
- Regular int column: `'District=1'`
- No field: `None` → empty string in plaintext

**index.json output:**
```json
{"districts": [
  {
    "source_district": "SLDUST=\"001\"",
    "totals": {...},
    "compactness": {...}
  }
]}
```

**index.txt output:**
```
District    Source District        Democratic Votes    ...
1           "SLDUST=""028"""       12345              ...
2           "SLDUST=""029"""       23456              ...
```

Note: CSV excel-tab dialect quotes fields containing quotes and doubles internal quotes per CSV spec.

---

## PHASE 3: Remove Extraneous district_number (PENDING)

### Issue

The `district_number` field (0-indexed array position) is completely redundant:

**Current structure in index.json:**
```json
{
  "number": 1,                          // User-facing district number (1, 2, 3...)
  "source_district": "SLDUST=\"028\"",  // Source field identifier (what we just added)
  "is_counted": true,
  "vote_swing": 0.0,
  "totals": {
    "district_number": 0,  // ← REDUNDANT: 0-indexed array position
    "Democratic Votes": 177750.84,
    ...
  },
  "compactness": {...}
}
```

### Why district_number is Redundant

1. **For display**: We use `number` (user-facing 1, 2, 3...)
2. **For source tracking**: We now have `source_district` (e.g., 'SLDUST="028"')
3. **For indexing**: Array iteration provides indices when needed
4. **Current usage**:
   - ❌ NOT used in plan.js (confirmed: not in FIELDS whitelist at lines 3-70)
   - ❌ NOT used in data.py:to_plaintext (uses `number` instead)
   - ❌ No other code references found
5. **Web UI impact**:
   - ✅ **Removing it will NOT change the Web UI** - it's not displayed
   - The Web UI only shows fields explicitly listed in the FIELDS array
   - `district_number` is not in that array, so it's already hidden
   - Dead code that just sits in the JSON

### Implementation Plan

**8. Modify `planscore/postread_calculate.py:commence_geometry_upload_scoring()` (lines 84-87)**

```python
def commence_geometry_upload_scoring(s3, athena, bucket, upload, ds_path):
    # ... existing code ...

    upload4 = upload3.clone(districts=[
        dict(totals=totals, **district)
        for (district, totals) in zip(districts, results)
    ])

    # Remove extraneous district_number from totals
    for district in upload4.districts:
        district['totals'].pop('district_number', None)

    # ... rest unchanged ...
```

**9. Modify `planscore/postread_calculate.py:commence_blockassign_upload_scoring()` (lines 138-141)**

```python
def commence_blockassign_upload_scoring(context, s3, athena, bucket, upload, file_path):
    # ... existing code ...

    upload5 = upload4.clone(districts=[
        dict(totals=totals, **district)
        for (district, totals) in zip(districts, results)
    ])

    # Remove extraneous district_number from totals
    for district in upload5.districts:
        district['totals'].pop('district_number', None)

    # ... rest unchanged ...
```

### Expected Result

**After Phase 3 index.json structure:**
```json
{
  "number": 1,                          // User-facing district number
  "source_district": "SLDUST=\"028\"",  // Source field identifier
  "is_counted": true,
  "vote_swing": 0.0,
  "totals": {
    "Democratic Votes": 177750.84,  // Only statistics here, no district_number
    ...
  },
  "compactness": {...}
}
```

### Testing

- Run full test suite to verify no breakage
- Check that `district_number` no longer appears as a column in web UI
- Verify index.json structure matches expected output
- Confirm no code actually depends on `district_number`
