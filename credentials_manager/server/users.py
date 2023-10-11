import bcrypt
import mysql.connector
import connector as cn
import crypto
from tabulate import tabulate


class cmUser:
    """This class contains all the code to create & delete credentials-manager users"""

    def __init__(self, cmUsername : str, cmPassword : str):
        """Constructor for credentials manager user objects.

        Args:
            cmUsername (str): Username
            cmPassword (str): Password
        """
        self.cmUsername = cmUsername
        self.cmPassword = cmPassword

    def fetchUser(self) -> bool:
        """Checks if a user exists in the CM database.

        Returns:
            bool: True if user exists.
        """
        try:
            # Connect to the MariaDB database
            connection = mysql.connector.connect(**cn.DBCONFIG)
            cursor = connection.cursor()

            # Get the salt and hashed password from the database for the given username
            selectQuery = "SELECT * FROM users WHERE username = %s"
            cursor.execute(selectQuery, (self.cmUsername,))
            result = cursor.fetchone()

            # If user doesn't exist
            if not result:
                return False
            else:
                return True
        except mysql.connector.Error as e:
            print(f"Error: {e}")
            return False
        finally:
            # Close connection gracefully
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    def putUser(self, salt, hashedPassword):
        """Function to store the cmUser, salt and password in the credentials_manager.users table

        Args:
            salt (bytes): Salt that was used to create salted and hashed password.
            hashedPassword (bytes): A salted and hashed password
        """
        try:
            # Connect to the MariaDB database
            connection = mysql.connector.connect(**cn.DBCONFIG)
            cursor = connection.cursor()

            # Check if user already exsists:
            if self.fetchUser():
                print(f"User '{self.cmUsername}' already exists.")
                return

            # Else, Insert the user and their salted/hashed password into the table
            insertQuery = (
                "INSERT INTO users (username, salt, password) VALUES (%s, %s, %s)"
            )
            cursor.execute(insertQuery, (self.cmUsername, salt, hashedPassword))
            connection.commit()

        except mysql.connector.Error as e:
            print(f"Error: {e}")
        finally:
            # Close the cursor and connection
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    def deleteUser(self):
        """Deletes the cmUser from the cm.users table"""
        try:
            # Connect to the MariaDB database
            connection = mysql.connector.connect(**cn.DBCONFIG)
            cursor = connection.cursor()

            # Check if user already exsists:
            if not self.fetchUser():
                print(f"User '{self.cmUsername}' doesn't exist.")
                return

            # Delete the user and their salted/hashed password from the table
            insertQuery = "DELETE FROM users WHERE username = %s;"
            cursor.execute(insertQuery, (self.cmUsername,))
            connection.commit()

            print(f"Deleted User {self.cmUsername}")
        except mysql.connector.Error as e:
            print(f"Error: {e}")
        finally:
            # Close the cursor and connection
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    def createUser(self):
        """Creates a new entry in the cm.users table."""
        # Check if user already exsits
        if self.fetchUser():
            print(f"User '{self.cmUsername}' already exists.")
        else:
            tuple = crypto.hashAndSaltPassword(self.cmPassword)
            salt = tuple[0]
            hashedPassword = tuple[1]
            self.putUser(salt, hashedPassword)

            print(f"Created user {self.cmUsername}")

    def authenticateUser(self) -> bool:
        """Takes in a user and and tries to authenticate them by comparing their password to the corresponding stored salted hash.

        Returns:
            bool: True if authentication successful.
        """
        try:
            # Connect to the MariaDB database
            connection = mysql.connector.connect(**cn.DBCONFIG)
            cursor = connection.cursor()

            # Get the salt and hashed password from the database for the given username
            selectQuery = "SELECT salt, password FROM users WHERE username = %s"
            cursor.execute(selectQuery, (self.cmUsername,))
            result = cursor.fetchone()

            # If user doesn't exist
            if not result:
                return False

            salt = result[0]
            storedHash = result[1]

            # Hash the provided password with the retrieved salt
            hashedPassword = bcrypt.hashpw(self.cmPassword.encode("utf-8"), salt)

            # Compare the computed hash with the stored hash
            return hashedPassword == storedHash

        except Exception as e:
            # Catch all errors. Don't print traceback.
            print(e)
            return False
        finally:
            # Close connection gracefully
            if cursor:
                cursor.close()
            if connection:
                connection.close()


def printUsers():
    """Pretty print the cm.users table
    """
    try:
        # Connect to the MariaDB database
        connection = mysql.connector.connect(**cn.DBCONFIG)
        cursor = connection.cursor()

        # Get result & pretty print
        cursor.execute("SELECT uid, username, password FROM users")
        result = cursor.fetchall()

        # For pretty printing we truncate the long hashed password string.
        modifiedResult = []
        for row in result:
            uid, username, password = row
            password = password.decode('utf-8')[:16] 
            modifiedResult.append((uid, username, password))

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
