from setuptools import setup

setup(
    name = 'PlanScore',
    url = 'https://github.com/migurski/PlanScore',
    author = 'Michal Migurski',
    description = '',
    packages = ['planscore', 'planscore.tests'],
    test_suite = 'planscore.tests',
    install_requires = [
        'boto3 == 1.4.4',
        ],
    extras_require = {
        'GDAL': ['GDAL == 2.1.3'],
        }
)
