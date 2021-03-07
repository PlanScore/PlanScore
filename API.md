API
===

🚧 PlanScore’s API is under development. 🚧

### Authentication

We require a [bearer token authorization header](https://tools.ietf.org/html/rfc6750)
to use the API. While it is under development, please contact
[info@planscore.org](mailto:info@planscore.org) to request a token.

### Sample Request

GeoJSON representing a district plan can be posted directly to `/api-upload`:

    curl --request POST \
        --header 'Authorization: Bearer {TOKEN}' \
        --data-binary @null-plan-incumbency.geojson \
        https://api.planscore.org/api-upload

See [null-plan-incumbency.geojson](planscore/tests/data/null-plan-incumbency.geojson)
for example input.

Data should be provided in [GeoJSON](https://geojson.org), one Polygon or
MultiPolygon per district. A meaningful plan description can be provided in a
root-level `description` field. If you know which districts have incumbents
running for re-election, select their party affiliation for a more accurate
prediction with an optional `Incumbent` property:

- `R` – Republican incumbent
- `D` – Democratic incumbent
- `O` – Open seat (default if unspecified)

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
