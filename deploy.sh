#!/bin/bash

rm -rf build
rm -rf dist
rm -rf tentacule/tentacule.egg-info

python setup.py sdist bdist_wheel
python -m twine upload -u __token__ -p $PYPI_TOKEN --verbose dist/*

rm -rf build
rm -rf dist
rm -rf tentacule/tentacule.egg-info
