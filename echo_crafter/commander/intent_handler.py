import os
import re
import yaml
import importlib
from echo_crafter.config import Config
from echo_crafter.logger import setup_logger
from echo_crafter.utils import play_sound

logger = setup_logger(__name__)

class IntentHandler:
    """Handle the intent and execute the command."""

    def __init__(self, *, context_file: str, controllers_dir: str):
        """Initialize the intent handler.

        Args:
            context_file: The path to the context file.
            controllers_dir: The path to the directory containing the controllers.
        """
        self.context = None

        try:
            with open(context_file, 'r') as f:
                self.context = yaml.safe_load(f)['context']
        except Exception as err:
            logger.error("Error loading context file: %s", str(err))
            raise RuntimeError("Error loading context file.")

        self.controllers = load_controllers(controllers_dir)


    def __call__(self, *, intent: str, slots: dict) -> None:
        """Handle the intent and execute the command.

        Args:
            intent: The intent.
            slots: The slots associated with the intent.
        """
        controller = self.controllers.get(camel_to_snake(intent))
        if controller:
            params = dict_camel_to_snake(slots)
            controller(**params)
            play_sound(Config['INTENT_SUCCESS_WAV'])
        else:
            logger.error("No controller found to handle intent: %s", intent)
            raise ValueError(f"Controller for intent {intent} not found")


def initialize(*, context_file: str = Config['RHINO_CONTEXT_SPEC'], controllers_dir: str = Config['COMMANDS_DIR']):
    """Create an instance of the intent handler."""
    return IntentHandler(context_file=context_file, controllers_dir=controllers_dir)

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
