import mysql.connector
import connector as cn
from tabulate import tabulate


class Permission:
    """This class handles the creation of permission objects which grant user access to specific credentials."""

    def __init__(self, uId, crId):
        """Constructor for permission objects

        Args:
            uId (int): User ID for the user that shall be granted access.
            crId (int): Credentials ID for the credentials to be accessed.
        """
        self.uId = uId
        self.crId = crId

    def putPermission(self):
        try:
            # Connect to the MariaDB database
            connection = mysql.connector.connect(**cn.DBCONFIG)
            cursor = connection.cursor()

            # Check if permission already exists.
            selectQuery = "SELECT * FROM permissions WHERE uid=%s AND cr_id=%s"
            cursor.execute(selectQuery, (self.uId, self.crId))
            result = cursor.fetchone()
            if result:
                print("Permission already exists.")
                return

            # Else, Insert the permissions into the table
            insertQuery = "INSERT INTO permissions (uid, cr_id) VALUES (%s, %s)"
            cursor.execute(
                insertQuery,
                (self.uId, self.crId),
            )
            connection.commit()

        except mysql.connector.Error as e:
            print(f"Error: {e}")
        finally:
            # Close connection gracefully
            if cursor:
                cursor.close()
            if connection:
                connection.close()


def createPermission(label, username):
    """Given a credentials label and a credentials manager username,
    tries to create a permission object that grants this user access to the credentials identified by this label.

    Args:
        label (str): Credentials label.
        username (str): Credentials Manager username.
    """
    try:
        # Connect to the MariaDB database
        connection = mysql.connector.connect(**cn.DBCONFIG)
        cursor = connection.cursor()

        # Get the uid for the given username from the users table
        uId = fetchUid(username)

        # Get the cr_id for the given label from the credentials table
        crId = fetchCrid(label)

        # Put permission into CM database
        permission = Permission(uId, crId)
        permission.putPermission()
        print(f"Granted access to '{label}' for user '{username}'.")

    except mysql.connector.Error as e:
        print(f"Error: {e}")
    finally:
        # Close connection gracefully
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def deletePermission(label, username):
    """Deletes entry for permission with specified ID from the CM database.

    Args:
        label (str): Unique credentials label.
        username (str): Unique CM username.
    """
    try:
        # Connect to the MariaDB database
        connection = mysql.connector.connect(**cn.DBCONFIG)
        cursor = connection.cursor()

        # Get the uid for the given username from the users table
        uId = fetchUid(username)

        # Get the cr_id for the given label from the credentials table
        crId = fetchCrid(label)

        # Check if permission exists
        selectQuery = "SELECT * FROM permissions WHERE cr_id = %s AND uid = %s"
        cursor.execute(selectQuery, (crId, uId))
        result = cursor.fetchone()
        if not result:
            print("Permission doesn't exist.")
            return

        # Delete Permission
        deleteQuery = "DELETE FROM permissions WHERE cr_id = %s AND uid = %s"
        cursor.execute(deleteQuery, (crId, uId))

        connection.commit()
        print(f"Removed access to '{label}' from user '{username}'.")

    except mysql.connector.Error as e:
        print(f"Error: {e}")
    finally:
        # Close connection gracefully
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def printPermissions():
    """Pretty prints content of cm.permissions table.
    """
    try:
        # Connect to the MariaDB database
        connection = mysql.connector.connect(**cn.DBCONFIG)
        cursor = connection.cursor()

        # Get result & pretty print
        cursor.execute("SELECT * FROM permissions")
        result = cursor.fetchall()

        fields = [i[0] for i in cursor.description]
        print(tabulate(result, headers=fields, tablefmt="psql"))
    except mysql.connector.Error as e:
        print(f"Error: {e}")
    finally:
        # Close connection gracefully
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def verifyPermission(username, label) -> bool:
    """Verifies if a user has access to the credentials with the given label.

    Args:
        username (str): Unique CM username.
        label (str): Unique credentials label.

    Returns:
        bool: True, if user has access.
    """
    try:
        # Connect to the MariaDB database
        connection = mysql.connector.connect(**cn.DBCONFIG)
        cursor = connection.cursor()

        # fetch uid and crid
        uId = fetchUid(username)
        crId = fetchCrid(label)

        selectQuery = "SELECT perm_id FROM permissions WHERE uid = %s AND cr_id = %s"
        cursor.execute(selectQuery, (uId, crId))
        result = cursor.fetchone()

        if not result:
            return False
        else:
            return True

    except mysql.connector.Error as e:
        print(f"Error: {e}")
    finally:
        # Close connection gracefully
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def fetchUid(username) -> int:
    """Fetches user ID for a given username from the cm.users table.

    Args:
        username (str): Unique CM username.

    Returns:
        int: CM User ID.
    """
    try:
        # Connect to the MariaDB database
        connection = mysql.connector.connect(**cn.DBCONFIG)
        cursor = connection.cursor()

        # Get the uid for the given username from the users table
        selectQuery = "SELECT uid FROM users WHERE username = %s"
        cursor.execute(selectQuery, (username,))
        result = cursor.fetchone()

        if not result:
            print("User doesn't exist.")
            return None
        else:
            uId = result[0]
            return uId
    except mysql.connector.Error as e:
        print(f"Error: {e}")
    finally:
        # Close connection gracefully
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def fetchCrid(label) -> int:
    """Fetches credentials ID for a given credentials label from the cm.credentials table.

    Args:
        label (str): Unique credentials label.

    Returns:
        int: Credentials ID.
    """
    try:
        # Connect to the MariaDB database
        connection = mysql.connector.connect(**cn.DBCONFIG)
        cursor = connection.cursor()

        # Get the cr_id for the given label from the credentials table
        selectQuery = "SELECT cr_id FROM credentials WHERE label = %s"
        cursor.execute(selectQuery, (label,))
        result = cursor.fetchone()

        if not result:
            print("Credentials don't exist.")
            return None
        else:
            crId = result[0]
            return crId
    except mysql.connector.Error as e:
        print(f"Error: {e}")
    finally:
        # Close connection gracefully
        if cursor:
            cursor.close()
        if connection:
            connection.close()
