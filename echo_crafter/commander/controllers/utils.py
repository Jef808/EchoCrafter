#!/usr/bin/env python3

"""Utility functions for defining command handlers."""

from subprocess import check_output


def current_active_window():
    """Return the class name of the currently active window."""
    return check_output(
        ["xdotool", "getactivewindow", "getwindowclassname"]
    ).decode("utf-8")


def project_directory(project):
    """Return the directory of the given project."""
    return f"~/projects/{project}"
