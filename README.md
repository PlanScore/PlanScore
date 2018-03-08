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

Install for Local Development
---

PlanScore is a Python 3 application deployed to Amazon Web Services with S3,
Lambda, and SQS. To make local development possible, use Docker and the local
AWS development stack [LocalStack](https://github.com/localstack/localstack).

1.  Clone the PlanScore git repository and prepare a
    [Python virtual environment](http://docs.python-guide.org/en/latest/dev/virtualenvs/#virtualenv) running Python 3.6.

2.  Install GDAL 2.1.3, a binary dependency required by PlanScore.
    See _GDAL_ section below for more details on operating systems.
    
        pip3 install GDAL==2.1.3

3.  Install the rest of PlanScore, keeping it editable, and run the test suite.
    
        pip3 install --editable .
        python3 setup.py test
    
4.  [Download and install Docker](https://docs.docker.com/engine/installation/).
    
5.  Get a current Docker image with Lambda Python 3.6 runtime environment.
    
        docker pull lambci/lambda:python3.6
    
6.  In its own Python 3 virtual environment, install LocalStack.
    
        pip3 install localstack
    
7.  In a separate window, run LocalStack.
    
        env SERVICES=s3,lambda,sqs LAMBDA_EXECUTOR=docker localstack start
    
    Wait for the expected output.
    
        Starting local dev environment. CTRL-C to quit.
        Starting mock S3 (http port 4572)...
        Starting mock SQS (http port 4576)...
        Starting mock Lambda service (http port 4574)...
        Ready.
    
8.  Build PlanScore dependencies, upload functions to LocalStack Lambda,
    and run the site in debug mode:
    
        make clean localstack-env && ./debug-site.py

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
