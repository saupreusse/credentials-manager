"""This module implements functions and classes that can be used to create clients
that use mutual authentication to connect & communicate with the CM server using secure SSL sockets."""
import ssl
import socket
import json
from jsonschema import validate, ValidationError

# Schema which specifies the client-server communication.
PROTOCOLSCHEMA = {
    "type": "object",
    "properties": {
        "header": {
            "type": "object",
            "properties": {
                "cmUser": {"type": "string"},
                "cmPassword": {"type": "string"},
                "cmRequest": {"type": "string"},
            },
            "required": ["cmUser", "cmPassword", "cmRequest"],
        },
        "payload": {
            "type": "object",
            "properties": {"args": {"type": "object"}},
            "required": ["args"],
        },
    },
    "required": ["header", "payload"],
}


def _validatePacket(packet: str) -> bool:
    """Validates if a message form follows protocol guidelines.

    Args:
        message (dict): Message to validate, received from client.

    Returns:
        bool: True if the message is valid, else False.
    """
    try:
        packet = json.loads(packet)
        validate(instance=packet, schema=PROTOCOLSCHEMA)
        return True
    except ValidationError as e:
        raise CmError(f"Packet validation failed: {e}")


class Client:
    """This class contains all necessary methods to create a SSL/TLS socket as client endpoint for communication
    with the Credentials Manager Server, by providing the necessary configuration information in form of SSLConfig objects.
    The methods used for communication with the server over raw sockets implement a json message format that both the client and server can understand.
    This allows them to interpret and respond to messages correctly.
    """

    def __init__(
        self,
        caCert: str,
        clientCert: str,
        clientKey: str,
        serverHost: str,
        serverPort: int,
        cmUser: str,
        cmPassword: str,
    ):
        """Initializes SSLConfig objects

        Args:
            caCert (str): Path to the server's CA certificate
            clientCert (str): Path to the client's certificate
            clientKey (str): Path to the client's private key
            serverHost (str): Server's hostname or IP
            serverPort (int): Server's listen port
            cmUser (str): CM username
            cmPassword(str) : CM user password
        """
        self.caCert = caCert
        self.clientCert = clientCert
        self.clientKey = clientKey
        self.serverHost = serverHost
        self.serverPort = serverPort
        self.cmUser = cmUser
        self.cmPassword = cmPassword

    def __str__(self):
        return f"{self.caCert}, {self.clientCert}, {self.serverHost}, {self.serverPort}, {self.cmUser}"

    def _createSSLSocket(self):
        """Establishes a SSL/TLS connection with the parameters specified in the instance.
        CM client (webapp) and CM Server use mutual authentication.

        Args:
            self (Client): Client Object containing the SSL/TLS & Client configuration

        Returns:
            SSLSocket: Socket wrapped in SSL/TLS context
        """
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
            context.load_verify_locations(self.caCert)
            context.load_cert_chain(certfile=self.clientCert, keyfile=self.clientKey)
            context.verify_mode = ssl.CERT_REQUIRED
            context.minimum_version = ssl.TLSVersion.TLSv1_3
            sslsock = context.wrap_socket(
                client_socket, server_hostname=self.serverHost
            )
            return sslsock
        except Exception as e:
            raise CmError(f"Error building SSL socket: {e}")

    def _createPacket(self, request):
        """Creates a CM packet to be sent to the server.

        Args:
            request (tuple): A request containing the Request type and arguments.

        Returns:
            str: A CM packet.
        """

        packet = {
            "header": {
                "cmUser": self.cmUser,
                "cmPassword": self.cmPassword,
                "cmRequest": request[0],
            },
            "payload": {"args": request[1]},
        }

        return json.dumps(packet)

    def execute(self, request):
        """Executes a client request by sending a CM packet to the CM server and waiting for a response.

        Args:
            request (tuple): Request to be executed.

        Returns:
            response (str): The Server's response.

        Raises:
            CmError: Error while executing request.
            CmError: Corrupt packet structure.
        """
        # Create a packet following protocol format
        packet = self._createPacket(request)
        sslSocket = None
        if _validatePacket(packet):
            try:
                sslSocket = self._createSSLSocket()

                # Open connection & exchange packets
                sslSocket.connect((self.serverHost, self.serverPort))
                sslSocket.sendall(packet.encode())
                response = sslSocket.recv(1024)
                return _interpretResponse(response.decode())
            except Exception as e:
                raise CmError(f"Error while executing request: {e}")
            finally:
                # Close the connection
                if sslSocket:
                    sslSocket.close()
        else:
            raise CmError(f"Error while executing request: Corrupt packet structure.")


def createClient(userConfigPath="/opt/credentials_manager/cm_config.json"):
    """Returns a Client object using the parameters inside the config file.

    Args:
        userConfigPath (str): Path to the cm_config.json

    Returns:
        Client : Client object.

    Raises:
        CmError : Error loading client configuration.
    """
    try:
        with open(userConfigPath, "r") as f:
            data = json.load(f)
            return Client(
                caCert=data["ca_cert"],
                clientCert=data["client_cert"],
                clientKey=data["client_key"],
                serverHost=data["server_host"],
                serverPort=data["server_port"],
                cmUser=data["client_username"],
                cmPassword=data["client_password"],
            )
    except Exception as e:
        raise CmError(f"Can't load CM client configuration: {e}")


def _interpretResponse(response):
    """Simple response interpreter for CM responses received by the client.
    X00 responses are error messages from the server, which means something
    went wrong executing the client request.

    Args:
        response (str): Server response.

    Raises:
        CmError: Invalid packet structure.
        CmError: Client authentication failed.

    Returns:
        str: response
    """
    # Error messages
    if response.startswith("500"):
        raise CmError("Invalid packet structure.")
    elif response.startswith("400"):
        raise CmError("Client authentication failed.")
    # Valid response
    else:
        return response


class CmError(Exception):
    """Exception raised for errors in the SSL connection."""

    pass
