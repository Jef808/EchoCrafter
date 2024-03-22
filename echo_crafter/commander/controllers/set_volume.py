import subprocess

def execute(*, volume_setting=None, percentage=None):
    """Set the volume to the given value."""
    if volume_setting is not None:
        print(f"Setting volume to '{volume_setting}'")
        mute_cmd_id = '0' if volume_setting == 'unmute' else '1'
        subprocess.Popen(
            ["pactl", "set-sink-mute", "@DEFAULT_SINK@", mute_cmd_id]
        )
    elif percentage is not None:
        print(f"Setting volume to {percentage}")

        subprocess.Popen(
            ["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{percentage}"]
        )
    else:
        msg = "Invalid parameters for intent 'setVolume': either `percentage` or `volumeSetting` must be provided"
        raise ValueError(msg)
