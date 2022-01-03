API
===

🚧 PlanScore’s API is under development. 🚧

### Authentication

We require a [bearer token authorization header](https://tools.ietf.org/html/rfc6750)
to use the API. While it is under development, please contact
[info@planscore.org](mailto:info@planscore.org) to request a token.

Simple Interaction
---

Plans represented as under-5MB GeoJSON files can be uploaded to the API in one
request. For other formats including zipped shapefiles, geopackage, or experimental
block assignment files, try *Multistep Interaction* below.

### Sample Request

GeoJSON representing a district plan can be posted directly to `/upload`:

    curl --request POST \
        --header 'Authorization: Bearer {TOKEN}' \
        --data-binary @null-plan-incumbency.geojson \
        https://api.planscore.org/upload

See [null-plan-incumbency.geojson](planscore/tests/data/null-plan-incumbency.geojson)
or [null-plan-modelversion.geojson](planscore/tests/data/null-plan-modelversion.geojson)
for example input.

Data should be provided in [GeoJSON](https://geojson.org), one Polygon or
MultiPolygon per district. A meaningful plan description can be provided in a
root-level `description` field. If you know which districts have incumbents
running for re-election, select their party affiliation for a more accurate
prediction with an optional `Incumbent` property:

- `R` – Republican incumbent
- `D` – Democratic incumbent
- `O` – Open seat (default if unspecified)

District plans shared with PlanScore are kept indefinitely. For score results
that automatically disappear within a week, use the `/upload/temporary` endpoint:

    curl --request POST \
        --header 'Authorization: Bearer {TOKEN}' \
        --data-binary @null-plan-incumbency.geojson \
        https://api.planscore.org/upload/temporary

### Sample Response

On success, two URLs will be returned in a JSON response:

    {
      "index_url": "https://planscore.s3.amazonaws.com/uploads/20210307T032912.752515089Z/index.json",
      "plan_url": "https://planscore.org/plan.html?20210307T032912.752515089Z"
    }

`index_url` is a machine-readable JSON representation of the plan being scored.
Initially it will show ongoing progress updates, and upon completion will
include complete scores for the uploaded plan. For an example, see
[index.json](https://planscore.s3.amazonaws.com/uploads/20210307T032912.752515089Z/index.json).

`plan_url` is a human-readable web page with graphs and maps for the plan being
scored. Initially it will show ongoing progress updates, and upon completion
will include complete scores for the uploaded plan. For an example, see
[plan.html?20210307T032912.752515089Z](https://planscore.org/plan.html?20210307T032912.752515089Z).

Multistep Interaction
---

Plans represented as zipped shapefiles, geopackage, experimental block
assignment files, or anything other than an under-5MB GeoJSON file should use
this three-step interaction.

### 1) Prepare Upload

Request S3 upload fields from `/upload`:

    curl --request GET \
        --header 'Authorization: Bearer {TOKEN}' \
        https://api.planscore.org/upload

The response will include a two-element list, with an AWS S3 URL and
a dictionary of additional form fields for a pre-signed POST request:

    HTTP/1.1 200
    
    [
        "https://planscore.s3.amazonaws.com/",
        {
            "key": {key},
            "AWSAccessKeyId": {AWSAccessKeyId},
            "x-amz-security-token": {x-amz-security-token},
            "policy": {policy},
            "signature": {signature},
            "acl": {acl},
            "success_action_redirect": {success_action_redirect},
        }
    ]

### 2) Send Upload

Send the complete upload file and all form fields from API response above to S3
in a `multipart/form-data` HTTP POST request:

    curl --request POST \
        --form key={key} \
        --form AWSAccessKeyId={AWSAccessKeyId} \
        --form x-amz-security-token={x-amz-security-token} \
        --form policy={policy} \
        --form signature={signature} \
        --form acl={acl} \
        --form success_action_redirect={success_action_redirect} \
        --form file=@null-plan-blockassignments.csv \
        https://planscore.s3.amazonaws.com/

See [null-plan-blockassignments.csv](planscore/tests/data/null-plan-blockassignments.csv)
for example input.

Retrieve the complete HTTP redirect URL from the S3 response:

    HTTP/1.1 302
    Location: {redirect URL}

### 3) Follow Through

Post a final request with additional detail to the redirect URL:

    curl --request POST \
        --header 'Authorization: Bearer {TOKEN}' \
        --header 'Content-Type: application/json' \
        --data '{"description": "A Plan", "incumbents": ["R","D"]}' \
        {redirect URL}

POST data should be a JSON dictionary with these optional keys:

- `description` (string): Short description of the plan will appear as the top-most header on the plan page.
- `incumbents` (list): Ordered list of incumbency scenario strings for each district. See above for possible values.
- `library_metadata` (dictionary): Any additional data to be passed through for possible later use.

On success, two URLs will be returned in a JSON response identical to _Simple Interaction_ above:

    {
      "index_url": "https://planscore.s3.amazonaws.com/uploads/20210307T032912.752515089Z/index.json",
      "plan_url": "https://planscore.org/plan.html?20210307T032912.752515089Z"
    }

Additional Methods
---

JSON representation of all currently-supported states is available at `/states`:

    curl https://api.planscore.org/states
