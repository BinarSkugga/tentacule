import os
import configparser
import subprocess
import sys
import importlib
from contextlib import contextmanager

from setuptools import setup


@contextmanager
def substituted_config():
    with open('setup.cfg', 'r') as cfg:
        template_cfg = cfg.read()

    if '\n' in template_cfg:
        template_cfg = template_cfg.replace('\r', '')
    else:
        template_cfg = template_cfg.replace('\r', '\n')

    try:
        from envsubst import envsubst
        substituted_config_text = envsubst(template_cfg)
        with open('setup.cfg', 'w') as cfg:
            cfg.write(substituted_config_text)

        yield template_cfg, substituted_config_text
    finally:
        with open('setup.cfg', 'w') as cfg:
            cfg.write(template_cfg)


def set_envs(env: str = None, pypi_user: str = None, pypi_password: str = None, pypi_url: str = None):
    os.environ['ENV'] = env or os.environ.get('ENV', 'develop')
    os.environ['PYPI_USER'] = pypi_user or os.environ.get('PYPI_USER', 'gitlab-ci-token')
    os.environ['GITLAB_TOKEN'] = pypi_password or os.environ.get('GITLAB_TOKEN', '')
    os.environ['PYPI_URL'] = pypi_url or os.environ.get('PYPI_URL', 'gitlab.com/api/v4/projects/23814428/packages/pypi')
    os.environ['PYPI_DEPLOY_USERNAME'] = os.environ.get('PYPI_DEPLOY_USERNAME', os.environ['PYPI_USER'])
    os.environ['PYPI_DEPLOY_PASSWORD'] = os.environ.get('PYPI_DEPLOY_PASSWORD', os.environ['GITLAB_TOKEN'])
    os.environ['DEPENDENCY_LINK'] = f'https://' \
                                    f'{os.environ["PYPI_DEPLOY_USERNAME"]}:{os.environ["PYPI_DEPLOY_PASSWORD"]}@' \
                                    f'{os.environ["PYPI_URL"]}/simple'


def raw_install(*packages):
    subprocess.run([sys.executable, '-m', 'pip', 'install', '-U', *packages])
    for p in packages:
        globals()[p] = importlib.import_module(p)


def gitlab_install(token: str, *requires: str):
    url = f'https://{os.environ["PYPI_USER"]}:{token}@{os.environ["PYPI_URL"]}/simple'
    completed_process = subprocess.run(
        [sys.executable, '-m', 'pip', 'install', '-U', f'--extra-index-url={url}', *requires])
    if completed_process.returncode != 0:
        raise RuntimeError('Could not install successfully')


if __name__ == '__main__':
    set_envs()
    raw_install('pip', 'setuptools', 'wheel', 'envsubst', 'pytest', 'nox')

    with substituted_config() as (template, substituted):
        configs = configparser.ConfigParser()
        configs.read_string(substituted)
        requirements = configs['options']['install_requires'].split('\n')[1:]
        # test_requirements = configs['options']['install_test_requires'].split('\n')[1:]

        if len(sys.argv) == 2 and sys.argv[1] == 'install':
            personal_access_token = os.environ['GITLAB_TOKEN']
            if len(personal_access_token) == 0:
                personal_access_token = input('Please provide your personal access token: ')

            gitlab_install(personal_access_token, *requirements)
            # gitlab_install(personal_access_token, *test_requirements)
        else:
            setup(
                install_requires=requirements
            )
