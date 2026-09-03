import time

from dotenv import load_dotenv
load_dotenv()

from google import genai
from google.genai import types
from google.genai import errors

from tools import ALL_TOOL_SCHEMAS

client = genai.Client()

tools = types.Tool(function_declarations=ALL_TOOL_SCHEMAS)
config = types.GenerateContentConfig(tools=[tools])

chat = client.chats.create(model="gemini-3.1-flash-lite", config=config)


def send_message_with_retry(message, max_retries=3):
    """Send a message to the chat, retrying on transient server errors.
    Quota errors are NOT retried since they won't resolve by waiting seconds."""
    for attempt in range(1, max_retries + 1):
        try:
            return chat.send_message(message)
        except errors.ServerError:
            print(f"\n[Server busy, retrying... attempt {attempt}/{max_retries}]")
            time.sleep(2 * attempt)
        except errors.ClientError as e:
            if "RESOURCE_EXHAUSTED" in str(e) or "429" in str(e):
                raise RuntimeError(
                    "Daily free-tier quota exceeded for this model. "
                    "Wait for it to reset, or switch to a different model."
                )
            raise
    raise RuntimeError("Gemini API is currently unavailable after several retries. Try again in a bit.")
