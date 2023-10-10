import os
import sys

import nox
from nox import Session

# Only reuse virtualenvs in local testing
environment = {**os.environ}


@nox.session()
def lint(session):
    session.install('flake8')
    session.run('flake8', 'src')
    session.run('flake8', 'tests')


@nox.session
def safety(session):
    session.install('wheel==0.38.*')
    session.install('safety')
    session.run('safety', 'check', '--full-report')


@nox.session()
def tests(session: Session):
    sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)) + os.sep + 'src')

    session.run(sys.executable, "-m", "pip", "install", "-U", "pip")
    session.run(sys.executable, 'setup.py', 'install', env={**environment, 'PYTHONPATH': os.pathsep.join(sys.path)})
    session.run('pytest', 'tests', env={**environment, 'PYTHONPATH': os.pathsep.join(sys.path)})
