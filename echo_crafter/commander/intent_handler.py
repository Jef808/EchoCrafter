"""Handle the intent and execute the command."""

from typing import NamedTuple
from echo_crafter.config import Config
from echo_crafter.logger import setup_logger
from echo_crafter.utils import play_sound
from echo_crafter.commander.controllers import loader
from echo_crafter.commander.utils import format_intent, format_slots
from echo_crafter.commander import dictionary

logger = setup_logger(__name__)


class IntentHandler:
    """Handle the intent and execute the command."""

    class HandleIntentResult(NamedTuple):
        """The result of handling an intent."""
        finished: bool
        extra_arg_required: bool

    def __init__(self, *, controllers_dir: str):
        """Create the intent handler.

        Args:
            context_file: The path to the context file.
            CONTROLLERS_DIR: The path to the directory containing the controllers.
        """
        self.context = None
        self.controllers = loader.load(controllers_dir)

        print("Controllers", self.controllers)

    def __call__(self, *, intent: str, slots: dict) -> None:
        """Handle the intent and execute the command.

        Args:
            intent: The intent.
            slots: The slots associated with the intent.
        """
        intent = format_intent(intent)
        params = format_slots(slots)
        controller = self.controllers[intent]

        if controller:
            controller(**params)
            play_sound(Config['INTENT_SUCCESS_WAV'])
        else:
            logger.error("No controller found to handle intent: %s", intent)
            raise ValueError(f"Controller for intent {intent} not found")


def create(*, controllers_dir: str = Config['CONTROLLERS_DIR']):
    """Create an instance of the intent handler."""
    return IntentHandler(controllers_dir=controllers_dir)
    
