from google.genai import types

from api import send_message_with_retry
from tools import TOOL_FUNCTIONS


def main():
    print("CLI Assistant (type 'exit' to quit)")

    while True:
        user_input = input("\nYou: ")

        if user_input.strip().lower() == "exit":
            break

        try:
            response = send_message_with_retry(user_input)
        except RuntimeError as e:
            print(f"\n[Error: {e}]")
            continue

        while True:
            function_call = None
            for part in response.candidates[0].content.parts:
                if part.function_call:
                    function_call = part.function_call
                    break

            if not function_call:
                break

            print(f"\n[Assistant wants to call: {function_call.name}({dict(function_call.args)})]")

            func = TOOL_FUNCTIONS.get(function_call.name)
            if func:
                result = func(**function_call.args)
            else:
                result = f"Error: unknown function {function_call.name}"

            function_response = types.Part.from_function_response(
                name=function_call.name,
                response={"result": result}
            )

            try:
                response = send_message_with_retry(function_response)
            except RuntimeError as e:
                print(f"\n[Error: {e}]")
                break

        print(f"\nAssistant: {response.text}")

if __name__ == "__main__":
    main()
