---
title: PlanScore API v1.0.0
language_tabs:
  - shell: Shell
  - http: HTTP
  - javascript: JavaScript
  - ruby: Ruby
  - python: Python
  - php: PHP
  - java: Java
  - go: Go
toc_footers: []
includes: []
search: true
highlight_theme: darkula
headingLevel: 2

---

<!-- Generator: Widdershins v4.0.1 -->

<h1 id="planscore-api">PlanScore API v1.0.0</h1>

> Scroll down for code samples, example requests and responses. Select a language for code samples from the tabs above or the mobile navigation menu.

PlanScore's API allows you to upload electoral district plans for scoring and analysis.

🚧 **This API is under development.** 🚧

Plans can be uploaded either directly as GeoJSON (simple interaction) or through a
multi-step process for larger files or alternative formats like shapefiles.

Authentication is required via bearer token. Contact info@planscore.org to request a token.

Base URLs:

* <a href="https://api.planscore.org">https://api.planscore.org</a>

Email: <a href="mailto:info@planscore.org">Support</a> 
License: <a href="https://github.com/PlanScore/PlanScore">Open Source</a>

# Authentication

- HTTP Authentication, scheme: bearer Bearer token required for authenticated endpoints. Contact info@planscore.org to request a token.

<h1 id="planscore-api-default">Default</h1>

## get__upload

> Code samples

```shell
# You can also use wget
curl -X GET https://api.planscore.org/upload \
  -H 'Accept: application/json' \
  -H 'Authorization: Bearer {access-token}'

```

```http
GET https://api.planscore.org/upload HTTP/1.1
Host: api.planscore.org
Accept: application/json

```

```javascript

const headers = {
  'Accept':'application/json',
  'Authorization':'Bearer {access-token}'
};

fetch('https://api.planscore.org/upload',
{
  method: 'GET',

  headers: headers
})
.then(function(res) {
    return res.json();
}).then(function(body) {
    console.log(body);
});

```

```ruby
require 'rest-client'
require 'json'

headers = {
  'Accept' => 'application/json',
  'Authorization' => 'Bearer {access-token}'
}

result = RestClient.get 'https://api.planscore.org/upload',
  params: {
  }, headers: headers

p JSON.parse(result)

```

```python
import requests
headers = {
  'Accept': 'application/json',
  'Authorization': 'Bearer {access-token}'
}

r = requests.get('https://api.planscore.org/upload', headers = headers)

print(r.json())

```

```php
<?php

require 'vendor/autoload.php';

$headers = array(
    'Accept' => 'application/json',
    'Authorization' => 'Bearer {access-token}',
);

$client = new \GuzzleHttp\Client();

// Define array of request body.
$request_body = array();

try {
    $response = $client->request('GET','https://api.planscore.org/upload', array(
        'headers' => $headers,
        'json' => $request_body,
       )
    );
    print_r($response->getBody()->getContents());
 }
 catch (\GuzzleHttp\Exception\BadResponseException $e) {
    // handle exception or api errors.
    print_r($e->getMessage());
 }

 // ...

```

```java
URL obj = new URL("https://api.planscore.org/upload");
HttpURLConnection con = (HttpURLConnection) obj.openConnection();
con.setRequestMethod("GET");
int responseCode = con.getResponseCode();
BufferedReader in = new BufferedReader(
    new InputStreamReader(con.getInputStream()));
String inputLine;
StringBuffer response = new StringBuffer();
while ((inputLine = in.readLine()) != null) {
    response.append(inputLine);
}
in.close();
System.out.println(response.toString());

```

```go
package main

import (
       "bytes"
       "net/http"
)

func main() {

    headers := map[string][]string{
        "Accept": []string{"application/json"},
        "Authorization": []string{"Bearer {access-token}"},
    }

    data := bytes.NewBuffer([]byte{jsonReq})
    req, err := http.NewRequest("GET", "https://api.planscore.org/upload", data)
    req.Header = headers

    client := &http.Client{}
    resp, err := client.Do(req)
    // ...
}

```

`GET /upload`

*Get S3 upload fields*

Request S3 upload fields for multistep upload process. Returns a pre-signed S3 URL
and form fields that can be used to upload files directly to S3.

> Example responses

> 200 Response

```json
[
  "https://planscore.s3.amazonaws.com/",
  {
    "key": "uploads/20210307T032912.752515089Z/${filename}",
    "AWSAccessKeyId": "AKIAIOSFODNN7EXAMPLE",
    "x-amz-security-token": "token123",
    "x-amz-storage-class": "INTELLIGENT_TIERING",
    "policy": "eyJjb25kaXRpb25zIjpbXX0=",
    "signature": "signature123",
    "acl": "bucket-owner-full-control",
    "success_action_redirect": "https://api.planscore.org/uploaded?id=signed_id"
  }
]
```

