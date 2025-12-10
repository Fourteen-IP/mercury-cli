from action_completer import ActionCompleter
from mercury_ocip import Client
from mercury_ocip import Agent
from prompt_toolkit import PromptSession


class MERCURY_CLI:
    """
    Singleton class for managing the Mercury CLI application.

    This class provides methods for client authentication, agent initialization,
    session creation, and access to key components like the client, session,
    completer, and agent.
    """

    __instance: "MERCURY_CLI" = None
    __completer: ActionCompleter
    __client: Client = None
    __session: PromptSession = None
    __agent: Agent = None

    def __new__(cls: "MERCURY_CLI"):
        """
        Ensures only one instance of MERCURY_CLI is created.
        """
        if not cls.__instance:
            cls.__instance = super(MERCURY_CLI, cls).__new__(cls)
            cls.__instance.__init__()

        return cls.__instance

    def __init__(self):
        """
        Initializes the action completer for the CLI.
        """
        self.__completer = ActionCompleter()
        self.__css = {
            "header": "bold #deaaff",
            "subheader": "bold #d8bbff",
            "version": "bold #c0fdff",
            "divider": "#666666",
            "separator": "#666666",
            "label": "#ffffff",
            "value": "#87d787",
            "success": "#00ff00 bold",
            "toolbar.status": "bg:#005577 #ffffff",
            "toolbar.context": "bg:#333333 #ffffff",
            "prompt": "ansicyan bold #c0fdff",
        }

    def client_auth(self, username: str, password: str, host: str, tls: bool = True):
        """
        Authenticates the client with the provided credentials.

        Args:
            username (str): Username for authentication.
            password (str): Password for authentication.
            host (str): Host address of the server.
            tls (bool): Whether to use TLS for the connection. Defaults to True.
        """
        self.__client = Client(
            username=username, password=password, host=host, conn_type="SOAP", tls=tls
        )
        self.agent_auth()

    def agent_auth(self):
        """
        Initializes the agent using the authenticated client.

        Raises:
            Exception: If the client is not initialized.
        """
        if not self.__client:
            raise Exception("Client not initialized. Call client_auth() first.")
        self.__agent = Agent.get_instance(client=self.__client)

    def session_create(self, **kwargs):
        """
        Creates a new interactive session for the CLI.

        Args:
            **kwargs: Additional arguments for configuring the session.
        """
        self.__session = PromptSession(**kwargs)

    @staticmethod
    def get() -> "MERCURY_CLI":
        """
        Retrieves the singleton instance of MERCURY_CLI.

        Returns:
            MERCURY_CLI: The singleton instance.
        """
        return MERCURY_CLI.__instance

    @staticmethod
    def client() -> Client:
        """
        Retrieves the authenticated client instance.

        Returns:
            Client: The authenticated client.
        """
        return MERCURY_CLI.__instance.__client

    @staticmethod
    def session() -> PromptSession:
        """
        Retrieves the current interactive session.

        Returns:
            PromptSession: The current session instance.
        """
        return MERCURY_CLI.__instance.__session

    @staticmethod
    def completer() -> ActionCompleter:
        """
        Retrieves the action completer instance.

        Returns:
            ActionCompleter: The action completer.
        """
        return MERCURY_CLI.__instance.__completer

    @staticmethod
    def agent() -> Agent:
        """
        Retrieves the initialized agent instance.

        Returns:
            Agent: The initialized agent.
        """
        return MERCURY_CLI.__instance.__agent

    @staticmethod
    def css() -> dict:
        """
        Retrieves the CSS style configuration dictionary.

        Returns:
            dict: The CSS configuration for prompt_toolkit styling.
        """
        return MERCURY_CLI.__instance.__css


MERCURY_CLI()
