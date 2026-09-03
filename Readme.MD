# CLI Coding Assistant

A small, from-scratch command-line coding assistant — a tiny clone of the core
mechanics behind tools like Claude Code. It can read files in your project,
propose edits, create new files, and delete files, but **nothing ever touches
disk without your explicit confirmation.**

Built in Python using Google's Gemini API (free tier).

## Author

**Shaurya Pathak**

## What it does

- Chat with an LLM in your terminal, with full conversation memory
- Ask it to read files in your project so it has real context
- Ask it to edit a file — it proposes an exact text replacement, shows you a
  `git diff`-style preview, and only writes the change if you approve
- Ask it to create a new file — shows you the content first, refuses to
  silently overwrite an existing file
- Ask it to delete a file — the highest-risk action, so instead of a simple
  yes/no, you must type the **exact filename** to confirm

## How it works

Every "action" (reading, editing, creating, deleting a file) is exposed to the
model as a **tool** it can request to use. The model never touches your
filesystem directly — it can only ask. This program is the one that decides,
on your behalf, whether to actually run it:

```
You ask something
  → model decides it needs a tool (e.g. read_file)
  → this program runs the real Python function
  → result goes back to the model
  → (repeat if more tools are needed)
  → model gives you a final answer
```

Edits, creations, and deletions all pause here and ask you first — that's the
whole point of the project.

## Project structure

```
.
├── assistant.py     # the main chat loop
├── api.py           # Gemini client setup + retry/error handling
├── tools.py         # read/edit/create/delete file tools + their schemas
├── requirements.txt
├── .gitignore
└── .env             # your API key (not committed — see below)
```

## Setup

1. **Clone the repo and enter it**
   ```bash
   git clone https://github.com/Shaurya517/cli-coding-assistant.git
   cd cli-coding-assistant
   ```

2. **Create and activate a virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate      # macOS/Linux
   venv\Scripts\activate         # Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Add your API key**

   Get a free key from [Google AI Studio](https://aistudio.google.com/app/apikey),
   then create a `.env` file in the project root:
   ```
   GEMINI_API_KEY=your-actual-key-here
   ```
   This file is git-ignored and never committed.

5. **Run it**
   ```bash
   python assistant.py
   ```

## Example session

```
CLI Assistant (type 'exit' to quit)

You: In app.py, change 'hello' to 'world'

[Assistant wants to call: read_file({'path': 'app.py'})]
[Assistant wants to call: edit_file({'path': 'app.py', 'old_text': "print('hello')\n", 'new_text': "print('world')\n"})]

--- Proposed change ---
--- app.py (before)
+++ app.py (after)
@@ -1 +1 @@
-print('hello')
+print('world')
------------------------
Apply this change? (y/n): y

Assistant: The file app.py has been updated to print 'world'.
```

## Safety design

| Action | Safeguard |
|---|---|
| `read_file` | Read-only, no confirmation needed |
| `edit_file` | Refuses if the target text is missing or ambiguous (appears more than once); shows a diff; requires y/n |
| `create_file` | Refuses to overwrite an existing file; shows content preview; requires y/n |
| `delete_file` | Requires typing the **exact filename** to confirm — not just y/n, since deletion is irreversible |

The confirmation prompts also handle:
- Unclear input (e.g. typing `maybe`) — re-asks instead of guessing
- `Ctrl+C` mid-prompt — cancels cleanly, no crash, nothing written
- Empty input at the main prompt — silently ignored, no wasted API call

## Notes

- Uses Google's Gemini free tier, which has daily request quotas per model. If
  you hit a `429` quota error, the assistant will tell you clearly rather than
  retrying — you can wait for the quota to reset or switch the model name in
  `api.py`.
- This is a learning/educational project, not a production tool. It's scoped
  deliberately small to focus on the core agent-loop and safety mechanics.

## Possible future additions

- A `list_files` tool so the model doesn't have to guess paths
- A session-level "trust mode" to skip confirmations for a batch of changes
- Persisting conversation history across runs
- A fallback to a second LLM provider if the free-tier quota runs out
