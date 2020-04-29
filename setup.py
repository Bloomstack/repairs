# -*- coding: utf-8 -*-
import ast
import re

from setuptools import find_packages, setup

# get version from __version__ variable in repairs/__init__.py
_version_re = re.compile(r'__version__\s+=\s+(.*)')

with open('repairs/__init__.py', 'rb') as f:
	version = str(ast.literal_eval(_version_re.search(f.read().decode('utf-8')).group(1)))

with open('requirements.txt') as f:
	install_requires = f.read().strip().split('\n')

setup(
	name='repairs',
	version=version,
	description='Repair management app',
	author='DigiThinkIT',
	author_email='rohan@digithinkit.com',
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
