# PlanScore

Partisan gerrymandering is a deeply undemocratic practice. It produces state
legislatures and congressional delegations that look nothing like the voters
they are meant to represent.

At PlanScore, we will present detailed comparative and historical information
about the partisan asymmetries of past and present district plans. We will also
provide a first-of-its-kind scoring service for new plans, allowing users to
upload maps and instantly receive projected data about their partisan
consequences. Previously, this sort of analysis was available only to the
parties’ line-drawers. Now it will be accessible to everyone, in the process
transforming the politics, litigation, and coverage of redistricting.

Install for Local Testing
---

PlanScore is a Python 3 application deployed to Amazon Web Services with S3,
and Lambda. Code can be tested locally, but the full application can only be
run in AWS Lambda with API Gateway.

1.  Clone the PlanScore git repository and prepare a
    [Python virtual environment](http://docs.python-guide.org/en/latest/dev/virtualenvs/#virtualenv) running Python 3.6.

2.  Install GDAL 3.2.1, a binary dependency required by PlanScore.
    See _GDAL_ section below for more details on operating systems.
    
        pip3 install GDAL==3.2.1

3.  Install the rest of PlanScore, keeping it editable, and run the test suite.
    
        pip3 install --editable '.[compiled]'
        python3 setup.py test

Install on AWS
---

All of PlanScore can be deployed to AWS via Cloudformation. For testing code
on new branches and debugging, use the steps below to create a new set of
stacks. Replace “my-stack-name” with something meaningful but keep the “cf-”
prefix required for all permissions to function.

1.  Install packages needed for deployment.
    
        pip3 install '.[deploy]'
        npm install aws-cdk
        export PATH="${PATH}:${PWD}/node_modules/.bin"
    
2.  Deploy to AWS using AWS-CDK. Two Cloudformation stacks will be created
    by this command, `cf-my-stack-name-Scoring` and `cf-my-stack-name-Content`.
    
        ./cdk-deploy.sh cf-my-stack-name
    
    Deploy script will output a working website base URL when complete, ending
    in “.cloudfront.net”. Stacks can be reviewed and deleted in
    [AWS Console](https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks?filteringStatus=active&filteringText=&viewNested=true&hideStacks=false).

GDAL
---

PlanScore requires GDAL 3.

##### Mac OS X

On Mac, [GDAL is gettable from KyngChaos](http://www.kyngchaos.com/software:frameworks).
After installing the framework to `/Library/Frameworks/GDAL.framework/Versions/3.2`,
install GDAL with [custom library and include directories](https://stackoverflow.com/questions/18783390/python-pip-specify-a-library-directory-and-an-include-directory).

    pip3 install \
        --global-option=build_ext \
        --global-option="-I/Library/Frameworks/GDAL.framework/Versions/3.2/Headers" \
        --global-option="-L/Library/Frameworks/GDAL.framework/Versions/3.2/unix/lib" \
        GDAL==3.2.1

Scoring Process
---

Behind-the-scenes code sequence when a user scores a plan.

1.  User starts at `/upload.html`
2.  Page requests an ID and S3 fields from `/upload` ([λ:`PlanScore-UploadFields`](planscore/upload_fields.py))
3.  User posts file to S3, redirects to `/preread` ([λ:`PlanScore-Preread`](planscore/preread.py))
4.  [λ:`PlanScore-Preread`](planscore/preread.py) prepares upload
    1.  Creates first index JSON
    2.  Invokes [λ:`PlanScore-PrereadFollowup`](planscore/preread_followup.py)
    3.  Redirects user to `/annotate.html{?id}{&bucket}{&key}` to wait
5.  [λ:`PlanScore-PrereadFollowup`](planscore/preread_followup.py) parses upload:
    1.  Guesses state model
    2.  Uploads plan GeoJSON
6.  User posts annotation form with incumbency settings to `/uploaded` ([λ:`PlanScore-PostreadCallback`](planscore/postread_callback.py))
7.  [λ:`PlanScore-PostreadCallback`](planscore/postread_callback.py) invokes [λ:`PlanScore-PostreadCalculate`](planscore/postread_calculate.py) and redirects user to `/plan.html?{id}` to wait
8.  [λ:`PlanScore-PostreadCalculate`](planscore/postread_calculate.py) commences scoring:
    1.  Uploads district geometry WKTs or block assignment lists
    2.  Optionally invokes [λ:`PlanScore-Polygonize`](planscore/polygonize.py)
    3.  Runs Athena query to calculate final scores
    4.  Saves index JSON with final data

### Adding a State

How to add a new state model to the scoring process.

-   Add to `State` enum in [`planscore/data.py`](planscore/data.py)
-   Add to `MODELS` list in [`planscore/data.py`](planscore/data.py)
-   Add to listing and alt text in [`planscore/website/templates/upload.html`](planscore/website/templates/upload.html)
-   Add to `supported` expression in [`design/Upload-Map.qgz`](design/Upload-Map.qgz)
-   Export SVG file from [`design/Upload-Map.qgz`](design/Upload-Map.qgz) to `design/Upload-Map.svg`
-   Compress [`planscore/website/static/supported-states.svg`](planscore/website/static/supported-states.svg) via [`planscore-svg:latest`](SVG):
    
        make planscore/website/static/supported-states.svg
