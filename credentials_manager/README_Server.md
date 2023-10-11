# Credentials-Manager Server
Credentials-Manager Server is a python project as part of my bachelor's thesis in computer science.
This project contains all files to run a CM Server, and access it via the CM CLI.

## Requirements
The CM server uses a mariaDB database to store and manage client credentials. Make sure you have mariaDB server 15.1 (or greater) installed on your system. Furthermore, the CM server uses a hardware security module which is accessed by the PKCS11 API. This guide will also guide you through the installation and setup process of [SoftHSM](https://www.opendnssec.org/softhsm/), because the original documentation leaves much to be desired.

## SoftHSM Setup
### 1. Install dependencies
```bash
# Install g++ and libssl-dev libraries
sudo apt install g++ libssl-dev

# Install OpenSC library
sudo apt install opensc
```
### 2. Download [softhsm-2.6.1.tar.gz](https://dist.opendnssec.org/source/)  
and build it from source.
In this example we will install SoftHSM in /opt/softhsm2
```bash
# Unpack softhsm2
tar xf softhsm-2.6.1.tar.gz

# Configure the makefile
./configure --prefix=/opt/softhsm2

# Make (this might take some time)
make

# Install
sudo make install

# Add softhsm to PATH (append this line at the end of ~/.profile)
export PATH=$PATH:/opt/softhsm2/bin

# Reload
source ~/.profile

# Test the installation (this should display the softhsm2 support tool)
softhsm2-util

# Test PKCS11 tool
pkcs11-tool --show-info --module /opt/softhsm2/lib/softhsm/libsofthsm2.so

```

### 3. Setup a SoftHSM slot
```bash
# 1. List available token slots (This should show one slot "Slot 0")
softhsm2-util --show-slots

# 2. Initialize a token in slot 0:
# YOUR_LABEL : a token label of your choice (descriptive name).
# YOUR_PIN : a user pin of your choice (required to access the key stored in the token).
# YOUR_SO_PIN : a security officer pin of your choice (used for administrative tasks).
softhsm2-util --init-token --slot 0 --label YOUR_LABEL --pin YOUR_PIN --so-pin YOUR_SO_PIN

# 3. If all went well, softhsm should display:
This token has been initialized and is reassigned to slot NEW_SLOT_NUMBER

# 4. Now we can create a Key inside this token:
# NEW_SLOT_NUMBER : replace with the new slot number this token was reassigned to.
# YOUR_PIN : replace with your user pin.
# YOUR_KEY_LABEL : a key lavel of your choice (descriptive name).
pkcs11-tool --module /opt/softhsm2/lib/softhsm/libsofthsm2.so --slot NEW_SLOT_NUMBER -l --pin YOUR_PIN --keygen --key-type aes:32 --id 01 --label "YOUR_KEY_LABEL"

# 5. if all went well, softhsm should display:
Key generated:
Secret Key Object; AES length 32
  label:      YOUR_KEY_LABEL
  ID:         01
  Usage:      encrypt, decrypt, verify, wrap, unwrap
  Access:     never extractable, local

```

### 4. Edit the server config
Navigate to credentials_manager/server/config/hsm_config.json and enter your hsm parameters:
```json
{
    "pkcs11" : "/opt/softhsm2/lib/softhsm/libsofthsm2.so",
    "slotid" : 1894991440, # NEW_SLOT_NUMBER
    "password" : "YOUR_PIN",
    "key" : "YOUR_KEY_LABEL"
}
```

## MariaDB SETUP
Setting up a [MariaDB server](https://mariadb.org/) is well documented and not part of this guide.
However, the CM server uses a MariaDB database to store and manage database credentials, cryptographic keys, and user information. In this guide we use mysql  Ver 15.1 Distrib 10.5.19-MariaDB, for debian-linux-gnu (aarch64) using  EditLine wrapper

### 1. Create the CM database
This is the database the CM server accesses. In this guide, we will call it "credentials_manager".
```sql
CREATE DATABASE credentials_manager;
```

### 2. Create a new user for the CM server
This is the user account which the CM server uses as login. Use a username and password of your choice.
```sql
CREATE USER "username"@"localhost" identified by "password";
```

### 3. Grant privileges
For security concerns, it would be best to create a user with only minimal access rights to the CM database. However in this guide we grant full access, in order to prevent errors further on.
```sql
GRANT ALL PRIVILEGES ON credentials_manager.* TO "username"@"localhost";
```

### 4. Import tables
Last we will import the tables "users", "data_keys", "credentials" and "permissions" into the CM database. The mysqldump for this operation is located in credentials_manager/server/cm_db.sql.

```bash
mysql -u username -p credentials_manager  < cm_db.sql
```

### 5. Edit the server config
Navigate to credentials_manager/server/config/cm_database_config.json and enter your database parameters:

```json
{
    "user" : "username",
    "password" : "password",
    "host" : "127.0.0.1",
    "database" : "credentials_manager"
}
```

## CM server setup
Now that our database and HSM are setup, we can finally take a look at the CM Server & CLI.

### Requirements
CM Server makes use of a few python libraries, which have to be installed before running the server.
```txt
cryptography==41.0.3
jsonschema==4.19.0
mysql-connector-python==8.1.0
PyKCS11==1.5.12
bcrypt==4.0.1
setuptools==52.0.0
tabulate==0.9.0
```

### Configure the server
The server configuration files are all located in credentials_manager/server/config. If you followed the first two steps on how to setup SoftHSM and MariaDB, you will already have encountered the cm_database_config.json and the hsm_config.json. Now it is time to take a look at our main server configuration called server_config.json.
Usually, you can leave it as is.

```json
{
    "ca_cert" : "config/certs/ca_certificate.pem",
    "server_cert" : "config/certs/server_certificate.pem",
    "server_key" : "config/certs/server_private_key.pem",
    "server_host" : "0.0.0.0",
    "server_port" : 12345
}
```
- ca_cert: Path to our CA's certificate (located in credentials_manager/server/config/ca_certificate.pem)
- server_cert: Path to our server's certificate (located in credentials_manager/server/config/server_certificate.pem)
- server_key: Path to our server's private key (located in credentials_manager/server/config/server_private_key.pem)
- server_host : The server's IP, leave this at "0.0.0.0" to listen on all available interfaces.
- server_port : The server's Port.

### Starting the server
To start the server, simply run the cm_server.py file located in credentials_manager/server/cm_server.py.
The server will announce itself in the console if all worked well.
```bash
# Starts the CM server script
python cm_server.py
```


## CM CLI
The Credentials-Manager CLI is a command line tool that acts as an interface between user and CM server. It comes with a set of commands that implement some basic functionality to manage users and credentials.

### Starting the CM CLI
To start the CLI, simply run the cm_cli.py file located in credentials_manager/server/cm_cli.py. The script will announce itself in the console if all worked well and prompt for a login. If you followed the steps in the MariaDB setup section, there will already be a user "cmAdmin" with password "cmAdminPassword" created which you can use.

```text
Welcome to the Credentials Manager monitor.
Please enter your username: cmAdmin
Please enter your password:
Authentication successful!
CM [cmAdmin]>> help

          Credentials Manager monitor command library:
          Please enter commands and arguments without using commas or parentheses.
          Commands are case insensitive while arguments are case sensitive.
          (Example: CREATE USER myuser mypassword)
          >>CREATE USER (username, password)
          >>DELETE USER (username)
          >>LIST USERS ()
          >>CREATE PERMISSION (CRlabel, username)
          >>DELETE PERMISSION (CRlabel, username)
          >>LIST PERMISSIONS ()
          >>CREATE CREDENTIALS (CRlabel, DBconfig)
          >>DELETE CREDENTIALS (CRlabel)
          >>LIST CREDENTIALS ()
          >>ROTATE CREDENTIALS (CRlabel)

CM [cmAdmin]>>
```
Using the "HELP" command will display a list of all available commands.

### Creating a new CM user
When a CM client (webapplication) fetches its credentials from the CM server, it must authenticate in two ways. One is done via mutual authentication over TLS (which is what all the certificates are there for) and the second is done using a username and password. To create a new CM User, we use the CREATE USER command.

```text
# creates a user for your CM client (webapplication).
CREATE USER CM_Username CM_Password
```
- CM_Username : a username of your choice.
- CM_Password : a password of your choice.

### Creating credentials
After we created a User for our CM client (webapplication), we can now store its database credentials securely in the CM Server. The CM Server will take a path to a json file containing the client's database configuration, read it's content and store it encrypted inside the credentials_manager database.

```txt
# Creates new credentials for your CM client (webapplication)
CREATE CREDENTIALS CR_LABEL DB_CONFIG.json
```
- CR_Label : a unique label of your choice (descriptive name)
- DB_CONFIG.json : path to the clients credentials stored in json format.

Note that the credentials in DB_CONFIG.json have to follow a strict format, so that the mysql.connector library can read them.

```json
{
    "user" : "webapplication",
    "password" : "webapplication_password",
    "host" : "127.0.0.1",
    "database" : "database_name"
    "port" : 3306
}
```
- user : the username that the CM client (webapplication) uses to connect to its MariaDB/MySQL database
- password : the password
- host : the host IP of the MariaDB/MySQL database the CM client (webapplication) connects to.
- database (optional) : the MariaDB/MySQL database name to connect to.
- port (optional) : the MariaDB/MySQL database port, defaults to 3306


You can delete the DB_CONFIG.json once the credentials have been created using the CLI. They are now securely stored inside the CM Server.

### Creating Permissions
Once we have created the CM user and its credentials, we can proceed granting this user access to the credentials. We do this with the CREATE PERMISSION command.

```txt
# Grants user "Username" access to credentials with label "CR_Label"
CREATE PERMISSION CR_Label Username
```

You can create new users and credentials in the same way. Now that we have setup the CM server, we can go ahead and take a look at the client (webapplication) readme "README_Client.md".