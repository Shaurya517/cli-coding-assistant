import time

from dotenv import load_dotenv
load_dotenv()

from google import genai
from google.genai import types
from google.genai import errors

client = genai.Client()

def read_file(path: str) -> str:
    """Read and return the contents of a file at the given path."""
    try:
        with open(path, "r") as f:
            return f.read()
    except FileNotFoundError:
        return f"Error: file '{path}' not found."
    except Exception as e:
        return f"Error reading file: {e}"

# This is the SCHEMA — a description of our function, in a format
# Gemini understands. Note: this is NOT our actual function, just
# metadata describing it (name, purpose, expected arguments).
read_file_tool = {
    "name": "read_file",
    "description": "Read and return the contents of a file at the given relative path.",
    "parameters": {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "The relative file path to read, e.g. 'main.py'"
            }
        },
        "required": ["path"]
    }
}

# Tools are grouped and passed into the chat config
tools = types.Tool(function_declarations=[read_file_tool])
config = types.GenerateContentConfig(tools=[tools])

chat = client.chats.create(model="gemini-3.6-flash", config=config)


def send_message_with_retry(chat, message, max_retries=3):
    """Send a message to the chat, retrying on transient server errors."""
    for attempt in range(1, max_retries + 1):
        try:
            return chat.send_message(message)
        except errors.ServerError:
            print(f"\n[Server busy, retrying... attempt {attempt}/{max_retries}]")
            time.sleep(2 * attempt)  # wait longer each retry (2s, 4s, 6s)
    # If we exhausted retries, raise a clear error instead of a deep traceback
    raise RuntimeError("Gemini API is currently unavailable after several retries. Try again in a bit.")


def main():
    print("CLI Assistant (type 'exit' to quit)")

    while True:
        user_input = input("\nYou: ")

        if user_input.strip().lower() == "exit":
            break

        try:
            response = send_message_with_retry(chat, user_input)
        except RuntimeError as e:
            print(f"\n[Error: {e}]")
            continue

        # A response can contain a function call INSTEAD of plain text.
        # We check for that first.
        function_call = None
        for part in response.candidates[0].content.parts:
            if part.function_call:
                function_call = part.function_call
                break

        if function_call:
            print(f"\n[Assistant wants to call: {function_call.name}({dict(function_call.args)})]")

            # We are the ones who actually execute it — the model cannot.
            if function_call.name == "read_file":
                result = read_file(function_call.args["path"])
            else:
                result = f"Error: unknown function {function_call.name}"

            # Send the result back to Gemini so it can form a real answer
            function_response = types.Part.from_function_response(
                name=function_call.name,
                response={"result": result}
            )

            try:
                response = send_message_with_retry(chat, function_response)
            except RuntimeError as e:
                print(f"\n[Error: {e}]")
                continue

        print(f"\nAssistant: {response.text}")

if __name__ == "__main__":
    main()
