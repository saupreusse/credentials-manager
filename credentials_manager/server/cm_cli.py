"""This module contains the code for the Credentials Manager CLI application.
CM CLI is a command line program which acts as a server-admin interface."""
import credentials as cr
import users
import permissions as perms
import getpass
import rotator


# Executable functions for different commands
def cliCreateUser(username, password):
    user = users.cmUser(username, password)
    user.createUser()


def cliDeleteUser(username):
    user = users.cmUser(username, None)
    user.deleteUser()


def cliListUsers():
    users.printUsers()


def cliCreatePermission(label, username):
    perms.createPermission(label, username)


def cliDeletePermission(label, username):
    perms.deletePermission(label, username)


def cliListPermissions():
    perms.printPermissions()


def cliCreateCredentials(label, filepath):
    dict = cr.loadCredentials(filepath)
    credentials = cr.Credentials(label, dict)
    credentials.createCredentials()


def cliDeleteCredentials(label):
    credentials = cr.Credentials(label, None)
    credentials.deleteCredentials()


def cliListCredentials():
    cr.printCredentials()


def cliRotateCredentials(label):
    rotator.rotationHandler(label)

def cliTestConnection(label):
    if rotator.testConnection(label):
        print("Connection Test successful!")
    else:
        print("Connection Test failed!")


def cliHelp():
    print(
        """
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
          >>TEST CONNECTION (CRlabel)
          """
    )


# Dispatch table mapping commands to functions
COMMANDS = {
    "CREATE USER": cliCreateUser,
    "DELETE USER": cliDeleteUser,
    "LIST USERS": cliListUsers,
    "CREATE PERMISSION": cliCreatePermission,
    "DELETE PERMISSION": cliDeletePermission,
    "LIST PERMISSIONS": cliListPermissions,
    "CREATE CREDENTIALS": cliCreateCredentials,
    "DELETE CREDENTIALS": cliDeleteCredentials,
    "LIST CREDENTIALS": cliListCredentials,
    "ROTATE CREDENTIALS": cliRotateCredentials,
    "TEST CONNECTION": cliTestConnection,
    "HELP": cliHelp,
}


def main():
    """Main method of the Credentials Manager (CM) CLI."""
    print("Welcome to the Credentials Manager monitor. For help check out the 'help' command")
    username = input("Please enter your username: ")
    password = getpass.getpass("Please enter your password: ")
    USER = users.cmUser(username, password)

    if USER.authenticateUser():
        print("Authentication successful!")
        while True:
            commandInput = input(f"CM [{username}]>> ")
            commandParts = commandInput.split(" ")

            # Assuming commands always consist of two words
            command = " ".join(commandParts[:2]).upper()
            args = commandParts[2:]

            if command in COMMANDS:
                try:
                    # Try executing the command with the provided arguments
                    COMMANDS[command](*args)
                except TypeError as e:
                    # Handle arguments gracefully
                    print(f"Error: Incorrect number of arguments for '{command}'.")
                except Exception as e:
                    # Handle all other exceptions
                    print(f"Error: {e}")
            elif commandInput.upper() == "EXIT":
                print("Exiting CM monitor...")
                break
            else:
                print("Invalid command structure.")
    else:
        print("Authentication failed. Exiting...")


if __name__ == "__main__":
    main()
