from echo_crafter.logger import setup_logger
from echo_crafter.config import Config
from echo_crafter.prompts import make_script
from .simply_transcribe import _execute as execute_transcription

logger = setup_logger(__name__)

def execute(*, slots):
    """Execute the getScript intent."""
    language = slots.get('language', 'python')

    transcript = []

    callback = lambda x: transcript.append(x)

    execute_transcription(callback=callback)

    query = ''.join(transcript)

    make_script.main(query, language=language, model='gpt-4-turbo-preview', temperature=0.4, max_new_tokens=300)
