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
        'planscore.tests': ['data/*.*', 'data/*/*/*/*.geojson',
            'data/uploads/sample-plan/districts/?.json',
            'data/uploads/sample-plan/tiles/*/*/*.json',
            'data/uploads/sample-plan/geometries/?.wkt'],
        },
    install_requires = [
        'boto3 == 1.4.4',
        'itsdangerous == 0.24',
        'ModestMaps == 1.4.7',
        'Flask == 0.12.2',
        'Jinja2 == 2.9.6',
        'Frozen-Flask == 0.14',
        'Markdown == 2.6.8',
        ],
    extras_require = {
        'compiled': ['GDAL == 2.1.3', 'numpy == 1.19.2'],
        },
    entry_points = dict(
        console_scripts = [
            'planscore-prepare-state = planscore.prepare_state:main',
            'planscore-empty-queue = planscore.empty_queue:main',
            'planscore-matrix-debug = planscore.matrix:main',
            ]
        ),
)
