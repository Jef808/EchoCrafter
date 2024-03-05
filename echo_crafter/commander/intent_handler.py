import json
import yaml
import importlib
import os
import sys

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

controllers = load_controllers()

class IntentHandler:
    """Handle the intent and execute the command."""
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
        controller = controllers.get(intent)
        if controller:
            controller(slots=slots)
        else:
            logger.error("No controller found to handle intent: %s", intent)
            raise ValueError(f"Controller for intent {intent} not found")

        if intent in self.intents:
            print(f"Executing {intent} with slots {slots}")
        else:
            print(f"Intent {intent} not found in context file")
            raise ValueError(f"Intent {intent} not found in context file")


def initialize():
    """Create an instance of the intent handler."""
    return IntentHandler()
