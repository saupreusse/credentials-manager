import os
import connector as cn
import mysql.connector
import credentials as cr
import crypto
import keys


def rotationHandler(label, password=None):
    """Handles the whole password rotation process.

    Args:
        label (str): The Label of the credentials to be rotated.

    Raises:
        Exception: Rotation Handler Exception.
    """
    try:
        # If a password was specified by user, use that password instead of generating a random one.
        if password:
            newPassword = password
        else:
            newPassword = createPassword()
    except Exception as e:
        raise RotationError(f"Password creation failed: {e}")

    try:
        setPassword(label, newPassword)
    except Exception as e:
        raise RotationError(f"Can't set new password: {e}")

    try:
        testConnection(label, newPassword)
    except Exception as e:
        raise RotationError(
            f"A new password was set, but the connection test failed: {e}"
        )

    try:
        finishRotation(label, newPassword)
    except Exception as e:
        raise RotationError(f"Rotation finish failed. {e}")

    print("Rotated credentials successfully!")


def createPassword(length=16):
    """Creates a random password for use in mysql databases.

    Args:
        length (int, optional): Password length. Defaults to 16.

    Raises:
        ValueError: Password too short.

    Returns:
        str: Random Password.
    """
    if length < 12:
        raise ValueError(
            "Password length should be at least 12 characters for security reasons."
        )

    # Charset
    chars = (
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        "abcdefghijklmnopqrstuvwxyz"
        "0123456789"
        "!@#$%^&*()_+-=[]|"
    )

    password = []
    while len(password) < length:
        byte = os.urandom(1)
        char = byte.decode("latin-1")
        if char in chars:
            password.append(char)

    return "".join(password)


def setPassword(label, newPassword) -> bool:
    """Logs in to the database under the old credentials, and updates the password for the user.

    Args:
        label (str): Credentials label.
        newPassword (str): New Password.

    Returns:
        bool: True, if it worked, Else False.
    """
    # fetch the old plaintext credentials
    decryptedCredentials = cr.fetchCredentials(label)

    try:
        # Connect to the MySQL database using the old password
        connection = mysql.connector.connect(**decryptedCredentials)
        cursor = connection.cursor()

        # Find current user@host (This part is only useful for mysql databases, where users can change their password using ALTER USER)
        # cursor.execute("SELECT USER()")
        # userHost = cursor.fetchone()[0]
        # username, hostname = userHost.split("@")

        # Set the new password for the current user
        changePasswordQuery = "SET PASSWORD = PASSWORD(%s)"
        cursor.execute(changePasswordQuery, (newPassword,))

        connection.commit()
        return

    except Exception as e:
        raise RotationError(f"Error: {e}")
    finally:
        # Close connection gracefully
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def testConnection(label, password=None) -> bool:
    """Tests if a connection can be established using the credentials with given the label.

    Args:
        label (str): Unique credentials label.
        password (str, optional): Custom password to be used for connecting. Defaults to None.

    Raises:
        RotationError: Connection test failed.

    Returns:
        bool: True, if connection could be established.
    """
    # Fetch the decrypted credentials & update password if one was given.
    decryptedCredentials = cr.fetchCredentials(label)
    if password:
        decryptedCredentials["password"] = password

    try:
        # Connect to the MySQL database using the given password
        connection = mysql.connector.connect(**decryptedCredentials)

        # If we've reached here without an exception, the connection was successful.
        return

    except Exception as e:
        raise RotationError(f"Connection test failed. {e}")
    finally:
        # Close connection gracefully
        if connection:
            connection.close()


def finishRotation(label, newPassword):
    """Finishes the rotation by updating the credentials and data key in the credentials manager.

    Args:
        label (str): Unique Credentials label.
        newPassword (str): New Password.

    Raises:
        RotationError: Can't finish rotation.
    """
    # Generate new Credentials & new DataKey
    newDataKey = keys.generateDataKey()
    newCredentials = {}
    try:
        # Fetch the decrypted credentials & update password
        decryptedCredentials = cr.fetchCredentials(label)
        decryptedCredentials["password"] = newPassword

        newCredentials = crypto.encryptCredentials(newDataKey, decryptedCredentials)
        newDataKey = newDataKey.encryptDataKey()
    except Exception as e:
        raise RotationError(f"Can't finish rotation: {e}")

    updateCredentialsAndDatakey(label, newCredentials, newDataKey)
    return


def updateCredentialsAndDatakey(
    label: str, newEncryptedCredentials: bytes, newDataKey: keys.DataKey
):
    """Helper function for finishRotation. Updates the new credentials and datakey in the cm.credentials & cm.data_keys table.

    Args:
        label (str): Unique Credentials label.
        newEncryptedCredentials (bytes): New Credentials that have already been encrypted with the data key.
        newEncryptedDataKey (DataKey): New DataKey that has already been encrypted with the HSM master key.

    Raises:
        Rotation Error: Can't update credentials and data key.
    """
    try:
        # Connect to the MariaDB database
        connection = mysql.connector.connect(**cn.DBCONFIG)
        cursor = connection.cursor()

        # Update the credentials for the given label
        updateCredentialsQuery = (
            "UPDATE credentials SET credentials = %s WHERE label = %s"
        )
        cursor.execute(updateCredentialsQuery, (newEncryptedCredentials, label))

        # Fetch the cr_id for the given label
        selectQuery = "SELECT cr_id FROM credentials WHERE label = %s"
        cursor.execute(selectQuery, (label,))
        result = cursor.fetchone()
        crId = result[0]

        # Update the data key for the given cr_id
        updateDataKeyQuery = "UPDATE data_keys SET data_key = %s, key_iv = %s, cr_iv = %s WHERE cr_id = %s"
        cursor.execute(
            updateDataKeyQuery,
            (
                newDataKey.dataKey,
                newDataKey.keyIv,
                newDataKey.crIv,
                crId,
            ),
        )

        # Commit the changes
        connection.commit()
    except Exception:
        raise RotationError("Can't update credentials or data key.")
    finally:
        # Close connection gracefully
        if cursor:
            cursor.close()
        if connection:
            connection.close()


class RotationError(Exception):
    """Class for custom error messages."""

    pass
