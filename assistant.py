from dotenv import load_dotenv
load_dotenv()  # reads .env and injects GEMINI_API_KEY into the environment

from google import genai

# The client is our connection to Gemini's API.
# It reads GEMINI_API_KEY from the environment automatically
# (which load_dotenv() just populated from your .env file).
client = genai.Client()

# Gemini's SDK has a concept called a "chat session" that
# handles conversation history FOR us internally — unlike
# raw API calls where we'd manage the messages list ourselves.
# We still need to understand what's happening under the hood though.
chat = client.chats.create(model="gemini-3.6-flash")

def main():
    print("CLI Assistant (type 'exit' to quit)")

    while True:
        user_input = input("\nYou: ")

        if user_input.strip().lower() == "exit":
            break

        # send_message sends this text PLUS the full past history
        # (the SDK tracks it internally in `chat`)
        response = chat.send_message(user_input)

        print(f"\nAssistant: {response.text}")

if __name__ == "__main__":
    main()
