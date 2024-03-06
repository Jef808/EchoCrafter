import os
import re
import sys
import json
import yaml
import importlib
from echo_crafter.config import Config
from echo_crafter.logger import setup_logger
from echo_crafter.utils import play_sound


logger = setup_logger(__name__)

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


def load_controllers():
    controllers = {}
    controllers_dir = os.path.join(os.path.dirname(__file__), 'controllers')
    for filename in os.listdir(controllers_dir):
        if filename.endswith('.py') and not filename.startswith('__'):
            module_name = filename[:-3]
            module = importlib.import_module(f'.controllers.{module_name}', package='echo_crafter.commander')
            if hasattr(module, 'execute'):
                controllers[module_name] = module.execute
    return controllers


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
        self.controllers = load_controllers()

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
        controller = self.controllers.get(camel_to_snake(intent))
        if controller:
            controller(slots=slots)
            play_sound(Config['INTENT_SUCCESS_WAV'])
        else:
            logger.error("No controller found to handle intent: %s", intent)
            raise ValueError(f"Controller for intent {intent} not found")

        # if intent in self.intents:
        #     print(f"Executing {intent} with slots {slots}")
        # else:
        #     print(f"Intent {intent} not found in context file")
        #     raise ValueError(f"Intent {intent} not found in context file")


def initialize():
    """Create an instance of the intent handler."""
    return IntentHandler()
