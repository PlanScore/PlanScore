# PlanScore

Coming soon.

Install for Local Development
---

PlanScore is a Python 3 application deployed to Amazon Web Services with S3 and
Lambda. To make local development possible, use Docker and the local AWS
development stack [LocalStack](https://github.com/localstack/localstack).

1.  Clone the PlanScore git repository and prepare a
    [Python virtual environment](http://docs.python-guide.org/en/latest/dev/virtualenvs/#virtualenv).

2.  Install GDAL 2.1.3, a binary dependency required by PlanScore.
    
    On Mac, [GDAL is gettable from KyngChaos](http://www.kyngchaos.com/software:frameworks).
    After installing the framework to `/Library/Frameworks/GDAL.framework/Versions/2.1`,
    install GDAL with [custom library and include directories](https://stackoverflow.com/questions/18783390/python-pip-specify-a-library-directory-and-an-include-directory).

        pip3 install \
            --global-option=build_ext \
            --global-option="-I/Library/Frameworks/GDAL.framework/Versions/2.1/Headers" \
            --global-option="-L/Library/Frameworks/GDAL.framework/Versions/2.1/unix/lib" \
            GDAL==2.1.3
    
3.  Install the rest of PlanScore, keeping it editable, and run the test suite.
    
        pip3 install --editable .
        python3 setup.py test
    
4.  [Download and install Docker](https://docs.docker.com/engine/installation/).
    
5.  Get a current Docker image with Lambda Python 3.6 runtime environment.
    
        docker pull lambci/lambda:python3.6
    
6.  In its own Python 3 virtual environment, install LocalStack.
    
        pip3 install localstack
    
7.  In a separate window, run LocalStack.
    
        env SERVICES=s3,lambda LAMBDA_EXECUTOR=docker localstack start
    
    Wait for the expected output.
    
        Starting local dev environment. CTRL-C to quit.
        Starting mock S3 (http port 4572)...
        Starting mock Lambda service (http port 4574)...
        Ready.
    
8.  Build PlanScore dependencies, upload functions to LocalStack Lambda,
    and run the site in debug mode:
    
        make clean localstack-env && ./debug-site.py
