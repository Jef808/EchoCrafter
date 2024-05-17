"""Load controllers from the given directory."""

import os
import subprocess
from pathlib import Path
from echo_crafter.logger import setup_logger

logger = setup_logger(__name__)


def make_controller(script: Path):
    """Make a lambda which will execute the given script.

    Return a function which can be called with python syntax but
    will translate the arguments to the command line syntax.
    """
    def controller(**kwargs):
        long_opts = []
        for k, v in kwargs.items():
            long_opts.extend([f"--{k}", str(v)])
        command = [str(script), *long_opts]
        return subprocess.Popen(command)
    return controller


def load(dir_path: str):
    """Load all the controllers from the given directory.

    Return a dictionary mapping the controller name to
    the controller function.
    """
    controllers = {}

    for executable in filter(
            lambda x: x.is_file() and os.access(str(x), os.X_OK),
            Path(dir_path).glob('*')
    ):
        key = executable.stem
        value = make_controller(executable)
        controllers[key] = value

    return controllers
