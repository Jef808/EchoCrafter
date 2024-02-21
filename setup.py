import platform
import os
from pathlib import Path
from setuptools import setup, find_packages, Command
from setuptools.command.build_py import build_py
import sys

project_root = Path(__file__).parent
venv_dir = os.getenv('VIRTUAL_ENV')

def get_os():
    os_name = platform.system()
    return 'macOS' if os_name == 'Darwin' else os_name

def is_virtual_env():
    return venv_dir is not None

if not is_virtual_env():
    print('This script should be run in a virtual environment')
    print("Please activate a virtual environment before running this script.")
    venv_dir = project_root / '.venv' if (project_root / '.venv').exists() else project_root / 'venv' if (project_root / 'venv').exists() else None
    if not venv_dir:
        print("You can create a virtual environment using:")
        if get_os() == 'Windows':
            print("python -m venv venv")
            venv_dir = project_root / 'venv'
        else:
            print("python -m venv .venv")
            venv_dir = project_root / '.venv'
        print("From the root of the project.")

    print("You can activate your virtual environment using:")
    if get_os() == 'Windows':
        print(f"{venv_dir.relative_to(project_root)}\\Scripts\\activate.bat")
    else:
        print(f"source {venv_dir.relative_to(project_root)}/bin/activate")
    sys.exit(1)

class BuildDocsCommand(Command):
    description = 'Build Sphinx documentation'
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        import subprocess
        docs_dir = project_root / 'docs'
        if not docs_dir.exists() or not docs_dir.is_dir() or not (docs_dir / 'Makefile').exists():
            raise FileNotFoundError('Documentation not found')
        venv_activate = project_root / '.venv/bin/activate'
        if venv_activate.exists():
            subprocess.run(['source', str(venv_activate)], shell=True)
        subprocess.run(['make', 'html'], cwd=docs_dir)

setup(
    name='echo-crafter',
    version='0.1.0',
    packages=find_packages(),
    cmdclass={
        'build_docs': BuildDocsCommand,
        'build_py': build_py
    },
    entry_points={
        'console_scripts': [
            'restart_daemons=scripts.restart_daemons:main',
        ]
    }
)
