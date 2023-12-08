import pyaudio
import numpy as np
import sys
import json

def list_microphone_names():
    """
    Returns a list of the names of all available microphones. For microphones where the name can't be retrieved, the list entry contains ``None`` instead.

    The index of each microphone's name in the returned list is the same as its device index when creating a ``Microphone`` instance - if you want to use the microphone at index 3 in the returned list, use ``Microphone(device_index=3)``.
    """
    audio = pyaudio.PyAudio()
    try:
        result = []
        for i in range(audio.get_device_count()):
            device_info = audio.get_device_info_by_index(i)
            result.append(device_info.get("name"))
    finally:
        audio.terminate()
    return result


def rms(np_array):
    d = np_array.astype(float)
    return np.sqrt(np.mean(d**2))


def list_working_microphones():
    """
    Returns a dictionary mapping device indices to microphone names, for microphones that are currently hearing sounds. When using this function, ensure that your microphone is unmuted and make some noise at it to ensure it will be detected as working.

    Each key in the returned dictionary can be passed to the ``Microphone`` constructor to use that microphone. For example, if the return value is ``{3: "HDA Intel PCH: ALC3232 Analog (hw:1,0)"}``, you can do ``Microphone(device_index=3)`` to use that microphone.
    """
    audio = pyaudio.PyAudio()
    try:
        result = {}
        for device_index in range(audio.get_device_count()):
            device_info = audio.get_device_info_by_index(device_index)
            device_name = device_info.get("name")
            assert isinstance(device_info.get("defaultSampleRate"), (float, int)) and device_info["defaultSampleRate"] > 0, "Invalid device info returned from PyAudio: {}".format(device_info)
            try:
                # read audio
                pyaudio_stream = audio.open(
                    input_device_index=device_index, format=pyaudio.paInt16,
                    rate=int(device_info["defaultSampleRate"]), input=True
                )
                try:
                    buffer = pyaudio_stream.read(1024)
                finally:
                    if not pyaudio_stream.is_stopped(): pyaudio_stream.stop_stream()
                    pyaudio_stream.close()
            except Exception as e:
                print(f"Exception while opening {device_name}: {e}", file=sys.stderr)
                continue

            print(f"Starting debiased energy computation for {device_name}", file=sys.stderr)

            # compute RMS of debiased audio
            data = np.frombuffer(buffer, np.int16)
            energy = -int(rms(data))
            energy_bytes = np.array([energy] * len(data), np.int16)
            debiased_energy = rms(data + energy_bytes)

            if debiased_energy > 30:  # probably actually audio
                result[device_index] = device_name
                print(f"** Working device found: {device_name}")
    finally:
        audio.terminate()
    return result


if __name__ == '__main__':
    microphone_names = list_microphone_names()
    working_microphones = list_working_microphones()
    print("Microphone names:", "\n  ".join(microphone_names))
    print("Working microphones:", "\n  ".join(json.dumps(microphone, indent=2) for microphone in working_microphones))
