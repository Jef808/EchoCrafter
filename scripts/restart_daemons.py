#!/usr/bin/env python3

"""This script is used to restart the listener and socket_read processes."""

from pathlib import Path
from psutil import Process, process_iter, NoSuchProcess, AccessDenied, ZombieProcess
from shlex import join as shlex_join
from typing import List, Sequence
import subprocess

def search_processes(search_strings: Sequence[str]) -> List[Process]:
    """
    Search for processes that contain the `search_string` in their command line.

    This is a python equivalent of running `pgrep -f SEARCH_STRING` from the shell.

    :param search_string: The string to search for in the command line of the processes.
    """
    matching_processes = []
    for proc in process_iter(attrs=['cmdline']):
        try:
            # The `info` attribute is not part of the `psutil.Process` class, but it is added within the `process_iter` function.
            cmdline = shlex_join(proc.info['cmdline'])  # type: ignore
            if any(search_string in cmdline for search_string in search_strings):
                matching_processes.append(proc)
        except (NoSuchProcess, AccessDenied, ZombieProcess, TypeError):
            pass

    return matching_processes

def get_corresponding_filename(process: Process) -> str:
    """
    Get the filename of the process.

    This is a python equivalent of running `readlink /proc/PID/exe` from the shell.

    :param process: The process to get the filename of.
    """
    try:
        return process.info['cmdline'][1].split('/')[-1]  # type: ignore
    except (NoSuchProcess, AccessDenied, ZombieProcess):
        return ''

def main():
    """Restart the listener and socket_read processes."""
    matching_processes = search_processes(('listener_with_wake_word', 'socket_read'))
    matching_processes_filenames = [get_corresponding_filename(proc) for proc in matching_processes]

    for proc, filename in zip(matching_processes, matching_processes_filenames):
        try:
            proc.terminate()
        except NoSuchProcess:
            pass
        except AccessDenied:
            print(f"No permission to terminate process with PID {proc.pid}.")
        print(f"Terminated {filename}...")

    for filename in ('listener_with_wake_word', 'socket_read'):
        subprocess.Popen(['python', f'echo_crafter/listener/{filename}.py'], cwd=Path(__file__).parent.parent)  # type: ignore
        print(f"Started {filename}.py...")


if __name__ == '__main__':
    main()
