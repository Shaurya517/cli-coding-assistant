import time
import difflib

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


def edit_file(path: str, old_text: str, new_text: str) -> str:
    """Replace an exact snippet of text in a file with new text.
    Requires old_text to match exactly once in the file."""
    try:
        with open(path, "r") as f:
            content = f.read()
    except FileNotFoundError:
        return f"Error: file '{path}' not found."
    except Exception as e:
        return f"Error reading file: {e}"

    count = content.count(old_text)

    if count == 0:
        return (f"Error: could not find the exact text to replace in '{path}'. "
                f"Make sure old_text matches the file exactly, including whitespace.")
    if count > 1:
        return (f"Error: the text to replace appears {count} times in '{path}', "
                f"which is ambiguous. Provide more surrounding context to make it unique.")

    new_content = content.replace(old_text, new_text)

    # --- Show a human-readable diff preview ---
    diff = difflib.unified_diff(
        content.splitlines(keepends=True),
        new_content.splitlines(keepends=True),
        fromfile=f"{path} (before)",
        tofile=f"{path} (after)"
    )
    print("\n--- Proposed change ---")
    print("".join(diff))
    print("------------------------")

    # --- Confirmation gate ---
    confirm = input("Apply this change? (y/n): ").strip().lower()
    if confirm != "y":
        # Be EXPLICIT that this was a deliberate rejection, not a transient
        # failure — otherwise the model may just retry the same edit again.
        return ("The user REJECTED this edit and does not want it applied. "
                "Do not attempt this same edit again. If you believe this edit is "
                "still necessary, explain why to the user and ask them directly "
                "instead of retrying silently.")

    with open(path, "w") as f:
        f.write(new_content)

    return f"Successfully edited '{path}'."


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

edit_file_tool = {
    "name": "edit_file",
    "description": "Replace an exact snippet of existing text in a file with new text. old_text must match exactly (including whitespace) and appear exactly once in the file.",
    "parameters": {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "The relative file path to edit."},
            "old_text": {"type": "string", "description": "The exact existing text to find and replace."},
            "new_text": {"type": "string", "description": "The new text to replace it with."}
        },
        "required": ["path", "old_text", "new_text"]
    }
}

tools = types.Tool(function_declarations=[read_file_tool, edit_file_tool])
config = types.GenerateContentConfig(tools=[tools])

chat = client.chats.create(model="gemini-3.1-flash-lite", config=config)


def send_message_with_retry(chat, message, max_retries=3):
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

        # Keep handling function calls until the model gives us a final text answer.
        while True:
            function_call = None
            for part in response.candidates[0].content.parts:
                if part.function_call:
                    function_call = part.function_call
                    break

            if not function_call:
                break

            print(f"\n[Assistant wants to call: {function_call.name}({dict(function_call.args)})]")

            if function_call.name == "read_file":
                result = read_file(function_call.args["path"])
            elif function_call.name == "edit_file":
                result = edit_file(
                    function_call.args["path"],
                    function_call.args["old_text"],
                    function_call.args["new_text"]
                )
            else:
                result = f"Error: unknown function {function_call.name}"

            function_response = types.Part.from_function_response(
                name=function_call.name,
                response={"result": result}
            )

            try:
                response = send_message_with_retry(chat, function_response)
            except RuntimeError as e:
                print(f"\n[Error: {e}]")
                break

        print(f"\nAssistant: {response.text}")

if __name__ == "__main__":
    main()
