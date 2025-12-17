import sys
from mercury_cli.globals import MERCURY_CLI
from action_completer import Action, ActionParam
from typing import Sequence as sr
from typing import Optional

completer = MERCURY_CLI.completer()
console = MERCURY_CLI.console()


def _get_commands():
    return [(name, action) for name, action in completer.root.children.items()]


def _get_command_names(
    action: Action, param: Optional[ActionParam] = None, value: Optional[sr] = None
):
    """Return list of command names for autocomplete."""
    return [name for name, action in completer.root.children.items()]


def _display_action_heuristics(name: str, action: Action):
    print(f" {name} - {action.display_meta}")

    if action and hasattr(action, "params"):
        for param in action.params:
            print(
                f"\t[Parameter]  {param.display if param.display else 'Unnamed'} - {param.display_meta}"
            )
    if action and hasattr(action, "children"):
        for child_name, child_action in action.children.items():
            _display_action_heuristics(child_name, child_action)


@completer.action("help", display_meta="Gives a list of all commands")
@completer.param(
    _get_command_names,
    cast=str,
    display_meta="Command name to get help for",
)
def _help(command_name: Optional[str] = None):
    if command_name:
        action = completer.root.children.get(command_name)
        if action:
            _display_action_heuristics(command_name, action)
        else:
            print(f"Unknown command: {command_name}")
    else:
        print("Available commands:")
        for name, action in _get_commands():
            print(f"  {name} - {action.display_meta}")


@completer.action("sysver", display_meta="Gives the current system version")
def _sysver():
    version = MERCURY_CLI.client().raw_command("SystemSoftwareVersionGetRequest")
    print(f"Current system version: {version.version}")


@completer.action("exit", display_meta="Exits the CLI")
def _exit():
    print("Exiting mercury_cli. Goodbye!")
    MERCURY_CLI.client().disconnect()
    sys.exit()


@completer.action("clear", display_meta="Clears the terminal screen")
def _clear():
    console.clear()
