import asyncio
import msgpack

class SessionManager:
    def __init__(self):
        self.messages = []

    async def load_messages(self, endpoint):
        try:
            async with endpoint as e:
                data = await e.read()
                if data:
                    self.messages = msgpack.unpackb(data, raw=False)
        except Exception as e:
            print(f"Error loading messages: {e}")

    async def save_messages(self, endpoint):
        try:
            data = msgpack.packb(self.messages, use_bin_type=True)
            async with endpoint as e:
                await e.write(data)
        except Exception as e:
            print(f"Error saving messages: {e}")

    async def add_user_message(self, message):
        self.messages.append({"role": "user", "content": message})

    async def add_assistant_message(self, message):
        self.messages.append({"role": "assistant", "content": message})

    async def get_messages(self):
        return self.messages

    async def clear_messages(self):
        self.messages = []
