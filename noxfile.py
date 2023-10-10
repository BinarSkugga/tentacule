import os
import sys

import nox
from nox import Session

IN_CI = 'GITLAB_CI' in os.environ
PARALLEL = os.environ.get('TEST_PARALLEL', 'false') == 'true'
# Only reuse virtualenvs in local testing
nox.options.reuse_existing_virtualenvs = not IN_CI
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

    if PARALLEL:
        session.install('pytest-xdist')
        num_proc = os.environ.get('TEST_NUM_PROCESSES', '8')
        num_proc = int(num_proc) if num_proc != 'auto' else 'auto'
        session.run('pytest', '--cov-config=.coveragerc', '--dist=loadfile', f'--numprocesses={num_proc}',
                    '--tx', 'popen//python=python', '--cov=src', '--junitxml=tests/report.xml', 'tests',
                    env={**environment, 'PYTHONPATH': os.pathsep.join(sys.path)})
    else:
        session.run('pytest', 'tests', env={**environment, 'PYTHONPATH': os.pathsep.join(sys.path)})