> 401 Response

```json
{
  "message": "Bad GeoJSON input"
}
```

<h3 id="get__upload-responses">Responses</h3>

|Status|Meaning|Description|Schema|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|S3 upload fields returned successfully|[S3UploadFields](#schemas3uploadfields)|
|401|[Unauthorized](https://tools.ietf.org/html/rfc7235#section-3.1)|Authentication required|[ErrorResponse](#schemaerrorresponse)|

### Response Headers

|Status|Header|Type|Format|Description|
|---|---|---|---|---|
|200|Access-Control-Allow-Origin|string||none|

<aside class="warning">
To perform this operation, you must be authenticated by means of one of the following methods:
BearerAuth
</aside>

## post__upload

> Code samples

```shell
# You can also use wget
curl -X POST https://api.planscore.org/upload \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json' \
  -H 'Authorization: Bearer {access-token}'

```

```http
POST https://api.planscore.org/upload HTTP/1.1
Host: api.planscore.org
Content-Type: application/json
Accept: application/json

```

```javascript
const inputBody = '{
  "type": "FeatureCollection",
  "description": "Congressional Redistricting Plan 2024",
  "model_version": "string",
  "library_metadata": {},
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Polygon",
        "coordinates": [
          [
            [
              0,
              0
            ]
          ]
        ]
      },
      "properties": {
        "Incumbent": "R"
      }
    }
  ]
}';
const headers = {
  'Content-Type':'application/json',
  'Accept':'application/json',
  'Authorization':'Bearer {access-token}'
};

fetch('https://api.planscore.org/upload',
{
  method: 'POST',
  body: inputBody,
  headers: headers
})
.then(function(res) {
    return res.json();
}).then(function(body) {
    console.log(body);
});

```

```ruby
require 'rest-client'
require 'json'

headers = {
  'Content-Type' => 'application/json',
  'Accept' => 'application/json',
  'Authorization' => 'Bearer {access-token}'
}

result = RestClient.post 'https://api.planscore.org/upload',
  params: {
  }, headers: headers

p JSON.parse(result)

```

```python
import requests
headers = {
  'Content-Type': 'application/json',
  'Accept': 'application/json',
  'Authorization': 'Bearer {access-token}'
}

r = requests.post('https://api.planscore.org/upload', headers = headers)

print(r.json())

```

```php
<?php

require 'vendor/autoload.php';

$headers = array(
    'Content-Type' => 'application/json',
    'Accept' => 'application/json',
    'Authorization' => 'Bearer {access-token}',
);

$client = new \GuzzleHttp\Client();

// Define array of request body.
$request_body = array();

try {
    $response = $client->request('POST','https://api.planscore.org/upload', array(
        'headers' => $headers,
        'json' => $request_body,
       )
    );
    print_r($response->getBody()->getContents());
 }
 catch (\GuzzleHttp\Exception\BadResponseException $e) {
    // handle exception or api errors.
    print_r($e->getMessage());
 }

 // ...

```

```java
URL obj = new URL("https://api.planscore.org/upload");
HttpURLConnection con = (HttpURLConnection) obj.openConnection();
con.setRequestMethod("POST");
int responseCode = con.getResponseCode();
BufferedReader in = new BufferedReader(
    new InputStreamReader(con.getInputStream()));
String inputLine;
StringBuffer response = new StringBuffer();
while ((inputLine = in.readLine()) != null) {
    response.append(inputLine);
}
in.close();
System.out.println(response.toString());

```

```go
package main

import (
       "bytes"
       "net/http"
)

func main() {

    headers := map[string][]string{
        "Content-Type": []string{"application/json"},
        "Accept": []string{"application/json"},
        "Authorization": []string{"Bearer {access-token}"},
    }

    data := bytes.NewBuffer([]byte{jsonReq})
    req, err := http.NewRequest("POST", "https://api.planscore.org/upload", data)
    req.Header = headers

    client := &http.Client{}
    resp, err := client.Do(req)
    // ...
}

```

`POST /upload`

*Upload district plan directly*

Upload a GeoJSON district plan directly for scoring. Plans must be under 5MB.
For larger files or other formats, use the multistep upload process.

> Body parameter

```json
{
  "type": "FeatureCollection",
  "description": "Congressional Redistricting Plan 2024",
  "model_version": "string",
  "library_metadata": {},
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Polygon",
        "coordinates": [
          [
            [
              0,
              0
            ]
          ]
        ]
      },
      "properties": {
        "Incumbent": "R"
      }
    }
  ]
}
```

<h3 id="post__upload-parameters">Parameters</h3>

|Name|In|Type|Required|Description|
|---|---|---|---|---|
|body|body|[GeoJSONPlan](#schemageojsonplan)|true|none|

> Example responses

> 200 Response

```json
{
  "index_url": "https://planscore.s3.amazonaws.com/uploads/20210307T032912.752515089Z/index.json",
  "plan_url": "https://planscore.org/plan.html?20210307T032912.752515089Z"
}
```

<h3 id="post__upload-responses">Responses</h3>

|Status|Meaning|Description|Schema|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|Plan uploaded successfully|[UploadResponse](#schemauploadresponse)|
|400|[Bad Request](https://tools.ietf.org/html/rfc7231#section-6.5.1)|Bad request - invalid GeoJSON or plan data|[ErrorResponse](#schemaerrorresponse)|
|401|[Unauthorized](https://tools.ietf.org/html/rfc7235#section-3.1)|Authentication required|[ErrorResponse](#schemaerrorresponse)|

<aside class="warning">
To perform this operation, you must be authenticated by means of one of the following methods:
BearerAuth
</aside>

## post__upload_temporary

> Code samples

```shell
# You can also use wget
curl -X POST https://api.planscore.org/upload/temporary \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json' \
  -H 'Authorization: Bearer {access-token}'

```

```http
POST https://api.planscore.org/upload/temporary HTTP/1.1
Host: api.planscore.org
Content-Type: application/json
Accept: application/json

```

```javascript
const inputBody = '{
  "type": "FeatureCollection",
  "description": "Congressional Redistricting Plan 2024",
  "model_version": "string",
  "library_metadata": {},
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Polygon",
        "coordinates": [
          [
            [
              0,
              0
            ]
          ]
        ]
      },
      "properties": {
        "Incumbent": "R"
      }
    }
  ]
}';
const headers = {
  'Content-Type':'application/json',
  'Accept':'application/json',
  'Authorization':'Bearer {access-token}'
};

fetch('https://api.planscore.org/upload/temporary',
{
  method: 'POST',
  body: inputBody,
  headers: headers
})
.then(function(res) {
    return res.json();
}).then(function(body) {
    console.log(body);
});

```

```ruby
require 'rest-client'
require 'json'

headers = {
  'Content-Type' => 'application/json',
  'Accept' => 'application/json',
  'Authorization' => 'Bearer {access-token}'
}

result = RestClient.post 'https://api.planscore.org/upload/temporary',
  params: {
  }, headers: headers

p JSON.parse(result)

```

```python
import requests
headers = {
  'Content-Type': 'application/json',
  'Accept': 'application/json',
  'Authorization': 'Bearer {access-token}'
}

r = requests.post('https://api.planscore.org/upload/temporary', headers = headers)

print(r.json())

```

```php
<?php

require 'vendor/autoload.php';

$headers = array(
    'Content-Type' => 'application/json',
    'Accept' => 'application/json',
    'Authorization' => 'Bearer {access-token}',
);

$client = new \GuzzleHttp\Client();

// Define array of request body.
$request_body = array();

try {
    $response = $client->request('POST','https://api.planscore.org/upload/temporary', array(
        'headers' => $headers,
        'json' => $request_body,
       )
    );
    print_r($response->getBody()->getContents());
 }
 catch (\GuzzleHttp\Exception\BadResponseException $e) {
    // handle exception or api errors.
    print_r($e->getMessage());
 }

 // ...

```

```java
URL obj = new URL("https://api.planscore.org/upload/temporary");
HttpURLConnection con = (HttpURLConnection) obj.openConnection();
con.setRequestMethod("POST");
int responseCode = con.getResponseCode();
BufferedReader in = new BufferedReader(
    new InputStreamReader(con.getInputStream()));
String inputLine;
StringBuffer response = new StringBuffer();
while ((inputLine = in.readLine()) != null) {
    response.append(inputLine);
}
in.close();
System.out.println(response.toString());

```

```go
package main

import (
       "bytes"
       "net/http"
)

func main() {

    headers := map[string][]string{
        "Content-Type": []string{"application/json"},
        "Accept": []string{"application/json"},
        "Authorization": []string{"Bearer {access-token}"},
    }

    data := bytes.NewBuffer([]byte{jsonReq})
    req, err := http.NewRequest("POST", "https://api.planscore.org/upload/temporary", data)
    req.Header = headers

    client := &http.Client{}
    resp, err := client.Do(req)
    // ...
}

```

`POST /upload/temporary`

*Upload temporary district plan*

Upload a GeoJSON district plan for temporary scoring. Results will automatically
disappear within a week. Same format as regular upload endpoint.

> Body parameter

```json
{
  "type": "FeatureCollection",
  "description": "Congressional Redistricting Plan 2024",
  "model_version": "string",
  "library_metadata": {},
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Polygon",
        "coordinates": [
          [
            [
              0,
              0
            ]
          ]
        ]
      },
      "properties": {
        "Incumbent": "R"
      }
    }
  ]
}
```

<h3 id="post__upload_temporary-parameters">Parameters</h3>

|Name|In|Type|Required|Description|
|---|---|---|---|---|
|body|body|[GeoJSONPlan](#schemageojsonplan)|true|none|

> Example responses

> 200 Response

```json
{
  "index_url": "https://planscore.s3.amazonaws.com/uploads/20210307T032912.752515089Z/index.json",
  "plan_url": "https://planscore.org/plan.html?20210307T032912.752515089Z"
}
```

<h3 id="post__upload_temporary-responses">Responses</h3>

|Status|Meaning|Description|Schema|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|Temporary plan uploaded successfully|[UploadResponse](#schemauploadresponse)|
|400|[Bad Request](https://tools.ietf.org/html/rfc7231#section-6.5.1)|Bad request - invalid GeoJSON or plan data|[ErrorResponse](#schemaerrorresponse)|
|401|[Unauthorized](https://tools.ietf.org/html/rfc7235#section-3.1)|Authentication required|[ErrorResponse](#schemaerrorresponse)|

<aside class="warning">
To perform this operation, you must be authenticated by means of one of the following methods:
BearerAuth
</aside>

## get__upload_interactive

> Code samples

```shell
# You can also use wget
curl -X GET https://api.planscore.org/upload/interactive \
  -H 'Accept: application/json' \
  -H 'Authorization: Bearer {access-token}'

```

```http
GET https://api.planscore.org/upload/interactive HTTP/1.1
Host: api.planscore.org
Accept: application/json

```

```javascript

const headers = {
  'Accept':'application/json',
  'Authorization':'Bearer {access-token}'
};

fetch('https://api.planscore.org/upload/interactive',
{
  method: 'GET',

  headers: headers
})
.then(function(res) {
    return res.json();
}).then(function(body) {
    console.log(body);
});

```

```ruby
require 'rest-client'
require 'json'

headers = {
  'Accept' => 'application/json',
  'Authorization' => 'Bearer {access-token}'
}

result = RestClient.get 'https://api.planscore.org/upload/interactive',
  params: {
  }, headers: headers

p JSON.parse(result)

```

```python
import requests
headers = {
  'Accept': 'application/json',
  'Authorization': 'Bearer {access-token}'
}

r = requests.get('https://api.planscore.org/upload/interactive', headers = headers)

print(r.json())

```

```php
<?php

require 'vendor/autoload.php';

$headers = array(
    'Accept' => 'application/json',
    'Authorization' => 'Bearer {access-token}',
);

$client = new \GuzzleHttp\Client();

// Define array of request body.
$request_body = array();

try {
    $response = $client->request('GET','https://api.planscore.org/upload/interactive', array(
        'headers' => $headers,
        'json' => $request_body,
       )
    );
    print_r($response->getBody()->getContents());
 }
 catch (\GuzzleHttp\Exception\BadResponseException $e) {
    // handle exception or api errors.
    print_r($e->getMessage());
 }

 // ...

```

```java
URL obj = new URL("https://api.planscore.org/upload/interactive");
HttpURLConnection con = (HttpURLConnection) obj.openConnection();
con.setRequestMethod("GET");
int responseCode = con.getResponseCode();
BufferedReader in = new BufferedReader(
    new InputStreamReader(con.getInputStream()));
String inputLine;
StringBuffer response = new StringBuffer();
while ((inputLine = in.readLine()) != null) {
    response.append(inputLine);
}
in.close();
System.out.println(response.toString());

```

```go
package main

import (
       "bytes"
       "net/http"
)

func main() {

    headers := map[string][]string{
        "Accept": []string{"application/json"},
        "Authorization": []string{"Bearer {access-token}"},
    }

    data := bytes.NewBuffer([]byte{jsonReq})
    req, err := http.NewRequest("GET", "https://api.planscore.org/upload/interactive", data)
    req.Header = headers

    client := &http.Client{}
    resp, err := client.Do(req)
    // ...
}

```

`GET /upload/interactive`

*Get upload fields for browser-based uploads*

Get S3 upload fields for browser-based interactive uploads. Similar to GET /upload
but designed for direct browser usage without authentication.

> Example responses

> 200 Response

```json
[
  "http://example.com",
  "http://example.com"
]
```

<h3 id="get__upload_interactive-responses">Responses</h3>

|Status|Meaning|Description|Schema|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|Upload fields returned successfully|[S3UploadFields](#schemas3uploadfields)|

### Response Headers

|Status|Header|Type|Format|Description|
|---|---|---|---|---|
|200|Access-Control-Allow-Origin|string||none|

<aside class="warning">
To perform this operation, you must be authenticated by means of one of the following methods:
BearerAuth
</aside>

## post__uploaded

> Code samples

```shell
# You can also use wget
curl -X POST https://api.planscore.org/uploaded \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json' \
  -H 'Authorization: Bearer {access-token}'

```

```http
POST https://api.planscore.org/uploaded HTTP/1.1
Host: api.planscore.org
Content-Type: application/json
Accept: application/json

```

```javascript
const inputBody = '{
  "description": "A Plan",
  "incumbents": [
    "R",
    "D",
    "O"
  ],
  "model_version": "string",
  "library_metadata": {}
}';
const headers = {
  'Content-Type':'application/json',
  'Accept':'application/json',
  'Authorization':'Bearer {access-token}'
};

fetch('https://api.planscore.org/uploaded',
{
  method: 'POST',
  body: inputBody,
  headers: headers
})
.then(function(res) {
    return res.json();
}).then(function(body) {
    console.log(body);
});

```

```ruby
require 'rest-client'
require 'json'

headers = {
  'Content-Type' => 'application/json',
  'Accept' => 'application/json',
  'Authorization' => 'Bearer {access-token}'
}

result = RestClient.post 'https://api.planscore.org/uploaded',
  params: {
  }, headers: headers

p JSON.parse(result)

```

```python
import requests
headers = {
  'Content-Type': 'application/json',
  'Accept': 'application/json',
  'Authorization': 'Bearer {access-token}'
}

r = requests.post('https://api.planscore.org/uploaded', headers = headers)

print(r.json())

```

```php
<?php

require 'vendor/autoload.php';

$headers = array(
    'Content-Type' => 'application/json',
    'Accept' => 'application/json',
    'Authorization' => 'Bearer {access-token}',
);

$client = new \GuzzleHttp\Client();

// Define array of request body.
$request_body = array();

try {
    $response = $client->request('POST','https://api.planscore.org/uploaded', array(
        'headers' => $headers,
        'json' => $request_body,
       )
    );
    print_r($response->getBody()->getContents());
 }
 catch (\GuzzleHttp\Exception\BadResponseException $e) {
    // handle exception or api errors.
    print_r($e->getMessage());
 }

 // ...

```

```java
URL obj = new URL("https://api.planscore.org/uploaded");
HttpURLConnection con = (HttpURLConnection) obj.openConnection();
con.setRequestMethod("POST");
int responseCode = con.getResponseCode();
BufferedReader in = new BufferedReader(
    new InputStreamReader(con.getInputStream()));
String inputLine;
StringBuffer response = new StringBuffer();
while ((inputLine = in.readLine()) != null) {
    response.append(inputLine);
}
in.close();
System.out.println(response.toString());

```

```go
package main

import (
       "bytes"
       "net/http"
)

func main() {

    headers := map[string][]string{
        "Content-Type": []string{"application/json"},
        "Accept": []string{"application/json"},
        "Authorization": []string{"Bearer {access-token}"},
    }

    data := bytes.NewBuffer([]byte{jsonReq})
    req, err := http.NewRequest("POST", "https://api.planscore.org/uploaded", data)
    req.Header = headers

    client := &http.Client{}
    resp, err := client.Do(req)
    // ...
}

```

`POST /uploaded`

*Complete multistep upload*

Final step in the multistep upload process. Called with the redirect URL from S3
after successful file upload to provide additional plan metadata and trigger scoring.

> Body parameter

```json
{
  "description": "A Plan",
  "incumbents": [
    "R",
    "D",
    "O"
  ],
  "model_version": "string",
  "library_metadata": {}
}
```

<h3 id="post__uploaded-parameters">Parameters</h3>

|Name|In|Type|Required|Description|
|---|---|---|---|---|
|body|body|[MultistepUploadRequest](#schemamultistepuploadrequest)|false|none|

> Example responses

> 200 Response

```json
{
  "index_url": "https://planscore.s3.amazonaws.com/uploads/20210307T032912.752515089Z/index.json",
  "plan_url": "https://planscore.org/plan.html?20210307T032912.752515089Z"
}
```

<h3 id="post__uploaded-responses">Responses</h3>

|Status|Meaning|Description|Schema|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|Upload completed successfully|[UploadResponse](#schemauploadresponse)|
|400|[Bad Request](https://tools.ietf.org/html/rfc7231#section-6.5.1)|Bad request - invalid upload data|[ErrorResponse](#schemaerrorresponse)|
|401|[Unauthorized](https://tools.ietf.org/html/rfc7235#section-3.1)|Authentication required|[ErrorResponse](#schemaerrorresponse)|

<aside class="warning">
To perform this operation, you must be authenticated by means of one of the following methods:
BearerAuth
</aside>

## get__states

> Code samples

```shell
# You can also use wget
curl -X GET https://api.planscore.org/states \
  -H 'Accept: application/json' \
  -H 'Authorization: Bearer {access-token}'

```

```http
GET https://api.planscore.org/states HTTP/1.1
Host: api.planscore.org
Accept: application/json

```

```javascript

const headers = {
  'Accept':'application/json',
  'Authorization':'Bearer {access-token}'
};

fetch('https://api.planscore.org/states',
{
  method: 'GET',

  headers: headers
})
.then(function(res) {
    return res.json();
}).then(function(body) {
    console.log(body);
});

```

```ruby
require 'rest-client'
require 'json'

headers = {
  'Accept' => 'application/json',
  'Authorization' => 'Bearer {access-token}'
}

result = RestClient.get 'https://api.planscore.org/states',
  params: {
  }, headers: headers

p JSON.parse(result)

```

```python
import requests
headers = {
  'Accept': 'application/json',
  'Authorization': 'Bearer {access-token}'
}

r = requests.get('https://api.planscore.org/states', headers = headers)

print(r.json())

```

```php
<?php

require 'vendor/autoload.php';

$headers = array(
    'Accept' => 'application/json',
    'Authorization' => 'Bearer {access-token}',
);

$client = new \GuzzleHttp\Client();

// Define array of request body.
$request_body = array();

try {
    $response = $client->request('GET','https://api.planscore.org/states', array(
        'headers' => $headers,
        'json' => $request_body,
       )
    );
    print_r($response->getBody()->getContents());
 }
 catch (\GuzzleHttp\Exception\BadResponseException $e) {
    // handle exception or api errors.
    print_r($e->getMessage());
 }

 // ...

```

```java
URL obj = new URL("https://api.planscore.org/states");
HttpURLConnection con = (HttpURLConnection) obj.openConnection();
con.setRequestMethod("GET");
int responseCode = con.getResponseCode();
BufferedReader in = new BufferedReader(
    new InputStreamReader(con.getInputStream()));
String inputLine;
StringBuffer response = new StringBuffer();
while ((inputLine = in.readLine()) != null) {
    response.append(inputLine);
}
in.close();
System.out.println(response.toString());

```

```go
package main

import (
       "bytes"
       "net/http"
)

func main() {

    headers := map[string][]string{
        "Accept": []string{"application/json"},
        "Authorization": []string{"Bearer {access-token}"},
    }

    data := bytes.NewBuffer([]byte{jsonReq})
    req, err := http.NewRequest("GET", "https://api.planscore.org/states", data)
    req.Header = headers

    client := &http.Client{}
    resp, err := client.Do(req)
    // ...
}

```

`GET /states`

*Get supported states*

Returns a list of all currently supported states and legislative bodies
available for district plan scoring.

> Example responses

> 200 Response

```json
[
  [
    "XX",
    "congress"
  ],
  [
    "CA",
    "congress"
  ],
  [
    "TX",
    "congress"
  ]
]
```

<h3 id="get__states-responses">Responses</h3>

|Status|Meaning|Description|Schema|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|List of supported states returned successfully|[StatesResponse](#schemastatesresponse)|

### Response Headers

|Status|Header|Type|Format|Description|
|---|---|---|---|---|
|200|Access-Control-Allow-Origin|string||none|

<aside class="warning">
To perform this operation, you must be authenticated by means of one of the following methods:
BearerAuth
</aside>

## get__model_versions

> Code samples

```shell
# You can also use wget
curl -X GET https://api.planscore.org/model_versions \
  -H 'Accept: application/json' \
  -H 'Authorization: Bearer {access-token}'

```

```http
GET https://api.planscore.org/model_versions HTTP/1.1
Host: api.planscore.org
Accept: application/json

```

```javascript

const headers = {
  'Accept':'application/json',
  'Authorization':'Bearer {access-token}'
};

fetch('https://api.planscore.org/model_versions',
{
  method: 'GET',

  headers: headers
})
.then(function(res) {
    return res.json();
}).then(function(body) {
    console.log(body);
});

```

```ruby
require 'rest-client'
require 'json'

headers = {
  'Accept' => 'application/json',
  'Authorization' => 'Bearer {access-token}'
}

result = RestClient.get 'https://api.planscore.org/model_versions',
  params: {
  }, headers: headers

p JSON.parse(result)

```

```python
import requests
headers = {
  'Accept': 'application/json',
  'Authorization': 'Bearer {access-token}'
}

r = requests.get('https://api.planscore.org/model_versions', headers = headers)

print(r.json())

```

```php
<?php

require 'vendor/autoload.php';

$headers = array(
    'Accept' => 'application/json',
    'Authorization' => 'Bearer {access-token}',
);

$client = new \GuzzleHttp\Client();

// Define array of request body.
$request_body = array();

try {
    $response = $client->request('GET','https://api.planscore.org/model_versions', array(
        'headers' => $headers,
        'json' => $request_body,
       )
    );
    print_r($response->getBody()->getContents());
 }
 catch (\GuzzleHttp\Exception\BadResponseException $e) {
    // handle exception or api errors.
    print_r($e->getMessage());
 }

 // ...

```

```java
URL obj = new URL("https://api.planscore.org/model_versions");
HttpURLConnection con = (HttpURLConnection) obj.openConnection();
con.setRequestMethod("GET");
int responseCode = con.getResponseCode();
BufferedReader in = new BufferedReader(
    new InputStreamReader(con.getInputStream()));
String inputLine;
StringBuffer response = new StringBuffer();
while ((inputLine = in.readLine()) != null) {
    response.append(inputLine);
}
in.close();
System.out.println(response.toString());

```

```go
package main

import (
       "bytes"
       "net/http"
)

func main() {

    headers := map[string][]string{
        "Accept": []string{"application/json"},
        "Authorization": []string{"Bearer {access-token}"},
    }

    data := bytes.NewBuffer([]byte{jsonReq})
    req, err := http.NewRequest("GET", "https://api.planscore.org/model_versions", data)
    req.Header = headers

    client := &http.Client{}
    resp, err := client.Do(req)
    // ...
}

```

`GET /model_versions`

*Get available model versions*

Returns a list of IDs and descriptions for all currently supported
predictive model versions.

> Example responses

> 200 Response

```json
[
  [
    "2024-01",
    "2024 Model Version"
  ],
  [
    "2022-01",
    "2022 Model Version"
  ]
]
```

<h3 id="get__model_versions-responses">Responses</h3>

|Status|Meaning|Description|Schema|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|List of model versions returned successfully|[ModelVersionsResponse](#schemamodelversionsresponse)|

### Response Headers

|Status|Header|Type|Format|Description|
|---|---|---|---|---|
|200|Access-Control-Allow-Origin|string||none|

<aside class="warning">
To perform this operation, you must be authenticated by means of one of the following methods:
BearerAuth
</aside>

# Schemas

<h2 id="tocS_GeoJSONPlan">GeoJSONPlan</h2>
<!-- backwards compatibility -->
<a id="schemageojsonplan"></a>
<a id="schema_GeoJSONPlan"></a>
<a id="tocSgeojsonplan"></a>
<a id="tocsgeojsonplan"></a>

```json
{
  "type": "FeatureCollection",
  "description": "Congressional Redistricting Plan 2024",
  "model_version": "string",
  "library_metadata": {},
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Polygon",
        "coordinates": [
          [
            [
              0,
              0
            ]
          ]
        ]
      },
      "properties": {
        "Incumbent": "R"
      }
    }
  ]
}

```

### Properties

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|type|string|true|none|Must be "FeatureCollection"|
|description|string|false|none|Short description of the plan that will appear as the top-most header on the plan page|
|model_version|string|false|none|Predictive model version to use. If omitted, the first available version is used.|
|library_metadata|object|false|none|Additional metadata to be passed through for possible later use|
|features|[[DistrictFeature](#schemadistrictfeature)]|true|none|Array of district polygons|

#### Enumerated Values

|Property|Value|
|---|---|
|type|FeatureCollection|

<h2 id="tocS_DistrictFeature">DistrictFeature</h2>
<!-- backwards compatibility -->
<a id="schemadistrictfeature"></a>
<a id="schema_DistrictFeature"></a>
<a id="tocSdistrictfeature"></a>
<a id="tocsdistrictfeature"></a>

```json
{
  "type": "Feature",
  "geometry": {
    "type": "Polygon",
    "coordinates": [
      [
        [
          0,
          0
        ]
      ]
    ]
  },
  "properties": {
    "Incumbent": "R"
  }
}

```

### Properties

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|type|string|true|none|none|
|geometry|any|true|none|none|

oneOf

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|» *anonymous*|[Polygon](#schemapolygon)|false|none|none|

xor

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|» *anonymous*|[MultiPolygon](#schemamultipolygon)|false|none|none|

continued

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|properties|object|true|none|none|
|» Incumbent|string|false|none|Incumbent party affiliation for more accurate predictions:<br>- R: Republican incumbent<br>- D: Democratic incumbent<br>- O: Open seat (default)|

#### Enumerated Values

|Property|Value|
|---|---|
|type|Feature|
|Incumbent|R|
|Incumbent|D|
|Incumbent|O|

<h2 id="tocS_Polygon">Polygon</h2>
<!-- backwards compatibility -->
<a id="schemapolygon"></a>
<a id="schema_Polygon"></a>
<a id="tocSpolygon"></a>
<a id="tocspolygon"></a>

```json
{
  "type": "Polygon",
  "coordinates": [
    [
      [
        0,
        0
      ]
    ]
  ]
}

```

### Properties

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|type|string|true|none|none|
|coordinates|[array]|true|none|none|

#### Enumerated Values

|Property|Value|
|---|---|
|type|Polygon|

<h2 id="tocS_MultiPolygon">MultiPolygon</h2>
<!-- backwards compatibility -->
<a id="schemamultipolygon"></a>
<a id="schema_MultiPolygon"></a>
<a id="tocSmultipolygon"></a>
<a id="tocsmultipolygon"></a>

```json
{
  "type": "MultiPolygon",
  "coordinates": [
    [
      [
        [
          0,
          0
        ]
      ]
    ]
  ]
}

```

### Properties

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|type|string|true|none|none|
|coordinates|[array]|true|none|none|

#### Enumerated Values

|Property|Value|
|---|---|
|type|MultiPolygon|

<h2 id="tocS_UploadResponse">UploadResponse</h2>
<!-- backwards compatibility -->
<a id="schemauploadresponse"></a>
<a id="schema_UploadResponse"></a>
<a id="tocSuploadresponse"></a>
<a id="tocsuploadresponse"></a>

```json
{
  "index_url": "https://planscore.s3.amazonaws.com/uploads/20210307T032912.752515089Z/index.json",
  "plan_url": "https://planscore.org/plan.html?20210307T032912.752515089Z"
}

```

### Properties

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|index_url|string(uri)|true|none|Machine-readable JSON representation of the plan being scored|
|plan_url|string(uri)|true|none|Human-readable web page with graphs and maps for the plan|

<h2 id="tocS_S3UploadFields">S3UploadFields</h2>
<!-- backwards compatibility -->
<a id="schemas3uploadfields"></a>
<a id="schema_S3UploadFields"></a>
<a id="tocSs3uploadfields"></a>
<a id="tocss3uploadfields"></a>

```json
[
  "http://example.com",
  "http://example.com"
]

```

S3 URL and form fields for pre-signed POST upload

### Properties

oneOf

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|*anonymous*|string(uri)|false|none|S3 upload URL|

xor

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|*anonymous*|object|false|none|Form fields to include in multipart/form-data upload|
|» key|string|false|none|S3 object key pattern|
|» AWSAccessKeyId|string|false|none|AWS access key ID|
|» x-amz-security-token|string|false|none|AWS security token|
|» x-amz-storage-class|string|false|none|S3 storage class|
|» policy|string|false|none|Base64-encoded upload policy|
|» signature|string|false|none|Upload signature|
|» acl|string|false|none|Access control list setting|
|» success_action_redirect|string(uri)|false|none|Redirect URL after successful upload|

<h2 id="tocS_MultistepUploadRequest">MultistepUploadRequest</h2>
<!-- backwards compatibility -->
<a id="schemamultistepuploadrequest"></a>
<a id="schema_MultistepUploadRequest"></a>
<a id="tocSmultistepuploadrequest"></a>
<a id="tocsmultistepuploadrequest"></a>

```json
{
  "description": "A Plan",
  "incumbents": [
    "R",
    "D",
    "O"
  ],
  "model_version": "string",
  "library_metadata": {}
}

```

### Properties

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|description|string|false|none|Short description of the plan|
|incumbents|[string]|false|none|Ordered list of incumbency scenario strings for each district|
|model_version|string|false|none|Predictive model version. If omitted, the first one is used.|
|library_metadata|object|false|none|Additional data to be passed through for possible later use|

<h2 id="tocS_StatesResponse">StatesResponse</h2>
<!-- backwards compatibility -->
<a id="schemastatesresponse"></a>
<a id="schema_StatesResponse"></a>
<a id="tocSstatesresponse"></a>
<a id="tocsstatesresponse"></a>

```json
[
  [
    "XX",
    "congress"
  ]
]

```

List of supported states and legislative bodies

### Properties

*None*

<h2 id="tocS_ModelVersionsResponse">ModelVersionsResponse</h2>
<!-- backwards compatibility -->
<a id="schemamodelversionsresponse"></a>
<a id="schema_ModelVersionsResponse"></a>
<a id="tocSmodelversionsresponse"></a>
<a id="tocsmodelversionsresponse"></a>

```json
[
  [
    "2024-01",
    "2024 Model Version"
  ]
]

```

List of available predictive model versions

### Properties

*None*

<h2 id="tocS_ErrorResponse">ErrorResponse</h2>
<!-- backwards compatibility -->
<a id="schemaerrorresponse"></a>
<a id="schema_ErrorResponse"></a>
<a id="tocSerrorresponse"></a>
<a id="tocserrorresponse"></a>

```json
{
  "message": "Bad GeoJSON input"
}

```

### Properties

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|message|string|true|none|Error message|

