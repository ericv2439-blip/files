import re
import subprocess
import sys
from pathlib import Path


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).parent


# ============================================================
# COMMAND REGISTRY
# ============================================================

COMMANDS = {
    "coffee.make": {
        "script": BASE_DIR / "coffee.py",

        "arguments": {
            "espresso": 0,
            "americano": 1,
            "cappuccino": 2,
            "mocha": 3,
        },

        "argument_count": 1,
    },

    # More commands can be added here:
    #
    # "message.send": {
    #     "script": BASE_DIR / "message.py",
    #     ...
    # },
}


# ============================================================
# FIND COMMANDS IN LLM OUTPUT
# ============================================================

def find_commands(text):
    """
    Search the entire LLM response for registered commands.

    Example:

        "I'll make that for you.
         coffee.make(mocha)"

    returns:

        [
            ("coffee.make", ["mocha"])
        ]
    """

    found = []

    for command_name, command_info in COMMANDS.items():

        # Escape the command name so dots such as
        # "coffee.make" are treated literally.
        escaped_name = re.escape(command_name)

        pattern = rf"{escaped_name}\(([^)]*)\)"

        matches = re.finditer(pattern, text)

        for match in matches:

            raw_arguments = match.group(1).strip()

            if raw_arguments:
                arguments = [
                    arg.strip()
                    for arg in raw_arguments.split(",")
                ]
            else:
                arguments = []

            found.append(
                (command_name, arguments)
            )

    return found


# ============================================================
# VALIDATE + CONVERT ARGUMENTS
# ============================================================

def prepare_arguments(command_name, arguments):

    command = COMMANDS[command_name]

    expected_count = command["argument_count"]

    if len(arguments) != expected_count:
        print(
            f"[ERROR] {command_name} expects "
            f"{expected_count} argument(s), "
            f"received {len(arguments)}"
        )

        return None

    prepared = []

    argument_map = command.get("arguments")

    for argument in arguments:

        # Convert named values into their internal IDs.
        if argument_map is not None:

            if argument not in argument_map:
                print(
                    f"[ERROR] Invalid argument '{argument}' "
                    f"for {command_name}"
                )

                return None

            argument = argument_map[argument]

        prepared.append(str(argument))

    return prepared


# ============================================================
# RUN SCRIPT
# ============================================================

def execute_command(command_name, arguments):

    command = COMMANDS[command_name]

    script = command["script"]

    if not script.exists():
        print(
            f"[ERROR] Script does not exist: {script}"
        )
        return

    prepared_arguments = prepare_arguments(
        command_name,
        arguments
    )

    if prepared_arguments is None:
        return

    print(
        f"[MAIN] Executing {command_name}"
    )

    print(
        f"[MAIN] Arguments: {prepared_arguments}"
    )

    process = subprocess.Popen(
        [
            sys.executable,
            str(script),
            *prepared_arguments
        ]
    )

    print(
        f"[MAIN] Started process {process.pid}"
    )


# ============================================================
# PROCESS LLM OUTPUT
# ============================================================

def process_llm_output(text):

    print("\n[LLM OUTPUT]")
    print(text)
    print()

    commands = find_commands(text)

    if not commands:
        print("[MAIN] No commands detected.")
        return

    for command_name, arguments in commands:

        print(
            f"[MAIN] Found: "
            f"{command_name}({', '.join(arguments)})"
        )

        execute_command(
            command_name,
            arguments
        )


# ============================================================
# MAIN
# ============================================================

def main():

    print("AI AUTOMATION SYSTEM")
    print("====================")
    print("Waiting for LLM output...\n")

    while True:

        try:

            # Prototype:
            # Enter LLM output manually.
            #
            # Later this can be replaced with
            # the actual Llama/LM Studio output stream.

            text = input("> ")

            if not text.strip():
                continue

            process_llm_output(text)

        except KeyboardInterrupt:
            print("\n[MAIN] Shutting down.")
            break

        except Exception as error:
            print(
                f"[MAIN] Error: {error}"
            )


if __name__ == "__main__":
    main()
