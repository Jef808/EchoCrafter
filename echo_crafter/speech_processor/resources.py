#!/usr/bin/env python3

from pathlib import Path
from contextlib import contextmanager
from pvleopard import LeopardError, create as createLeopard
from pvrhino import RhinoError, create as createRhino
from pvporcupine import KEYWORD_PATHS, PorcupineError, create as createPorcupine
from pvcobra import CobraError, create as createCobra
from pvrecorder import PvRecorder
from echo_crafter.config import Config
from echo_crafter.logger import setup_logger
from typing import Generator

logger = setup_logger(__name__)


def pv_keyword_path(keyword):
    """Get the path to the keyword file for the given keyword."""
    keyword_path = KEYWORD_PATHS.get(keyword, "")
    if not keyword_path:
        for f in Path(Config['DATA_DIR']).glob('*.ppn'):
            print("found file: ", f)
            filename = str(f.stem)
            if filename.startswith(keyword):
                keyword_path = str(f)
                break
    if not keyword_path:
        raise ValueError(f"Keyword file not found for {keyword}")
    return keyword_path


@contextmanager
def create_porcupine(*, sensitivity, wake_word):
    """Create a Porcupine instance and yield it. Delete the instance upon exit."""
    porcupine_instance = None
    try:
        porcupine_instance = createPorcupine(
            keyword_paths=[pv_keyword_path(wake_word)],
            sensitivities=[sensitivity],
            access_key=Config['PICOVOICE_API_KEY']
        )
        yield porcupine_instance
    except (PorcupineError, ValueError) as e:
        logger.error("Porcupine failed to initialize: ", e, exc_info=True)
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
        logger.error("Cobra failed to initialize: ", e, exc_info=True)
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
        logger.error("Leopard failed to initialize: ", e, exc_info=True)
    finally:
        if leopard_instance is not None:
            leopard_instance.delete()


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
        logger.error("Failed to initialize recorder: ", e, exc_info=True)
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
        logger.error("Rhino failed to initialize: ", e, exc_info=True)
    finally:
        if rhino_instance is not None:
            rhino_instance.delete()

