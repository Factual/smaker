from setuptools import setup
setup(
    name='smaker',
    version='0.0.1',
    packages=['snakerunner'],
    entry_points={
        'console_scripts': ['smaker=snakerunner.cli:main']
    }
)
