#!/usr/bin/env python3

"""Set the volume to the given value."""

import subprocess
from pathlib import Path


def main(*,
         volume_setting=None,
         percentage=None) -> None:
    """Set the volume to the given value."""
    if volume_setting is not None:
        mute_cmd_id = None
        match volume_setting:
            case "mute":
                print("muting volume")
                mute_cmd_id = '1'
            case "unmute":
                print("Unmuting volume")
                mute_cmd_id = '0'
            case _:
                pass
        if mute_cmd_id is None:
            raise ValueError("Invalid volume setting")
        with subprocess.Popen(
                ["pactl", "set-sink-mute", "@DEFAULT_SINK@", mute_cmd_id],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
        ) as proc:
            stdout, stderr = proc.communicate()
            if stderr.decode("utf-8"):
                raise RuntimeError(f"Error setting volume: {stderr.decode('utf-8')}")
    elif percentage is not None:
        print(f"Setting volume to {percentage}")
        with subprocess.Popen(
            ["pactl", "set-sink-volume", "@DEFAULT_SINK@", percentage],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        ) as proc:
            stdout, stderr = proc.communicate()
            if stderr.decode("utf-8"):
                raise RuntimeError(f"Error setting volume: {stderr.decode('utf-8')}")
    else:
        msg = "Invalid parameters for intent 'setVolume': either `percentage` or `volumeSetting` must be provided"
        raise ValueError(msg)


if __name__ == "__main__":
    import sys
    import argparse

    print(Path(__file__).name, "was executed with", sys.argv[1:])

    parser = argparse.ArgumentParser(description="Set the volume to the given value.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--volume_setting", choices=["mute", "unmute"], help="Set the volume to mute or unmute.")
    group.add_argument("--percentage", type=str, help="Set the volume to the specified percentage.")

    args = parser.parse_args()

    main(volume_setting=args.volume_setting, percentage=args.percentage)
