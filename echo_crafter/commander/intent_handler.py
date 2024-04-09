import os
import re
import importlib
from typing import NamedTuple
from echo_crafter.config import Config
from echo_crafter.logger import setup_logger
from echo_crafter.utils import play_sound
from echo_crafter.commander.dictionary import slots_dictionary
from echo_crafter.commander.intents import requires_extra_arg

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
            controllers_dir: The path to the directory containing the controllers.
        """
        self.context = None
        self.controllers = load_controllers(controllers_dir)


    def __call__(self, *, intent: str, slots: dict) -> HandleIntentResult:
        """Handle the intent and execute the command.

        Args:
            intent: The intent.
            slots: The slots associated with the intent.
        """
        intent = camel_to_snake(intent)
        params = dict_camel_to_snake(translate_slots(slots))
        controller = self.controllers.get(intent)
        if controller:
            if requires_extra_arg(intent=intent, slots=params):
                logger.info("Intent requires an extra argument: %s", intent)
                return self.HandleIntentResult(finished=False, extra_arg_required=True)
            controller(**params)
            play_sound(Config['INTENT_SUCCESS_WAV'])
            return self.HandleIntentResult(finished=True, extra_arg_required=False)
        else:
            logger.error("No controller found to handle intent: %s", intent)
            raise ValueError(f"Controller for intent {intent} not found")


def initialize(*, controllers_dir: str = Config['COMMANDS_DIR']):
    """Create an instance of the intent handler."""
    return IntentHandler(controllers_dir=controllers_dir)

def translate_slots(slots: dict) -> dict:
    """Translate the slots to the corresponding values in the dictionary."""
    return {k: slots_dictionary.get(k, {}).get(v, v) for k, v in slots.items()}

def dict_camel_to_snake(d: dict) -> dict:
    """Convert all keys in a dictionary from CamelCase to snake_case."""
    return {camel_to_snake(k): space_to_underscore(v).lower() for k, v in d.items()}

def space_to_underscore(s: str) -> str:
    """Replace spaces with underscores in a string."""
    return re.sub(r'\s', '_', s)

def camel_to_snake(camel_str: str) -> str:
    """
    Convert a string from CamelCase to snake_case.

    Args:
    camel_str (str): The CamelCase string to be converted.

    Returns:
    str: The converted snake_case string.
    """
    # Insert an underscore before any uppercase letter followed by a lowercase letter, then lowercase the entire string
    snake_str = re.sub(r'(?<!^)(?=[A-Z][a-z])', '_', camel_str).lower()
    return snake_str


def load_controllers(dir_path: str):
    """Load all the controllers from the given directory."""
    controllers = {}
    for filename in os.listdir(dir_path):
        if filename.endswith('.py') and not filename.startswith('__'):
            module_name = filename[:-3]
            module = importlib.import_module(f'.controllers.{module_name}', package='echo_crafter.commander')
            if hasattr(module, 'execute'):
                controllers[module_name] = module.execute
    return controllers
