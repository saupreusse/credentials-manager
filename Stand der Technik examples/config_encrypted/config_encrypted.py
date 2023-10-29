#!/usr/bin/python3

import cgi
import mysql.connector
import configparser
from crypto import decryptConfig

print("Content-Type: text/html")
print()

# Apply the decryption function on the encrypted config file.
config = configparser.ConfigParser()
config.read_string(decryptConfig("encrypted_db_config.ini", "crypto_key.key"))
dbConfig = {
    "host": config.get("database", "host"),
    "user": config.get("database", "user"),
    "password": config.get("database", "password"),
    "database": config.get("database", "database"),
}

try:
    # Connect to the MariaDB server using the decrypted config file.
    conn = mysql.connector.connect(**dbConfig)
    conn.close()
    print("<h1>Connected successfully</h1>")
except mysql.connector.Error:
    print("<h1>Connection failed</h1>")
