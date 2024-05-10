from typing import NamedTuple
from echo_crafter.config import Config
from echo_crafter.logger import setup_logger
from echo_crafter.utils import play_sound
from echo_crafter.commander.controllers import loader
from echo_crafter.commander.utils import translate_slots, dict_camel_to_snake, camel_to_snake

logger = setup_logger(__name__)

class IntentHandler:
    """Handle the intent and execute the command."""

    class HandleIntentResult(NamedTuple):
        """The result of handling an intent."""
        finished: bool
        extra_arg_required: bool

    def __init__(self, *, controllers_dir: str):
        """Initialize the intent handler.

        Args:
            context_file: The path to the context file.
            CONTROLLERS_DIR: The path to the directory containing the controllers.
        """
        self.context = None
        self.controllers = loader.load(controllers_dir)


    def __call__(self, *, intent: str, slots: dict) -> None:
        """Handle the intent and execute the command.

        Args:
            intent: The intent.
            slots: The slots associated with the intent.
        """
        intent = camel_to_snake(intent)
        params = translate_slots(dict_camel_to_snake(slots))
        controller = self.controllers.get(intent)
        if controller:
            controller(**params)
            play_sound(Config['INTENT_SUCCESS_WAV'])
        else:
            logger.error("No controller found to handle intent: %s", intent)
            raise ValueError(f"Controller for intent {intent} not found")


def initialize(*, controllers_dir: str = Config['CONTROLLERS_DIR']):
    """Create an instance of the intent handler."""
    return IntentHandler(controllers_dir=controllers_dir)
