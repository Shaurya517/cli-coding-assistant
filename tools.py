import difflib


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

    confirm = input("Apply this change? (y/n): ").strip().lower()
    if confirm != "y":
        return ("The user REJECTED this edit and does not want it applied. "
                "Do not attempt this same edit again. If you believe this edit is "
                "still necessary, explain why to the user and ask them directly "
                "instead of retrying silently.")

    with open(path, "w") as f:
        f.write(new_content)

    return f"Successfully edited '{path}'."


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

# A lookup table mapping tool names to their actual Python functions.
# This lets assistant.py dispatch calls without a long if/elif chain,
# and makes adding new tools later a one-line addition here.
TOOL_FUNCTIONS = {
    "read_file": read_file,
    "edit_file": edit_file,
}

ALL_TOOL_SCHEMAS = [read_file_tool, edit_file_tool]
