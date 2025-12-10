import sys
from importlib import metadata
from prompt_toolkit.styles import Style
from prompt_toolkit import print_formatted_text
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit import prompt
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory

from mercury_cli.globals import MERCURY_CLI
from mercury_cli.utils.egg import main as egg_main  # noqa: F401
from mercury_cli.commands.misc.plugins import load_plugins
import mercury_cli.commands  # noqa: F401
import argparse

SPLASH_ART = """
███╗   ███╗███████╗██████╗  ██████╗██╗   ██╗██████╗ ██╗   ██╗      ██████╗██╗     ██╗
████╗ ████║██╔════╝██╔══██╗██╔════╝██║   ██║██╔══██╗╚██╗ ██╔╝     ██╔════╝██║     ██║
██╔████╔██║█████╗  ██████╔╝██║     ██║   ██║██████╔╝ ╚████╔╝█████╗██║     ██║     ██║
██║╚██╔╝██║██╔══╝  ██╔══██╗██║     ██║   ██║██╔══██╗  ╚██╔╝ ╚════╝██║     ██║     ██║
██║ ╚═╝ ██║███████╗██║  ██║╚██████╗╚██████╔╝██║  ██║   ██║        ╚██████╗███████╗██║
╚═╝     ╚═╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═╝   ╚═╝         ╚═════╝╚══════╝╚═╝                                                                                                                                              
"""

# CSS Style for the CLI
cli_style = Style.from_dict(MERCURY_CLI.css())

parser = argparse.ArgumentParser()  # For non interactive commands
parser.add_argument("--no-login", required=False, action="store_true")
args = parser.parse_args()


def show_splash() -> None:
    """
    Prints out the SPLASH_ART and welcome message to the console.
    """

    output = []

    output.append(("class:header", f"{SPLASH_ART}"))
    output.append(
        (
            "class:header",
            "Welcome to mercury_cli",
        )
    )
    output.append(
        (
            "class:version",
            f" v{metadata.version('mercury-cli')}\n",
        )
    )
    output.append(
        ("class:divider", "\n" + "─" * 80 + "\n"),
    )

    print_formatted_text(FormattedText(output), style=cli_style)


def authenticate() -> None:
    """
    Prompts the user for authentication details and authenticates the mercury client.
    """
    username = prompt("Username: ", style=cli_style)
    password = prompt("Password: ", is_password=True, style=cli_style)
    host = prompt(
        "URL (e.g., https://mercury.example.com/webservice/services/ProvisioningService): ",
        style=cli_style,
    )

    MERCURY_CLI.get().client_auth(
        username=username, password=password, host=host, tls=True
    )  # Authenticate mercury client


def main():
    """
    Main entry point for the mercury_cli application.

    Handles user authentication, session creation, and command processing loop.
    """
    show_splash()

    while True:
        try:  # If authentication fails, prompt again
            if not args.no_login:  # Skip login if --no-login is provided
                authenticate()
            break
        except Exception as e:
            print(f"Authentication failed: {e}")
            print("Please try again.\n")
            continue

    MERCURY_CLI.get().session_create(  # Create terminal prompt session
        message="mercury_cli >>> ",
        style=cli_style,
        refresh_interval=1,
        completer=MERCURY_CLI.completer(),
        auto_suggest=AutoSuggestFromHistory(),
    )

    try:
        load_plugins()
    except Exception as e:
        print(f"Plugins failed to load: {e}")

    command_loop()


def command_loop() -> None:
    """
    Main command processing loop for mercury_cli.
    Continuously prompts the user for commands and executes them.

    Raises:
        SystemExit: When the user exits the CLI (e.g., via Ctrl+C or EOF).
        Exception: For any unexpected errors during command execution.

    Returns:
        None

    """
    while True:
        try:
            text = MERCURY_CLI.session().prompt()
            match text.strip():
                case "":  # If command is empty, ignore and re-prompt
                    continue
                case "mercury":  # Hidden easter egg command
                    egg_main()
                    continue
                case _:  # Default case to run any other command
                    try:
                        MERCURY_CLI.completer().run_action(text)
                    except ValueError as ve:
                        # Check if this is actually a "command not found" error
                        if (
                            "not found" in str(ve).lower()
                            or "no action" in str(ve).lower()
                        ):
                            print(
                                f"Unknown command \"{text}\". Type 'help' for a list of commands."
                            )
                        else:
                            # Other ValueError (like spinner terminal size issues)
                            print(f"Error: {ve}")
                    except Exception as e:
                        print(f"Error executing command: {e}")

        except (KeyboardInterrupt, EOFError):
            print("Exiting mercury_cli. Goodbye!")
            MERCURY_CLI.client().disconnect()  # Mercury Client Cleanup
            sys.exit()

        except Exception as e:
            print(f"Error: {e}")
            pass  # Ignore errors so it doesnt crash the cli


if __name__ == "__main__":
    main()
