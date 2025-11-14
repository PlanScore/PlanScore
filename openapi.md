# PlanScore API

PlanScore's API allows you to upload electoral district plans for scoring and analysis.

🚧 **This API is under development.** 🚧

Plans can be uploaded either directly as GeoJSON (simple interaction) or through a
multi-step process for larger files or alternative formats like shapefiles.

Authentication is required via bearer token. Contact info@planscore.org to request a token.


# Base URL


| URL | Description |
|-----|-------------|
| https://api.planscore.org | Production server |


# Authentication



## Security Schemes

| Name              | Type              | Description              | Scheme              | Bearer Format             |
|-------------------|-------------------|--------------------------|---------------------|---------------------------|
| BearerAuth | http | Bearer token required for authenticated endpoints. Contact info@planscore.org to request a token. | bearer |  |

# APIs

## POST /upload

Upload district plan directly

Upload a GeoJSON district plan directly for scoring. Plans must be under 5MB.
For larger files or other formats, use the multistep upload process.





### Request Body

[GeoJSONPlan](#geojsonplan)







### Responses

#### 200


Plan uploaded successfully


[UploadResponse](#uploadresponse)







#### 400


Bad request - invalid GeoJSON or plan data


[ErrorResponse](#errorresponse)







#### 401


Authentication required


[ErrorResponse](#errorresponse)







## GET /upload

Get S3 upload fields

Request S3 upload fields for multistep upload process. Returns a pre-signed S3 URL
and form fields that can be used to upload files directly to S3.





### Responses

#### 200


S3 upload fields returned successfully


[S3UploadFields](#s3uploadfields)







#### 401


Authentication required


[ErrorResponse](#errorresponse)







## POST /upload/temporary

Upload temporary district plan

Upload a GeoJSON district plan for temporary scoring. Results will automatically
disappear within a week. Same format as regular upload endpoint.





### Request Body

[GeoJSONPlan](#geojsonplan)







### Responses

#### 200


Temporary plan uploaded successfully


[UploadResponse](#uploadresponse)







#### 400


Bad request - invalid GeoJSON or plan data


[ErrorResponse](#errorresponse)







#### 401


Authentication required


[ErrorResponse](#errorresponse)







## GET /upload/interactive

Get upload fields for browser-based uploads

Get S3 upload fields for browser-based interactive uploads. Similar to GET /upload
but designed for direct browser usage without authentication.





### Responses

#### 200


Upload fields returned successfully


[S3UploadFields](#s3uploadfields)







## POST /uploaded

Complete multistep upload

Final step in the multistep upload process. Called with the redirect URL from S3
after successful file upload to provide additional plan metadata and trigger scoring.





### Request Body

[MultistepUploadRequest](#multistepuploadrequest)







### Responses

#### 200


Upload completed successfully


[UploadResponse](#uploadresponse)







#### 400


Bad request - invalid upload data


[ErrorResponse](#errorresponse)







#### 401


Authentication required


[ErrorResponse](#errorresponse)







## GET /states

Get supported states

Returns a list of all currently supported states and legislative bodies
available for district plan scoring.





### Responses

#### 200


List of supported states returned successfully


[StatesResponse](#statesresponse)







## GET /model_versions

Get available model versions

Returns a list of IDs and descriptions for all currently supported
predictive model versions.





### Responses

#### 200


List of model versions returned successfully


[ModelVersionsResponse](#modelversionsresponse)







# Components



## GeoJSONPlan



| Field | Type | Description |
|-------|------|-------------|
| type | string | Must be "FeatureCollection" |
| description | string | Short description of the plan that will appear as the top-most header on the plan page |
| model_version | string | Predictive model version to use. If omitted, the first available version is used. |
| library_metadata | object | Additional metadata to be passed through for possible later use |
| features | array | Array of district polygons |


## DistrictFeature



| Field | Type | Description |
|-------|------|-------------|
| type | string |  |
| geometry |  |  |
| properties | object |  |


## Polygon



| Field | Type | Description |
|-------|------|-------------|
| type | string |  |
| coordinates | array |  |


## MultiPolygon



| Field | Type | Description |
|-------|------|-------------|
| type | string |  |
| coordinates | array |  |


## UploadResponse



| Field | Type | Description |
|-------|------|-------------|
| index_url | string | Machine-readable JSON representation of the plan being scored.
The response follows the structure defined in the PlanIndex schema.
 |
| plan_url | string | Human-readable web page with graphs and maps for the plan |


## S3UploadFields


S3 URL and form fields for pre-signed POST upload




## MultistepUploadRequest



| Field | Type | Description |
|-------|------|-------------|
| description | string | Short description of the plan |
| incumbents | array | Ordered list of incumbency scenario strings for each district |
| model_version | string | Predictive model version. If omitted, the first one is used. |
| library_metadata | object | Additional data to be passed through for possible later use |


## StatesResponse


List of supported states and legislative bodies




## ModelVersionsResponse


List of available predictive model versions




## PlanIndex



| Field | Type | Description |
|-------|------|-------------|
| id | string | Unique identifier for the plan |
| auth_token | string | Authentication token used for the upload (redacted) |
| commit_sha | string | Git commit SHA of the PlanScore version used for analysis |
| description | string | Plan description provided during upload |
| districts | array | Array of district analysis data |
| execution_id | string | AWS Step Functions execution identifier |
| geometry_key | string | S3 key for the geometry JSON file |
| incumbents | array | Incumbent party for each district (R=Republican, D=Democratic, O=Open) |
| key | string | S3 key path for the original uploaded file |
| library_metadata | object | Additional metadata passed through from upload |
| message | string | Status message about the scoring process |
| model | object | Information about the predictive model used |
| model_version | string | Specific model version used for analysis |
| start_time | number | Unix timestamp when scoring started |
| status | boolean | Whether scoring completed successfully |
| summary | object | Plan-level summary statistics and partisan metrics |


## ErrorResponse



| Field | Type | Description |
|-------|------|-------------|
| message | string | Error message |
