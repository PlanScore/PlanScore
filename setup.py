from setuptools import setup

setup(
    name = 'PlanScore',
    url = 'https://github.com/migurski/PlanScore',
    author = 'Michal Migurski',
    description = '',
    packages = [
        'planscore', 'planscore.website', 'planscore.tests', 'planscore.compactness'
        ],
    test_suite = 'planscore.tests',
    package_data = {
        'planscore': ['geodata/*.*', 'model/*.csv.gz'],
        'planscore.website': ['templates/*.html', 'static/*.*'],
        'planscore.tests': [
            'data/*.*',
            'data/*/*/*/*.geojson',
            'data/*/tiles/*/*/*.geojson',
            'data/*/slices/*.json',
            'data/*-graphs/*/*.pickle',
            'data/uploads/sample-plan/districts/?.json',
            'data/uploads/sample-plan/tiles/*/*/*.json',
            'data/uploads/sample-plan/geometries/?.wkt'
            'data/uploads/sample-plan3/slices/*.json',
            'data/uploads/sample-plan3/assignments/?.txt'
            ],
        },
    install_requires = [
        'boto3 == 1.18.1',
        'Flask == 2.0.1',
        'itsdangerous == 2.0.1',
        'Jinja2 == 3.0.1',
        'Markdown == 3.3.4',
        'ModestMaps == 1.4.7',
        'networkx == 2.5.1',
        ],
    extras_require = {
        'compiled': [
            'GDAL == 3.2.1',
            'numpy == 1.21.2',
            ],
        'deploy': [
            'pip >= 21.2.4',
            'aws-cdk.aws-apigateway == 1.122.0',
            'aws-cdk.aws-certificatemanager == 1.122.0',
            'aws-cdk.aws-cloudfront == 1.122.0',
            'aws-cdk.aws-cloudfront-origins == 1.122.0',
            'aws-cdk.aws-iam == 1.122.0',
            'aws-cdk.aws-lambda == 1.122.0',
            'aws-cdk.aws-logs == 1.122.0',
            'aws-cdk.aws-s3 == 1.122.0',
            'aws-cdk.aws-s3-deployment == 1.122.0',
            'aws-cdk.core == 1.122.0',
            'Frozen-Flask == 0.14',
            ],
        'metrics': [
            'google-api-python-client == 2.9.0',
            'oauth2client == 4.1.3',
            ],
        },
    entry_points = dict(
        console_scripts = [
            'planscore-matrix-debug = planscore.matrix:main',
            'planscore-polygonize = planscore.polygonize:main',
            'planscore-prepare-state = planscore.prepare_state:main',
            'planscore-score-locally = planscore.score:main',
            'planscore-update-metrics = planscore.update_metrics:main',
            ]
        ),
)
