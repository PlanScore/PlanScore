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

2.  Install GDAL 2.1.3, a binary dependency required by PlanScore.
    See _GDAL_ section below for more details on operating systems.
    
        pip3 install GDAL==2.1.3

3.  Install the rest of PlanScore, keeping it editable, and run the test suite.
    
        pip3 install --editable .
        python3 setup.py test

4.  Deploy to [dev.planscore.org](https://dev.planscore.org).
    
        make dev-website dev-lambda

GDAL
---

PlanScore requires GDAL 2.

##### Mac OS X

On Mac, [GDAL is gettable from KyngChaos](http://www.kyngchaos.com/software:frameworks).
After installing the framework to `/Library/Frameworks/GDAL.framework/Versions/2.1`,
install GDAL with [custom library and include directories](https://stackoverflow.com/questions/18783390/python-pip-specify-a-library-directory-and-an-include-directory).

    pip3 install \
        --global-option=build_ext \
        --global-option="-I/Library/Frameworks/GDAL.framework/Versions/2.1/Headers" \
        --global-option="-L/Library/Frameworks/GDAL.framework/Versions/2.1/unix/lib" \
        GDAL==2.1.3

##### Ubuntu 17 (Artful Aardvark)

Repositories already offer GDAL 2:

    sudo apt install gdal-bin libgdal-dev python3-gdal

##### Ubuntu 16 (Xenial Xerus)

Ubuntu 16 repositories offer GDAL 1, but GDAL 2 is in
[UbuntuGIS unstable PPA](https://launchpad.net/~ubuntugis/+archive/ubuntu/ubuntugis-unstable).
Add the unstable PPA and upgrade:

    # GDAL 2 utilities and headers
    sudo add-apt-repository -y ppa:ubuntugis/ubuntugis-unstable
    sudo apt update
    sudo apt upgrade
    sudo apt install gdal-bin libgdal-dev python3-gdal

    # within the virtualenv, set these environment variables when pip tries
    # to compile the new GDAL these will tell it where to find headers + libs
    export CPLUS_INCLUDE_PATH=/usr/include/gdal
    export C_INCLUDE_PATH=/usr/include/gdal
    pip3 install gdal==2.1.3

##### GDAL From Source

Alternately, you may install GDAL from source and into some specific
subdirectory. That usually includes a bunch of other libraries depending on the
formats you want to support.

This technique could be attractive if you are running an OS whose repositories
do not offer GDAL 2, but you're reluctant to update to unstable packages.

Once that is done, within the virtualenv you will need to export some
environment variables, as described in Ubuntu 16.

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
    1.  Uploads district geometry WKTs
    2.  Loads model tiles
    3.  Invokes [λ:`PlanScore-ObserveTiles`](planscore/observe.py)
    4.  Fans out [λ:`PlanScore-RunTile`](planscore/tiles.py)
9.  [λ:`PlanScore-RunTile`](planscore/tiles.py) aggregates district statistics in tile, saves results to S3
10. [λ:`PlanScore-ObserveTiles`](planscore/observe.py) scores plan:
    1.  Waits for all expected aggregated tile statistics
    2.  Calculates final scores
    3.  Saves index JSON with final data

### Adding a State

How to add a new state model to the scoring process.

-   Add to `State` enum in [`planscore/data.py`](planscore/data.py)
-   Add to `MODELS2020` list in [`planscore/data.py`](planscore/data.py)
-   Add to `STATE` enum in [`planscore/matrix.py`](planscore/matrix.py)
-   Add to listing and alt text in [`planscore/website/templates/upload.html`](planscore/website/templates/upload.html)
-   Add to `supported` expression in [`design/Upload-Map.qgz`](design/Upload-Map.qgz)
-   Export SVG file from [`design/Upload-Map.qgz`](design/Upload-Map.qgz) to `design/Upload-Map.svg`
-   Compress [`planscore/website/static/supported-states.svg`](planscore/website/static/supported-states.svg) via [`planscore-svg:latest`](SVG):
    
        make planscore/website/static/supported-states.svg
