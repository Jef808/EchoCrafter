import time
import json
import sys
sys.path.append('os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))')
from openai import OpenAI
from echo_crafter.config import LLMConfig

class OpenAIAPI:
    """OpenAI API client."""

    def __init__(self, SYSTEM_MESSAGES, *, model, max_new_tokens=None, temperature=None):
        """Initialize the OpenAI API client."""
        self.client = OpenAI(api_key=LLMConfig['API_KEY'])
        self.session_id = None
        self.messages = SYSTEM_MESSAGES
        self.temperature = temperature if temperature is not None else 0.4
        self.max_new_tokens = max_new_tokens
        self.model = model
        self.created = time.time()
        self.usage = {'completion_tokens': 0, 'prompt_tokens': 0, 'total_tokens': 0}
        self.cost = 0.0
        self._last_finish_reason = None


    def create_chat_completion(self, message):
        """Create a chat completion."""
        oaimsg_u = {"role": "user", "content": message}
        self.messages.append(oaimsg_u)

        payload = {
            "model": self.model,
            "temperature": self.temperature,
            "messages": self.messages,
            "max_tokens": self.max_new_tokens
        }

        response = self.client.chat.completions.create(**payload)
        self.usage['completion_tokens'] += response.usage.completion_tokens
        self.usage['prompt_tokens'] += response.usage.prompt_tokens
        self.usage['total_tokens'] += response.usage.total_tokens
        self.cost += response.usage.prompt_tokens * LLMConfig['MODELS'][0]['pricing']['input'] / 1_000_000
        self.cost += response.usage.completion_tokens * LLMConfig['MODELS'][0]['pricing']['output']  / 1_000_000

        content = response.choices[0].message.content
        if content:
            oaimsg_a = {"role": "assistant", "content": content}
            self.messages.append(oaimsg_a)

        self._last_finish_reason = response.choices[0].finish_reason

        return content

    def log_session(self):
        """Log the session chat to a file."""
        try:
            log_entry = {
                "timestamp": self.created,
                "model": self.model,
                "temperature": self.temperature,
                "messages": self.messages,
                "usage": self.usage,
                "cost": self.cost,
                "error": None
            }
            with open(LLMConfig['LOG_FILE'], 'a+') as f:
                f.write(json.dumps(log_entry) + '\n')

        except Exception as e:
            print(f"Error occurred while logging session: {e}", file=sys.stderr)
            print("Current messages:", self.messages, file=sys.stderr)


    def is_paused(self):
        """Check if the session is paused."""
        return self._last_finish_reason == 'length'
