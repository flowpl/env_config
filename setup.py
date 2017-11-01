from setuptools import setup, find_packages

setup(
    packages=find_packages('env_config', exclude=['snapshots']),
    pbr=True,
    setup_requires=['pbr>=3.1.1'],
)
