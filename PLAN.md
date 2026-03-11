# Implementation Plan: Block Assignment File Generation

## Overview
Generate block assignment CSV files from geographic district inputs, making them available for download through the `blockassign_file` key in `library_metadata`.

## Requirements
- Generate assignment files ONLY for geometry uploads, NOT for block assignment uploads
- Use Athena query with spatial join to determine block-to-district assignments
- Output CSV columns (in order): `district_number`, `source_district`, `geoid20`, `intpt_lon`, `intpt_lat`
- District numbers must be 1-based (Athena returns 0-based, need conversion)
- Files must be gzipped when uploaded to S3
- URL stored in `library_metadata['blockassign_file']` for frontend access
- Source district can be blank if not available

## Implementation Steps

### Step 1: Modify `put_district_geometries()` to Track Source Districts
**File**: `planscore/postread_calculate.py`

**Current behavior**: Returns list of S3 keys

**New behavior**: Return tuple `(keys, source_districts)` where `source_districts` is a list of strings

**Changes**:
```python
def put_district_geometries(s3, bucket, upload, path):
    # ... existing code ...

    field_name, features = util.ordered_districts(ds.GetLayer(0))
    source_districts = []

    for (index, feature) in enumerate(features):
        # Extract source_district value from feature
        if field_name:
            source_district = str(feature.GetField(field_name))
        else:
            source_district = ''

        source_districts.append(source_district)

        # ... existing geometry processing ...

    return keys, source_districts
```

**Impact**: Need to update all callers to handle tuple return value
- Test: `test_put_district_geometries` (update to unpack tuple)
- Test: `test_put_district_geometries_25d` (update to unpack tuple)
- Test: `test_put_district_geometries_missing_geometries` (update to unpack tuple)
- Test: `test_put_district_geometries_mixed_geometries` (update to unpack tuple)

### Step 2: Store Source Districts in Upload Object
**File**: `planscore/postread_calculate.py`, function `commence_geometry_upload_scoring()`

**Current code** (around line 60-61):
```python
upload2 = upload.clone(geometry_key=data.UPLOAD_GEOMETRY_KEY.format(id=upload.id))
put_district_geometries(s3, bucket, upload2, ds_path)
```

**New code**:
```python
upload2 = upload.clone(geometry_key=data.UPLOAD_GEOMETRY_KEY.format(id=upload.id))
keys, source_districts = put_district_geometries(s3, bucket, upload2, ds_path)
```

Then when creating districts with compactness information (around line 68-69):
```python
districts = observe.populate_compactness(geometries)
upload3 = upload2.clone(districts=districts)
```

**New code**:
```python
districts = observe.populate_compactness(geometries)
# Add source_district to each district dict
for (district, source_district) in zip(districts, source_districts):
    district['source_district'] = source_district
upload3 = upload2.clone(districts=districts)
```

### Step 3: Create `generate_block_assignment_file()` Function
**File**: `planscore/postread_calculate.py`

Add new function after `accumulate_district_totals()`:

```python
def generate_block_assignment_file(athena, s3, bucket, upload):
    '''Generate block assignment CSV file from spatial join and upload to S3.

    Returns S3 URL for the generated file.
    '''
    # Build Athena query for spatial join
    where_clause = 'ST_Within(ST_GeometryFromText(b.point), ST_GeometryFromText(d.polygon))'

    query = f'''
        -- {os.environ.get('ATHENA_DB')} {upload.model.key_prefix} and {upload.id[:2]}…{upload.id[-4:]}
        SELECT
            d.number AS district_number,
            b.geoid20,
            ST_X(ST_GeometryFromText(b.point)) AS intpt_lon,
            ST_Y(ST_GeometryFromText(b.point)) AS intpt_lat
        FROM
            "{os.environ.get('ATHENA_DB')}"."blocks" as b,
            "{os.environ.get('ATHENA_DB')}"."districts" AS d
        WHERE
            {where_clause}
            AND b.prefix = '{upload.model.key_prefix}'
            AND d.upload = '{upload.id}'
        ORDER BY d.number
    '''

    print(query)

    # Execute query and collect results
    rows = []
    for (status, dict) in util.iter_athena_exec(athena, query):
        if 'ResultSet' in dict:
            rows = resultset_to_district_totals(dict)

    # Build source_district lookup by district number (0-based from Athena)
    source_district_map = {}
    for district in upload.districts:
        # district['number'] is 1-based from observe.populate_compactness
        district_index = district.get('number', 0) - 1
        source_district_map[district_index] = district.get('source_district', '')

    # Generate CSV content
    csv_buffer = io.StringIO()
    csv_writer = csv.writer(csv_buffer)

    # Write header
    csv_writer.writerow(['district_number', 'source_district', 'geoid20', 'intpt_lon', 'intpt_lat'])

    # Write data rows
    for row in rows:
        athena_district_number = row['district_number']  # 0-based from Athena
        one_based_district = athena_district_number + 1  # Convert to 1-based
        source_district = source_district_map.get(athena_district_number, '')

        csv_writer.writerow([
            one_based_district,
            source_district,
            row['geoid20'],
            row['intpt_lon'],
            row['intpt_lat'],
        ])

    # Gzip and upload to S3
    csv_content = csv_buffer.getvalue().encode('utf8')
    gzipped_content = gzip.compress(csv_content)

    key = data.UPLOAD_BLOCKASSIGN_FILE_KEY.format(id=upload.id)

    s3.put_object(
        Bucket=bucket,
        Key=key,
        ACL='bucket-owner-full-control',
        Body=gzipped_content,
        ContentType='text/csv',
        ContentEncoding='gzip',
        StorageClass='INTELLIGENT_TIERING',
    )

    # Return S3 URL
    url = constants.S3_URL_PATTERN.format(b=bucket, k=key)
    return url
```

