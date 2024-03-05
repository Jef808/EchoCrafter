import json
import yaml
from .controllers import (
    focus_window,
    open_window,
    set_volume,
    transcribe,
    get_script,
)
from echo_crafter.config import Config
from echo_crafter.logger import setup_logger

logger = setup_logger(__name__)

class IntentHandler:
    """Handle the intent and execute the command."""

    def __init__(self, context_file: str = Config['RHINO_CONTEXT_SPEC']):
        """Initialize the intent handler.

        Args:
            context_file: The path to the context file.
        """
        self.context = None

        try:
            with open(context_file, 'r') as f:
                self.context = yaml.safe_load(f)['context']
        except Exception as err:
            logger.error("Error loading context file: %s", str(err))
            raise RuntimeError("Error loading context file.")

        self.intents = list(self.context['expressions'].keys())
        self.slots = self.context['slots']

        print("Context specs: ")
        print(json.dumps(self.context, indent=2))
        print("Intents: ")
        print(json.dumps(self.intents, indent=2))
        print("Slots: ")
        print(json.dumps(self.slots, indent=2))


    def __call__(self, *, intent: str, slots) -> None:
        """Handle the intent and execute the command.

        Args:
            intent: The intent.
            slots: The slots associated with the intent.
        """
        print(f"Handling intent: {intent}")
        print(f"With slots: {slots}")

        match intent:
            case 'getScript':
                get_script.execute(slots=slots)
            case 'answerQuestion':
                pass
            case 'simplyTranscribe':
                transcribe.execute(slots=slots)
            case 'focusWindow':
                focus_window.execute(slots=slots)
            case 'openWindow':
                open_window.execute(slots=slots)
            case 'setVolume':
                set_volume.execute(slots=slots)
            case 'cancel':
                pass
            case _:
                logger.error("No implementation known to handle intent: %s", intent)
                raise ValueError(f"Intent {intent} not found in context file")

        if intent in self.intents:
            print(f"Executing {intent} with slots {slots}")
        else:
            print(f"Intent {intent} not found in context file")
            raise ValueError(f"Intent {intent} not found in context file")


def initialize():
    """Create an instance of the intent handler."""
    return IntentHandler()
