import json
import connector as cn
import mysql.connector
import crypto
import keys
from tabulate import tabulate


# JSON schema for the credentials structure
CRSCHEMA = {
    "type": "object",
    "properties": {
        "host": {"type": "string"},
        "user": {"type": "string"},
        "password": {"type": "string"},
        "database": {"type": "string"},
        "port": {"type": "integer"},
    },
    "required": ["host", "user", "password"],
    "additionalProperties": False,
}


class Credentials:
    def __init__(self, label, credentials):
        """Constructor for credentials objecs.

        Args:
            label (str): Unique credentials label.
            credentials (dict[str]): Credentials dictionary.
        """
        self.label = label
        self.credentials = credentials

    def putCredentials(self):
        """Puts credentials into the cm.credentials table."""
        try:
            # Connect to the MariaDB database
            connection = mysql.connector.connect(**cn.DBCONFIG)
            cursor = connection.cursor()

            # Select credentials from the table & commit
            insertQuery = "INSERT INTO credentials (credentials, label) VALUES (%s, %s)"
            cursor.execute(insertQuery, (self.credentials, self.label))
            connection.commit()
        except mysql.connector.Error as e:
            print(f"Error: {e}")
        finally:
            # Close connection gracefully
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    def createCredentials(self):
        """Creates encrypted credentials from a plaintext credentials object and puts them in the cm database,
        if they don't already exist."""
        # Check if credentials already exist
        if fetchCredentials(self.label):
            print(f"Credentials with label {self.label} already exist.")
            return
        # if they don't exist, check if the given input is valid
        elif not cn.validateDict(self.credentials, CRSCHEMA):
            print("Invalid credentials format.")
            return
        # if the input is valid & credentials dont exist, create credentials
        else:
            try:
                # first, generate a data key for these specific credentials
                dataKey = keys.generateDataKey()

                # second, encrypt the plaintext credentials using the datakey
                ciphertext = crypto.encryptCredentials(dataKey, self.credentials)
                encryptedCredentials = Credentials(self.label, ciphertext)

                # third, encrypt the datakey
                encryptedDataKey = dataKey.encryptDataKey()

                # fourth, put the encrypted credentials
                encryptedCredentials.putCredentials()

                # fifth, put the encrypted datakey
                encryptedDataKey.putKey(self.label)
                print(f"Created credentials '{self.label}'.")
            except Exception as e:
                print(f"Error: {e}")

    def deleteCredentials(self):
        """Deletes credentials from the CM database."""
        try:
            # Connect to the MariaDB database
            connection = mysql.connector.connect(**cn.DBCONFIG)
            cursor = connection.cursor()

            if not fetchCredentials(self.label):
                print(f"There are no credentials for label '{self.label}'")
                return

            # Delete credentials from the table & commit
            deleteQuery = "DELETE FROM credentials WHERE label = %s"
            cursor.execute(deleteQuery, (self.label,))
            connection.commit()

            print(f"Deleted credentials '{self.label}'")
        except mysql.connector.Error as e:
            print(f"Error: {e}")
        finally:
            # Close connection gracefully
            if cursor:
                cursor.close()
            if connection:
                connection.close()


def fetchCredentials(label):
    """Fetches credentials for a given label and decrypts them using the corresponding data key.

    Args:
        label (str): Unique credentials label.

    Returns:
        dict[str]: Plaintext credentials.
    """
    try:
        # Connect to the MariaDB database
        connection = mysql.connector.connect(**cn.DBCONFIG)
        cursor = connection.cursor()

        # Select credentials from the table & commit
        cursor.execute(
            "SELECT credentials, cr_id FROM credentials WHERE label = %s",
            (label,),
        )
        result = cursor.fetchone()
        if not result:
            return None
        encryptedCredentials, crId = result

        # Fetch & decrypt the data keybytes
        dataKey = keys.fetchDataKey(crId)
        if not dataKey:
            return None

        # Use the decryptCredentials function to decrypt the credentials
        decryptedCredentials = crypto.decryptCredentials(dataKey, encryptedCredentials)
        return decryptedCredentials

    except mysql.connector.Error as e:
        print(f"Error: {e}")
        return None
    finally:
        # Close connection gracefully
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def loadCredentials(filepath):
    """Loads & verifies credentials.json stored in given path.

    Args:
        filepath (str): Path to the credentials.json.

    Returns:
        dict[str]: Credentials dictionary. None, if no such file or invalid format.
    """
    try:
        with open(filepath, "r") as f:
            credentials = json.load(f)
            if cn.validateDict(credentials, CRSCHEMA):
                return credentials
            else:
                return None
    except Exception:
        print("Can't open credentials file.")
        return None


def printCredentials():
    try:
        # Connect to the MariaDB database
        connection = mysql.connector.connect(**cn.DBCONFIG)
        cursor = connection.cursor()

        # Get result & pretty print
        cursor.execute("SELECT cr_id, label, credentials FROM credentials")
        result = cursor.fetchall()

        # For pretty printing we truncate the long encrypted credentials string.
        modifiedResult = []
        for row in result:
            crId, label, credentials = row
            credentials = credentials[:16]
            modifiedResult.append((crId, label, credentials))

        fields = [i[0] for i in cursor.description]
        print(tabulate(modifiedResult, headers=fields, tablefmt="psql"))
    except mysql.connector.Error as e:
        print(f"Error: {e}")
    finally:
        # Close connection gracefully
        if cursor:
            cursor.close()
        if connection:
            connection.close()
