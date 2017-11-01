from setuptools import setup, find_packages

packages = find_packages('.', exclude=['src.snapshots'])

setup(
    packages=find_packages('env_config', exclude=['src.snapshots']),
    pbr=True,
    setup_requires=['pbr>=3.1.1'],
)
