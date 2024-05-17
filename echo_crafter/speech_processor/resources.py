#!/usr/bin/env python3

"""Resource management functions for the voice input module."""

from pathlib import Path
from typing import Generator
from contextlib import contextmanager
from importlib import import_module

from pvcheetah import CheetahError, create as createCheetah
from pvleopard import LeopardError, create as createLeopard
from pvrhino import RhinoError, create as createRhino
from pvporcupine import KEYWORD_PATHS, PorcupineError, create as createPorcupine
from pvcobra import CobraError, create as createCobra
from pvrecorder import PvRecorder

from echo_crafter.config import Config
from echo_crafter.logger import setup_logger
from echo_crafter.speech_processor.transcribe_deepgram_file import create as createDeepgram

logger = setup_logger(__name__)


def porcupine_keyword_path(keyword) -> Path:
    """Get the path to the keyword file for the given keyword."""
    if keyword in KEYWORD_PATHS:
        return Path(KEYWORD_PATHS[keyword])
    for f in Path(Config['DATA_DIR']).glob('*.ppn'):
        filename = f.stem
        if filename.startswith(keyword):
            return Path(f)
    return None

def porcupine_model_path_by_language(language):
    """Get the path to the model file for the given language."""
    return Config[f'PORCUPINE_MODEL_FILE_{language.upper()}']


def porcupine_get_paths(keyword):
    """Get the paths to the keyword files for the given keyword."""
    keyword_path = porcupine_keyword_path(keyword)
    if keyword_path is None:
        return None, None

    assert keyword_path.exists(), "Failed to find keyword filepath"

    keyword_filename = keyword_path.stem
    language = keyword_filename.split('_')[1]

    if language == "en":
        return keyword_path, None

    model_path = porcupine_model_path_by_language(language)
    assert Path(model_path).exists(), "Failed to find model filepath for language {language}"

    return keyword_path, model_path


@contextmanager
def create_porcupine(*, wake_word, sensitivity):
    """Create a Porcupine instance and yield it. Delete the instance upon exit."""
    porcupine_instance = None
    try:
        keyword_path, model_path = porcupine_get_paths(wake_word)
        porcupine_instance = createPorcupine(
            keyword_paths=[keyword_path],
            model_path=model_path,
            sensitivities=[sensitivity],
            access_key=Config['PICOVOICE_API_KEY']
        )
        yield porcupine_instance
    except (PorcupineError, ValueError) as e:
        logger.exception("Porcupine failed to initialize: %s", e, exc_info=True)
        raise
    finally:
        if porcupine_instance is not None:
            porcupine_instance.delete()


@contextmanager
def create_cobra():
    """Create a Cobra instance and yield it. Delete the instance upon exit."""
    cobra_instance = None
    try:
        cobra_instance = createCobra(
            access_key=Config['PICOVOICE_API_KEY'],
        )
        yield cobra_instance
    except CobraError as e:
        logger.exception("Cobra failed to initialize: %s", e, exc_info=True)
    finally:
        if cobra_instance is not None:
            cobra_instance.delete()


@contextmanager
def create_leopard(*, model_file=Config['LEOPARD_MODEL_FILE']):
    """Create a Leopard instance and yield it. Delete the instance upon exit."""
    leopard_instance = None
    try:
        leopard_instance = createLeopard(
            access_key=Config['PICOVOICE_API_KEY'],
            model_path=model_file
            )
        yield leopard_instance
    except LeopardError as e:
        logger.exception("Leopard failed to initialize: %s", e, exc_info=True)
    finally:
        if leopard_instance is not None:
            leopard_instance.delete()


@contextmanager
def create_cheetah(*, model_file=Config['CHEETAH_MODEL_FILE']):
    cheetah_instance = None
    try:
        cheetah_instance = createCheetah(
            access_key=Config['PICOVOICE_API_KEY'],
            model_path=model_file
            )
        yield cheetah_instance
    except CheetahError as e:
        logger.exception("Cheetah failed to initialize: %s", e, exc_info=True)
    finally:
        if cheetah_instance is not None:
            cheetah_instance.delete()


@contextmanager
def create_recorder(*, frame_length=Config['FRAME_LENGTH']) -> Generator[PvRecorder, None, None]:
    """Create a PvRecorder instance and yield it. Delete the instance upon exit."""
    recorder_instance = None
    try:
        recorder_instance = PvRecorder(
            frame_length=frame_length,
        )
        yield recorder_instance
    except Exception as e:
        logger.exception("Failed to initialize recorder: %s", e, exc_info=True)
    finally:
        if recorder_instance is not None:
            if recorder_instance.is_recording:
                recorder_instance.stop()
            recorder_instance.delete()


@contextmanager
def create_rhino(*, context_file=Config['RHINO_CONTEXT_FILE'], sensitivity=0.7):
    """Create a PvRecorder instance and yield it. Delete the instance upon exit."""
    rhino_instance = None
    try:
        rhino_instance = createRhino(
            access_key=Config['PICOVOICE_API_KEY'],
            context_path=context_file,
            sensitivity=sensitivity
        )
        yield rhino_instance
    except RhinoError as e:
        logger.exception("Rhino failed to initialize: %s", e, exc_info=True)
    finally:
        if rhino_instance is not None:
            rhino_instance.delete()

@contextmanager
def create_deepgram():
    """Create a DeepgramClient instance and yield it. Delete the instance upon exit."""
    deepgram_instance = None
    try:
        deepgram_instance = createDeepgram(
            access_key=Config['DEEPGRAM_API_KEY']
        )
        yield deepgram_instance
    except Exception as e:
        logger.exception("Deepgram failed to initialize: %s", e, exc_info=True)