### Step 4: Integrate into Workflow
**File**: `planscore/postread_calculate.py`, function `commence_geometry_upload_scoring()`

**Current code** (around line 61-71):
```python
upload2 = upload.clone(geometry_key=data.UPLOAD_GEOMETRY_KEY.format(id=upload.id))
put_district_geometries(s3, bucket, upload2, ds_path)

response = accumulate_district_totals(athena, upload2, True)

observe.put_upload_index(storage, upload2.clone(message='Calculating district shapes'))

geometries = observe.load_upload_geometries(storage, upload2)
districts = observe.populate_compactness(geometries)
upload3 = upload2.clone(districts=districts)
```

**New code**:
```python
upload2 = upload.clone(geometry_key=data.UPLOAD_GEOMETRY_KEY.format(id=upload.id))
keys, source_districts = put_district_geometries(s3, bucket, upload2, ds_path)

response = accumulate_district_totals(athena, upload2, True)

observe.put_upload_index(storage, upload2.clone(message='Calculating district shapes'))

geometries = observe.load_upload_geometries(storage, upload2)
districts = observe.populate_compactness(geometries)

# Add source_district to each district dict
for (district, source_district) in zip(districts, source_districts):
    district['source_district'] = source_district

upload3 = upload2.clone(districts=districts)

observe.put_upload_index(storage, upload3.clone(message='Counting votes and people in each district'))

for (state, results) in response:
    pass

print(json.dumps(state))
print(json.dumps(results))

upload4 = upload3.clone(districts=[
    dict(totals=totals, **district)
    for (district, totals) in zip(districts, results)
])

# Generate block assignment file after districts have data
observe.put_upload_index(storage, upload4.clone(message='Generating block assignment file'))
blockassign_url = generate_block_assignment_file(athena, s3, bucket, upload4)

observe.put_upload_index(storage, upload4.clone(message='Predicting future votes for each district'))

try:
    upload5 = score.calculate_everything(upload4)
except Exception as err:
    upload6 = upload4.clone(
        status=False,
        message=f'Something went wrong: {err}',
    )
else:
    upload6 = upload5.clone(
        status=True,
        message='Finished scoring this plan.',
        library_metadata={'blockassign_file': blockassign_url},
    )

observe.put_upload_index(storage, upload6)

return upload6
```

### Step 5: Update Existing Tests
**File**: `planscore/tests/test_postread_calculate.py`

Update these tests to handle new tuple return from `put_district_geometries()`:
- `test_put_district_geometries`: Change `keys = ...` to `keys, source_districts = ...`
- `test_put_district_geometries_25d`: Same change
- `test_put_district_geometries_missing_geometries`: Same change
- `test_put_district_geometries_mixed_geometries`: Same change

## Testing Strategy

### Unit Tests (already added, currently failing)
1. `test_generate_block_assignment_file_spatial_join` - Query structure and S3 upload
2. `test_generate_block_assignment_file_csv_format` - CSV format and 1-based numbering
3. `test_generate_block_assignment_file_blank_source_district` - Blank source_district handling
4. `test_commence_geometry_upload_scoring_creates_blockassign_file` - Workflow integration
5. `test_put_district_geometries_tracks_source_district` - Source district extraction

### Manual Testing
1. Upload a geometry file with district names
2. Verify blockassign_file appears in library_metadata
3. Download and verify CSV format
4. Check district_number is 1-based
5. Verify source_district column contains correct values

## Edge Cases to Handle
1. **Blank source_district**: When `field_name` is None or feature has no field, use empty string
2. **Missing source_district key in district dict**: Use `.get('source_district', '')`
3. **Library_metadata persistence**: Ensure it's passed through all upload.clone() calls
4. **Block assignment uploads**: This should NOT generate files (only geometry uploads)

## Files to Modify
1. `planscore/data.py` - ✅ DONE (UPLOAD_BLOCKASSIGN_FILE_KEY constant added)
2. `planscore/postread_calculate.py` - Modify `put_district_geometries()`, add `generate_block_assignment_file()`, modify `commence_geometry_upload_scoring()`
3. `planscore/tests/test_postread_calculate.py` - ✅ DONE (5 failing tests added), need to update 4 existing tests

## Success Criteria
- All 5 new tests pass
- All existing tests still pass
- Generated CSV has correct format and column order
- District numbers are 1-based
- Files are gzipped
- URL appears in library_metadata
- Block assignment uploads do NOT generate these files
