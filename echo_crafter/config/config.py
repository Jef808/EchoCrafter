"""Set the global configuration for the Echo Crafter project."""

from .config_base import *
from .utils import get_openai_api_key, get_picovoice_api_key

import os
from pathlib import Path

RUNTIME_DIR = Path(os.environ.get('XDG_RUNTIME_DIR', '/tmp'))

DEFAULT_API_KEYS = ApiKeys(
    openai_api_key=get_openai_api_key(),
    picovoice_api_key=get_picovoice_api_key()
)

DEFAULT_DIRECTORIES = Directories(
    project_root=Path(__file__).parent.parent,
    data_dir=Path(__file__).parent.parent / 'data',
    tests_dir=Path(__file__).parent.parent / 'tests',
)

DEFAULT_SOCKETS = Sockets(
    socket_path=str(RUNTIME_DIR / 'echo_crafter.sock')
)

DEFAULT_FILES = Files(
    cheetahModelFile=Path(__file__).parent.parent / 'data' / 'speech-command-cheetah-v1.pv',
    porcupineLaptopKeywordFile=Path(__file__).parent.parent / 'data' / 'laptop_en_linux_v3_0_0.ppn',
    rhinoContextFile=Path(__file__).parent.parent / 'data' / 'computer-commands_en_linux_v3_0_0.rhn',
    transcriptBeginWav=Path(__file__).parent.parent / 'data' / 'transcript_begin.wav',
    transcriptSuccessWav=Path(__file__).parent.parent / 'data' / 'transcript_success.wav'
)

DEFAULT_MICROPHONE_SETTINGS = MicrophoneSettings(
    deviceIndex=-1,
    sampleRate=16000,
    frameLength=512,
    intentCollectionTimeoutSecs=5,
    transcriptCollectionTimeoutSecs=15
)

DEFAULT_ENVIRONMENT_VARIABLES = EnvironmentVariables(
    manualSkipWakeWord='ECHO_CRAFTER_WAIT_FOR_KEYWORD',
    manualSetIntent='ECHO_CRAFTER_INTENT',
    manualSetSlots='ECHO_CRAFTER_SLOTS'
)

def verify_config_types(config: Config) -> bool:
    """Verify that the config object has the correct types."""
    return all(
        all((isinstance(config, section), section_type) for section, section_type in section_types.items())
        for section_types in (
                Directories.__annotations__,
                ApiKeys.__annotations__,
                MicrophoneSettings.__annotations__,
                EnvironmentVariables.__annotations__
        ))


def validate_paths(directories: Directories) -> bool:
    """Validate that all paths exists and are of the correct type."""
    return all(
        (path.exists() and path.is_dir() for path in directories),
        (path.exists() and path.is_file() for path in directories,
        (path.is_socket() for path in directories.socket_path)
    )


def validate_api_keys(api_keys: Config.ApiKeys) -> bool:
    """Validate that all API keys are non-empty strings."""
    OpenAI(api_key=api_keys.openai, max_tokens=0)
    return all(
        (isistance(api_key, str) and api_key for api_key in api_keys)
    )


def is_source_device(device_info: DeviceInfo) -> bool:
    """Verify that the device can record audio."""
    return device_info['maxInputChannels'] > 0


def device_is_compatible(p: PyAudio,
                             device_info: DeviceInfo,
                             sample_rate: int):
        """
        Verify that the device supports the necessary settings for our Microphone stream.

        More precisely, this checks that the device supports streaming at the chosen
        frame rate with uint16 format are supported by the device.
        """
        return p.is_format_supported(
            sample_rate,
            input_device=device_info['index'],
            input_channels=1,
            input_format=paInt16
        )


def verify_device_index(device_index: int) -> bool:
    """Verify that the device index is a valid index."""
    try:
        devnull = os.open(os.devnull, os.O_WRONLY)
        old_stderr = os.dup(2)
        sys.stderr.flush()
        os.dup2(devnull, 2)
        os.close(devnull)

        p = PyAudio()
        device_info = p.get_device_info_by_index(device_index)
        return is_source_device(device_info) and device_is_compatible(p, device_info, MICROPHONE_SETTINGS.sampleRate)
    except Exception as e:
        print(f"An error occurred while verifying the device index {device_index} with PyAudio:", e, file=sys.stderr)
        return False
    finally:
        p.terminate()
        os.close(old_stderr)
        os.dup2(old_stderr, 2)


def validate_microphone_settings(microphone_settings: Config.MicrophoneSettings) -> bool:
    """Validate that all microphone settings are of the correct type."""
    return all(
        (path.exists() and path.is_dir() for path in (microphone_settings.cheetahModelFile, microphone_settings.porcupineLaptopKeywordFile, microphone_settings.rhinoContextFile)),
        (path.exists() and path.suffix == '.wav' for path in (microphone_settings.transcriptBeginWav, microphone_settings.transcriptSuccessWav)),
    )


def verify_environment_variables(
        environment_variables: Config.EnvironmentVariables) -> bool:
    """Do not do anything since all members are optional and arbitrary."""
    return True


_config = Config(
    directories=DIRECTORIES,
    apiKeys=API_KEYS,
    microphoneSettinctgs=MICROPHONE_SETTINGS,
    environmentVariables=ENVIRONMENT_VARIABLES)


def setup_config():
    """Create the Config object."""
    if not verify_config_types(_config):
        raise TypeError("The config object has the wrong types.")

    return _config
