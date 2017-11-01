from setuptools import setup, find_packages

packages = find_packages('.', exclude=['src.snapshots'])

setup(
    packages=packages,
    pbr=True,
    setup_requires=['pbr>=3.1.1'],
)
