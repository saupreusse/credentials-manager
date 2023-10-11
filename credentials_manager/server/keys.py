from PyKCS11 import PyKCS11, PyKCS11Lib, CKM_AES_CBC_PAD, CKO_SECRET_KEY
import mysql.connector
import os
import connector as cn


class DataKey:
    """This class contains all functions to create DataKey objects that can be used to encrypt and decrypt credentials.
    Note that data keys have to be encrypted by the master key inside a hardware security module before they can be stored
    in the credentials manager database.
    """

    def __init__(self, dataKey: bytes, keyIv: bytes, crIv: bytes):
        """Constructor for DataKey objects.

        Args:
            dataKey (bytes): A true random AES key used for encrypting credentials.
            keyIv (bytes): A true random initialization vector used for encrypting & decrypting the dataKey with the HSM master key.
            crIv (bytes): A true random initialization vector used for encrypting & decrypting credentials with the data key.
        """
        self.dataKey = dataKey
        self.keyIv = keyIv
        self.crIv = crIv

    def putKey(self, label):
        """Stores a data key for the credentials with given label in the cm.data_keys table.

        Args:
            label (str): Unique label of the credentials this key belongs to.
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
                print("No credentials with this label exist.")
                return

            crId = result[0]

            # Check if a data key for this cr_id exists already.
            selectQuery = "SELECT * FROM data_keys WHERE cr_id = %s"
            cursor.execute(selectQuery, (crId,))
            result = cursor.fetchone()

            if result:
                print("These credentials already have a data key.")
                return

            # Insert the  encrypted datakey, key_iv, and cr_id into the data_keys table
            insertQuery = "INSERT INTO data_keys (cr_id, data_key, key_iv, cr_iv) VALUES (%s, %s, %s, %s)"
            cursor.execute(
                insertQuery,
                (crId, self.dataKey, self.keyIv, self.crIv),
            )
            connection.commit()

        except mysql.connector.Error as e:
            print(e)
        finally:
            # Close the cursor and connection
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    def encryptDataKey(self):
        """Takes a data key as input and encrypts it using the HSM root key.

        Args:
            dataKey (DataKey): A cryptographic Key that shall be encrypted.

        Returns:
            Datakey: The encrypted key.
        """
        session = None
        lib = None

        try:
            # Load the SoftHSM PKCS11 module & start session
            lib = PyKCS11Lib()
            lib.load(cn.HSMCONFIG["pkcs11"])
            session = lib.openSession(cn.HSMCONFIG["slotId"])
            session.login(cn.HSMCONFIG["password"])

            # Find the AES Root key
            aesKey = session.findObjects(
                [
                    (PyKCS11.CKA_LABEL, cn.HSMCONFIG["key"]),
                    (PyKCS11.CKA_CLASS, CKO_SECRET_KEY),
                ]
            )[0]

            # Encrypt the key using the AES Root key
            mechanism = PyKCS11.Mechanism(CKM_AES_CBC_PAD, self.keyIv)
            encryptedKey = session.encrypt(aesKey, self.dataKey, mechanism)

            return DataKey(bytes(encryptedKey), self.keyIv, self.crIv)

        except Exception as e:
            raise HsmError(e)
        finally:
            # Close session gracefully
            if session:
                session.logout()
                session.closeSession()

    def decryptDataKey(self):
        """Takes an encrypted key and an IV as input and decrypts it using the root key token that is stored in the HSM slot.

        Args:
            dataKey (DataKey): Encrypted key that shall be decrypted.

        Returns:
            DataKey: Decrypted Datakey.
        """
        session = None
        lib = None
        try:
            # Load the SoftHSM PKCS11 module & start session
            lib = PyKCS11Lib()
            lib.load(cn.HSMCONFIG["pkcs11"])
            session = lib.openSession(cn.HSMCONFIG["slotId"])
            session.login(cn.HSMCONFIG["password"])

            # Find the AES Root key
            aesKey = session.findObjects(
                [
                    (PyKCS11.CKA_LABEL, cn.HSMCONFIG["key"]),
                    (PyKCS11.CKA_CLASS, CKO_SECRET_KEY),
                ]
            )[0]

            # Decrypt the key using the AES Root key
            mechanism = PyKCS11.Mechanism(CKM_AES_CBC_PAD, self.keyIv)
            decryptedKey = session.decrypt(aesKey, self.dataKey, mechanism)

            return DataKey(bytes(decryptedKey), self.keyIv, self.crIv)
        except Exception as e:
            raise HsmError(e)
        finally:
            # Close session gracefully
            if session:
                session.logout()
                session.closeSession()


def generateAesKey(length=32) -> bytes:
    """Generates a random AES key in the specified length.

    Args:
        length (int, optional): Length of the key. Defaults to 32.

    Raises:
        ValueError: Invalid key length.

    Returns:
        bytes: Random AES key.
    """
    if length not in (16, 24, 32):
        raise ValueError("Invalid key length. Must be 16, 24, or 32 bytes.")
    return os.urandom(length)


def generateIv(length=16) -> bytes:
    """Generates a random Initialization Vector for AES in the specified length.

    Args:
        length (int, optional): Lenght of the key. Defaults to 16.

    Raises:
        ValueError: Invalid key length.

    Returns:
        bytes: Random IV.
    """
    if length not in (8, 16):
        raise ValueError("Invalid key length. Must be 8, or 16 bytes.")
    return os.urandom(length)


def generateDataKey() -> DataKey:
    """Creates a random data key object.

    Returns:
        DataKey: DataKey.
    """
    dataKey = generateAesKey()
    keyIv = generateIv()
    crIv = generateIv()
    return DataKey(dataKey, keyIv, crIv)


def fetchDataKey(crId) -> DataKey:
    """Given a credentials id, fetches the corresponding data key object that has been used for encryption.

    Args:
        crId (str): credentials Id for the desired data key

    Returns:
        DataKey: The decrypted datakey object.
    """
    try:
        connection = mysql.connector.connect(**cn.DBCONFIG)
        cursor = connection.cursor()

        selectQuery = "SELECT data_key, key_iv, cr_iv FROM data_keys WHERE cr_id = %s"
        cursor.execute(selectQuery, (crId,))
        result = cursor.fetchone()
        if not result:
            return None

        # Convert the fetched values into a DataKey object
        dataKey, keyIv, crIv = result
        dataKey = DataKey(dataKey, keyIv, crIv)
        decryptedDataKey = dataKey.decryptDataKey()
        return decryptedDataKey
    except Exception:
        print("Can't fetch encrypted data key.")
    finally:
        # Close the cursor and connection
        if cursor:
            cursor.close()
        if connection:
            connection.close()


class HsmError(Exception):
    """Exception raised for errors in the hardware security module."""

    pass
