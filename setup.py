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


def raw_install(*packages):
    subprocess.run([sys.executable, '-m', 'pip', 'install', '-U', *packages])
    for p in packages:
        if '=' in p:
            p = p.split('=')[0]
        globals()[p] = importlib.import_module(p)


if __name__ == '__main__':
    raw_install('pip', 'setuptools', 'wheel', 'envsubst', 'pytest', 'nox')

    with substituted_config() as (template, substituted):
        configs = configparser.ConfigParser()
        configs.read_string(substituted)
        requirements = configs['options']['install_requires'].split('\n')[1:]
        # test_requirements = configs['options']['install_test_requires'].split('\n')[1:]

        if len(sys.argv) == 2 and sys.argv[1] == 'install':
            raw_install(*requirements)
            # gitlab_install(personal_access_token, *test_requirements)
        else:
            setup(
                install_requires=requirements
            )
