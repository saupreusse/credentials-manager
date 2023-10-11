import socket
import ssl
import json
import cm_protocol
import users
import cm_requests


# Server settings & certificates for TLS
with open("config/server_config.json", "r") as f:
    config = json.load(f)

    serverHost = config["server_host"]
    serverPort = config["server_port"]
    serverCert = config["server_cert"]
    serverKey = config["server_key"]
    caCert = config["ca_cert"]


def main():
    """The Credentials Manager Server's main function."""
    # Create a socket & listen on it
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverSocket.bind((serverHost, serverPort))
    serverSocket.listen(5)

    print(f"CM Server listening on {serverHost}:{serverPort}")
    sslClientSocket = None

    while True:
        # Accept incoming connections
        clientSocket, clientAddress = serverSocket.accept()
        print(f"Accepted connection from {clientAddress}")

        # Wrap the socket with TLS
        try:
            context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            context.load_verify_locations(caCert)
            context.load_cert_chain(certfile=serverCert, keyfile=serverKey)
            context.verify_mode = ssl.CERT_REQUIRED
            context.minimum_version = ssl.TLSVersion.TLSv1_3
            sslClientSocket = context.wrap_socket(
                clientSocket, server_side=True, do_handshake_on_connect=True
            )
        except Exception as e:
            print(f"Error: {e}")

        try:
            # Receive and send data
            data = sslClientSocket.recv(1024)
            print(f"Received packet from {clientAddress}")
            if data:
                packet = data.decode()

                # Validate packet structure against PROTOCOLSCHEMA
                if not cm_protocol.validatePacket(packet):
                    response = "500 : Invalid packet structure."
                    sslClientSocket.sendall(response.encode())
                    continue
                print("Packet validity OK!")

                # Client authentication
                packet = json.loads(packet)
                header = packet["header"]
                user = users.cmUser(
                    cmUsername=header["cmUser"], cmPassword=header["cmPassword"]
                )

                if not user.authenticateUser():
                    print("Client authentication failed!")
                    response = "400 : Client authentication failed."
                    sslClientSocket.sendall(response.encode())
                    continue
                print("Client authentication successful!")

                # Handle request based on request type
                result = cm_requests.requestHandler(packet)
                sslClientSocket.sendall(json.dumps(result).encode())
                print(f"Sent answer to {clientAddress}")

        except Exception as e:
            print(f"Error: {e}")
        finally:
            # Close the connection gracefully
            if sslClientSocket:
                sslClientSocket.close()
            print("Connection closed.")


if __name__ == "__main__":
    main()
