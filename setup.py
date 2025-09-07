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
            'data/*/blocks/*.parquet',
            'data/*-graphs/*/*.pickle',
            'data/uploads/sample-plan/districts/?.json',
            'data/uploads/sample-plan/tiles/*/*/*.json',
            'data/uploads/sample-plan/geometries/?.wkt'
            'data/uploads/sample-plan3/slices/*.json',
            'data/uploads/sample-plan3/assignments/?.txt'
            ],
        },
    install_requires = [
        'boto3 == 1.40.25',
        'Flask == 2.3.3',
        'itsdangerous == 2.2.0',
        'Jinja2 == 3.1.6',
        'Markdown == 3.9',
        'ModestMaps == 1.4.7',
        'networkx == 2.8.8',
        'Werkzeug == 2.3.8',
        ],
    extras_require = {
        'large': [
            'Shapely == 1.7.1',
            ],
        'compiled': [
            'GDAL == 3.8.4',
            'numpy == 1.26.4',
            ],
        'deploy': [
            'pip >= 22',
            'aws-cdk.core == 1.204.0',
            'aws-cdk.aws-stepfunctions == 1.204.0',
            'aws-cdk.aws-s3-deployment == 1.204.0',
            'aws-cdk.aws-s3 == 1.204.0',
            'aws-cdk.aws-logs == 1.204.0',
            'aws-cdk.aws-lambda == 1.204.0',
            'aws-cdk.aws-iam == 1.204.0',
            'aws-cdk.aws-glue == 1.204.0',
            'aws-cdk.aws-cloudfront-origins == 1.204.0',
            'aws-cdk.aws-cloudfront == 1.204.0',
            'aws-cdk.aws-certificatemanager == 1.204.0',
            'aws-cdk.aws-apigateway == 1.204.0',
            'aws-cdk-aws-s3-notifications == 1.204.0',
            'Frozen-Flask == 1.0.2',
            ],
        'metrics': [
            'google-api-python-client == 2.9.0',
            'oauth2client == 4.1.3',
            ],
        'prepare': [
            'geopandas == 0.10.2',
            'pandas == 1.4.1',
            'pyarrow == 6.0.1',
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
