# Remove source_district Concept Completely

## Overview
Simplify block assignment file generation by removing all source_district tracking. The CSV will have only 4 columns instead of 5. This makes the implementation cleaner and easier to merge with the other branch later.

## Changes to `planscore/postread_calculate.py`:

### 1. **`put_district_geometries()` function** (lines 341-419)
- **Remove lines 359, 362-368**: Delete `source_districts` list and all tracking code
- **Update line 419**: Change `return keys, source_districts` to `return keys`
- Result: Function returns just `keys` (not a tuple)

### 2. **`commence_geometry_upload_scoring()` function** (lines 57-111)
- **Update line 61**: Change `keys, source_districts = put_district_geometries(...)` to `put_district_geometries(...)`
- **Remove lines 70-72**: Delete loop that adds `source_district` to each district dict
- Result: No source_district tracking in geometry upload workflow

### 3. **`generate_block_assignment_file()` function** (lines 227-306)
- **Remove lines 265-269**: Delete `source_district_map` dictionary comprehension
- **Update line 276**: Change CSV header from `['district_number', 'source_district', 'geoid20', 'intpt_lon', 'intpt_lat']` to `['district_number', 'geoid20', 'intpt_lon', 'intpt_lat']`
- **Update lines 280-286**: Change CSV row from 5 columns to 4 columns, removing `source_district_map.get(...)` line
- Result: CSV file has only 4 columns

## Changes to `planscore/tests/test_postread_calculate.py`:

### 4. **Update 4 existing tests to not unpack tuple** (lines 75, 91, 107, 123)
- Change: `keys, source_districts = postread_calculate.put_district_geometries(...)`
- To: `keys = postread_calculate.put_district_geometries(...)`

### 5. **Remove test_put_district_geometries_tracks_source_district** (lines ~760-770)
- Delete entire test - no longer relevant

### 6. **Remove test_generate_block_assignment_file_blank_source_district** (lines ~676-715)
- Delete entire test - no longer relevant

### 7. **Update test_generate_block_assignment_file_spatial_join** (lines ~559-615)
- Remove `source_district` from mock districts (lines 590-591)
- Update CSV header assertion (line 618) to check 4 columns instead of 5
- Update CSV content assertion (line 619) to check 4 columns

### 8. **Update test_generate_block_assignment_file_csv_format** (lines ~617-675)
- Remove `source_district` from mock districts (lines 649-650)
- Update CSV assertions (lines 664, 669, 673) to check 4 columns only

### 9. **Update test_commence_geometry_upload_scoring_good_ogr_file** (line 318)
- Change mock return: `([...], ['District-1', 'District-2'])` to just `[...]`
- Update populate_compactness mock to return simple dicts without source_district

### 10. **Update test_commence_geometry_upload_scoring_zipped_ogr_file** (line 355)
- Same changes as #9

### 11. **Update test_commence_geometry_upload_scoring_creates_blockassign_file** (line 726)
- Change mock return: `([...], ['District-1', 'District-2'])` to just `[...]`
- Remove source_district from mock districts in assertions

## Summary
- CSV file will have 4 columns: `district_number`, `geoid20`, `intpt_lon`, `intpt_lat`
- All source_district tracking removed from both geometry and block assignment processing
- Simplified implementation - easier to reintroduce later from other branch
- 2 tests removed entirely, ~9 tests simplified

## Files to Modify
1. `planscore/postread_calculate.py` - Remove source_district tracking from 3 functions
2. `planscore/tests/test_postread_calculate.py` - Update 9 tests, remove 2 tests
