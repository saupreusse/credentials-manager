from cryptography.fernet import Fernet


def encryptConfig(configFile):
    # Generate a crypto key and save it to a file called "crypto_key.key".
    key = Fernet.generate_key()
    with open("crypto_key.key", "wb") as ck:
        ck.write(key)

    # Read the plaintext config.
    with open(configFile, "r") as file:
        plaintext = file.read().encode()

    # Encrypt and save the config to a file called "encrypted_db_config.ini"
    cipherSuite = Fernet(key)
    ciphertext = cipherSuite.encrypt(plaintext)
    with open("encrypted_db_config.ini", "wb") as file:
        file.write(ciphertext)


def decryptConfig(configFile, keyFile):
    # Load the crypto key.
    with open(keyFile, "rb") as kf:
        key = kf.read()

    # Load the encrypted config file and decrypt it.
    cipherSuite = Fernet(key)
    with open(configFile, "rb") as cf:
        ciphertext = cf.read()
    plaintext = cipherSuite.decrypt(ciphertext).decode()

    return plaintext
