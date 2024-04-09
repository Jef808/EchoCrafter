from echo_crafter.logger import setup_logger
from echo_crafter.prompts import make_script
from .simply_transcribe import _execute as execute_transcription
from typing import Literal

logger = setup_logger(__name__)

def execute():
    """Execute the getAnswer intent."""
    callback = lambda x: make_script.main(x, language=language, model='gpt-4-turbo-preview', temperature=0.4, max_new_tokens=300)
    execute_transcription(callback_final=callback)
