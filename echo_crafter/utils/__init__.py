#!/usr/bin/env python3

def play_sound(wav_file):
    """Play a sound file."""
    import subprocess
    subprocess.Popen(["aplay", "-q", wav_file])
