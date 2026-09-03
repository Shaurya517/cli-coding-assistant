import os
import difflib


def ask_yes_no(prompt: str) -> bool:
    """Ask a y/n question, looping until a clear answer is given.
    Returns True for yes, False for no. Treats Ctrl+C as 'no'."""
    while True:
        try:
            answer = input(prompt).strip().lower()
        except KeyboardInterrupt:
            print("\n[Cancelled]")
            return False

        if answer in ("y", "yes"):
            return True
        if answer in ("n", "no"):
            return False

        print("Please answer 'y' or 'n'.")


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

    diff = difflib.unified_diff(
        content.splitlines(keepends=True),
        new_content.splitlines(keepends=True),
        fromfile=f"{path} (before)",
        tofile=f"{path} (after)"
    )
    print("\n--- Proposed change ---")
    print("".join(diff))
    print("------------------------")

    if not ask_yes_no("Apply this change? (y/n): "):
        return ("The user REJECTED this edit and does not want it applied. "
                "Do not attempt this same edit again. If you believe this edit is "
                "still necessary, explain why to the user and ask them directly "
                "instead of retrying silently.")

    with open(path, "w") as f:
        f.write(new_content)

    return f"Successfully edited '{path}'."


def create_file(path: str, content: str) -> str:
    """Create a new file with the given content. Refuses to overwrite an existing file."""
    if os.path.exists(path):
        return (f"Error: '{path}' already exists. Use edit_file if you want to "
                f"modify it, or choose a different path.")

    print(f"\n--- Proposed new file: {path} ---")
    print(content)
    print("------------------------")

    if not ask_yes_no(f"Create '{path}'? (y/n): "):
        return ("The user REJECTED creating this file. Do not attempt to create it "
                "again. Ask the user directly if they want something different.")

    try:
        with open(path, "w") as f:
            f.write(content)
    except Exception as e:
        return f"Error creating file: {e}"

    return f"Successfully created '{path}'."


def delete_file(path: str) -> str:
    """Delete a file, after strong explicit confirmation. This is irreversible."""
    if not os.path.exists(path):
        return f"Error: '{path}' does not exist, nothing to delete."

    print(f"\n!!! DESTRUCTIVE ACTION: this will permanently delete '{path}' !!!")
    print("This cannot be undone by this tool.")

    try:
        confirm = input(f"Type the filename exactly to confirm deletion of '{path}': ").strip()
    except KeyboardInterrupt:
        print("\n[Cancelled]")
        return "The user cancelled the deletion (Ctrl+C). Do not retry."

    if confirm != path:
        return ("The user did NOT confirm deletion (typed filename did not match). "
                "Do not attempt to delete this file again. Ask the user directly "
                "if they still want it deleted.")

    try:
        os.remove(path)
    except Exception as e:
        return f"Error deleting file: {e}"

    return f"Successfully deleted '{path}'."


# --- Schemas: describe the functions above to Gemini ---

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

create_file_tool = {
    "name": "create_file",
    "description": "Create a new file with the given content. Fails if the file already exists.",
    "parameters": {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "The relative path of the new file."},
            "content": {"type": "string", "description": "The full content to write to the new file."}
        },
        "required": ["path", "content"]
    }
}

delete_file_tool = {
    "name": "delete_file",
    "description": "Permanently delete a file. This is irreversible and requires strong user confirmation.",
    "parameters": {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "The relative path of the file to delete."}
        },
        "required": ["path"]
    }
}

# A lookup table mapping tool names to their actual Python functions.
# This lets assistant.py dispatch calls without a long if/elif chain,
# and makes adding new tools later a one-line addition here.
TOOL_FUNCTIONS = {
    "read_file": read_file,
    "edit_file": edit_file,
    "create_file": create_file,
    "delete_file": delete_file,
}

ALL_TOOL_SCHEMAS = [read_file_tool, edit_file_tool, create_file_tool, delete_file_tool]
