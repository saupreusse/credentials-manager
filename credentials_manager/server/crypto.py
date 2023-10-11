from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import json
import bcrypt
import keys


def encryptCredentials(dataKey : keys.DataKey, plaintext):
    """
    Encrypts a string using a DataKey and crIv in  AES CBC mode.

    Args:
        dataKey (DataKey): DataKey object containing the encryption key and crIv.
        plaintext (dict): Credentials to encrypt.

    Returns:
        bytes: The encrypted ciphertext.
    """
    try:
        # Create a Cipher object using AES algorithm in CBC mode
        cipher = Cipher(
            algorithms.AES(bytes(dataKey.dataKey)),
            modes.CBC(dataKey.crIv),
            backend=default_backend(),
        )

        # Encrypt the plaintext
        padder = padding.PKCS7(128).padder()
        encryptor = cipher.encryptor()
        plaintextBytes = json.dumps(plaintext).encode("utf-8")
        paddedData = padder.update(plaintextBytes) + padder.finalize()
        ciphertext = encryptor.update(paddedData) + encryptor.finalize()

        return ciphertext
    except Exception as e:
        print(f"Error: {e}")
        return None


def decryptCredentials(dataKey, ciphertext):
    """
    Decrypts credentials in ciphertext using a DataKey and crIv.

    Args:
        dataKey (DataKey): The DataKey object containing the decryption key and crIV.
        ciphertext (bytes): The encrypted ciphertext.

    Returns:
        dict[str]: The decrypted credentials.
    """
    try:
        # Create a Cipher object using AES algorithm in CBC mode
        cipher = Cipher(
            algorithms.AES(bytes(dataKey.dataKey)),
            modes.CBC(dataKey.crIv),
            backend=default_backend(),
        )

        # Decrypt the ciphertext
        unpadder = padding.PKCS7(128).unpadder()
        decryptor = cipher.decryptor()
        decryptedData = decryptor.update(ciphertext) + decryptor.finalize()
        plaintext = unpadder.update(decryptedData) + unpadder.finalize()

        return json.loads(plaintext.decode("utf-8"))
    except Exception as e:
        print(f"Error: {e}")
        return None


def hashAndSaltPassword(password):
    """Takes a cleartext password as input and returns a tuple of salt and password hash.

    Args:
        password (_type_): _description_

    Returns:
        bytes: Salt that was used to create salted and hashed password.
        bytes: A salted and hashed password.
    """
    salt = bcrypt.gensalt()
    hashedPassword = bcrypt.hashpw(password.encode("utf-8"), salt)
    return salt, hashedPassword
