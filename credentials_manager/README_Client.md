# Credentials-Manager Utils

Credentials-Manager Utils is a Python library for dealing with CM client-server communication.
This folder contains the raw files of the Credentials-Manager Utils package, which has to be installed in order to
create a CM client endpoint to connect to a CM server.
It also contains a already pre-packed tar.gz, which can be used for easy installation.
This guide will walk you through the setup process of the CM client. All client files are located in credentials_manager/client.
Before you proceed, you should have followed the steps in the "README_Server.md". Make sure your CM server is setup correctly before attempting to create a client connection from your webapplication.

## Installation

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install CM Utils. The package is located in a seperate folder in credentials_manager/credentials_manager/credentials_manager-1.0.tar.gz.

```bash
pip install credentials_manager-1.0.tar.gz
```

## Configuration
CM Utils reads its configuration from /opt/credentials_manager/cm_config.json.  
Please create this file (or copy the template from credentials_manager/client/config/cm_config.json) and correctly configure it before you proceed. It is important that the user under which the client is running has read access to this file. This is a common error for client.cgi scripts that are executed by an apache webserver, that might be running under its own user.

```json
{
    "ca_cert" : "path/to/ca_certificate.pem",
    "client_cert" : "path/to/client_certificate.pem",
    "client_key" : "path/to/client_private_key.pem",
    "server_host" : "127.0.0.1",
    "server_port" : 12345,
    "client_username" : "username",
    "client_password" : "password"
}
```
- ca_cert: Path to the CA certificate (located in credentials_manager/client/config/certs)
- client_cert: Path to the client certificate (located in credentials_manager/client/config/certs)
- client_key: Path to the client's private key (located in credentials_manager/client/config/certs)
- server_host: CM server's IP address (specified in credentials_manager/server/config/server_config.json)
- server_port: CM server's port (specified in credentials_manager/server/config/server_config.json)
- client_username: The CM client's username (This is the user you have created via the CM CLI)
- client_password: The CM client's password (This is the password you have created via the CM CLI)

## Usage
This is a simple test-client python file, that connects to a CM server which is running on the network.
Make sure that the client-server communication isn't blocked by firewalls and that the CM server is actually running.

```python
from credentialsManager import credentialsManager

try:
    # Create a client endpoint for client-server communication
    client = credentialsManager.createClient()

    # Send a 'GET_CR' Request to the CM server. Change the label "webappcr" to your client's credentials label.
    request = ("GET_CR", {"label" : "webappcr"})
    
    # The Server answer's with a string containing the client's database credentials.
    result = client.execute(request)
    print("Received message:", result)
except Exception as e:
    print(f"Error: {e}")
```

Down below is a simple python.cgi script for use in a webserver. There are a few things to consider before proceeding, depending on your setup. Some errors I encountered are covered in the "Troubleshooting" section in this file.


```python
#!/usr/bin/python3

# It might be neccessary to include the site-packages here, as displayed in "Troubleshooting".
import mysql.connector
from credentialsManager import credentialsManager
import json

print("Content-Type: text/html")
print()
print("<h1> Credentials Manager Test Page </h1>")

# Send a GET_CR request to the CM server. Change the label "webappcr" to your client's credentials label.
try:
    client = credentialsManager.createClient()
    request = ("GET_CR", {"label": "webappcr"})
    result = client.execute(request)
except Exception as e:
    print(f"Error: {e}")

# Convert the credentials string to a dictionary in order to connect to the database.
config = json.loads(result)
print(f"<p>Credentials: {config}</p>")


# Connect to MariaDB
conn = mysql.connector.connect(**config)

# ...
```

## Troubleshooting
Depending on your apache setup, and how you installed the mysql.connector and credentials-Manager Utils, you might encounter some issues running cm-client.cgi scripts.

- ModuleNotFoundError:  
Make sure the package is correctly installed for the interpreter specified in your script's shebang. You can explicitly include side-packages in your cgi scripts and grant other users (including Apache) access like this.


```bash
# Get the path for your interpreter's CM site-packages
/usr/bin/python3 -c "import credentialsManager; print(credentialsManager.__path__)"
```

```python
# Inside your cgi-script, add these lines before importing the CM package
import sys
sys.path.append('/usr/lib/python3/dist-packages')
```

```bash
# Make sure the Apache webserver can access the package
sudo chmod -R o+rX /usr/lib/python3/dist-packages/

```

- If nothing works:  
  - Try importing the credentialsManager module directly from:  
   /credentials_manager/credentials_manager/credentialsManager/credentialsManager.py  
  - Try running the script locally using ./cm_client.cgi