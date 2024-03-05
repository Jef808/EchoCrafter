import json
import subprocess


def execute(*, slots):
    """Set the volume to the given value."""
    if slots.get('volumeSetting') is not None:
        volume_setting = slots['volumeSetting']
        print(f"Setting volume to '{volume_setting}'")
        mute_cmd_id = '0' if volume_setting == 'unmute' else '1'
        subprocess.Popen(
            ["pactl", "set-sink-mute", "@DEFAULT_SINK@", mute_cmd_id]
        )
    elif slots.get('percentage') is not None:
        percentage = slots['percentage']
        print(f"Setting volume to {percentage}")

        subprocess.Popen(
            ["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{percentage}"]
        )
    else:
        msg = f"Invalid slots for intent 'setVolume': either `percentage` or `volumeSetting` must be provided but got: {json.dumps(slots)}"
        raise ValueError(msg)
