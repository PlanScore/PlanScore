from setuptools import setup

setup(
    name = 'PlanScore',
    url = 'https://github.com/migurski/PlanScore',
    author = 'Michal Migurski',
    description = '',
    packages = ['planscore'],
    install_requires = [
        'boto3 == 1.4.4',
        ]
)
