import json
import subprocess
from json.decoder import JSONDecodeError
from rich.console import Console
from rich.markdown import Markdown
from typing import Iterable, List, Literal, Optional, Tuple, TypedDict
from anthropic import Anthropic
from anthropic.types import Message as AnthropicResponse

console = Console()


class MessagePart(TypedDict):
    type: Literal['text']
    text: str

MessageContent = List[MessagePart]

class Message(TypedDict):
    role: Literal['system', 'assistant', 'user']
    content: MessageContent


def assistant_message(text: str) -> Message:
    assert text, "Assistant message must not be empty"
    return Message(role="assistant", content=[{"type": "text", "text": text}])


def user_message(text: str) -> Message:
    assert text, "User message must not be empty"
    return Message(role="user", content=[{"type": "text", "text": text}])


def system_message(text: str) -> Message:
    return Message(role="system", content=[{"type": "text", "text": text}])


def extract_system_message(messages: List[Message]) -> Tuple[Optional[Message], List[Message]]:
    search = [(i, msg) for i, msg in enumerate(messages) if msg['role'] == 'system']
    i, sys_msg = search[0] if search else (None, None)
    return sys_msg, (messages[:i] + messages[i+1:] if i is not None else messages)


def make_payload(*, model, messages, max_tokens, **kwargs) -> dict:
    model = {
        "big": "claude-3-opus-20240229",
        "medium": "claude-3-sonnet-20240229",
        "small": "claude-3-haiku-20240229",
    }[model]

    system_message, _messages = extract_system_message(messages)

    kwargs = {k: v for k, v in kwargs.items() if v is not None}

    payload = {
        "model": model,
        "messages": _messages,
        "max_tokens": max_tokens,
        **kwargs
    }

    if system_message is not None and system_message['content'][0]['text']:
        payload['system'] = system_message['content'][0]['text']

    return payload


def prompt_claude_3(
        *,
        client: Optional[Anthropic] = None,
        messages: List[Message] = [],
        model: Literal["big", "medium", "small"] = "medium",
        max_tokens: int = 1000,
        temperature: Optional[float] = None,
        stop_sequences: Optional[List[str]] = None
) -> AnthropicResponse:
    """
    Send a prompt to the Anthropic Claude 3 model and return its response.

    Args:
        prompt (str): The input text to send to the model.

    Returns:
        str: The model's response to the input prompt.
    """
    # Ensure that the ANTHROPIC_API_KEY environment variable is set
    if client is None:
        client = Anthropic()

    payload = make_payload(model=model, messages=messages, max_tokens=max_tokens, temperature=temperature, stop_sequences=stop_sequences)

    import json
    #print(json.dumps(payload, indent=2))

    return client.messages.create(**payload)


if __name__ == "__main__":
    messages = [
        system_message("You are an expert Python programmer."),
        user_message("Write a class which will perform the api requests when interacting with LLM apis. Here is a description of the requirements in a few points:"
                     "- Contains user and assistant message history"
                     "- Allows loading and saving of the message history to an arbitrary endpoint which should be treated as a blackbox for this class"
                     "- Use MessagePack format for saving and loading the message history"
                     "- Is going to be directly accessed by the user interface class for adding new messages and retrieving the list of messages."
                     "- Works asynchronously, integrating with asyncio, including the loading and saving of the message history to a file."
                     "Only write the code for the class, treat everything else as a blackbox."
                     ),
        assistant_message("```python")
    ]

    user_message_text = ""
    stop_sequences = ["```"]

    response = prompt_claude_3(model="big", max_tokens=2000, messages=messages, stop_sequences=stop_sequences)

    print(response.content[0].text.strip())
