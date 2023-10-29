#!/usr/bin/python3

import cgi
import mysql.connector
import configparser

print("Content-Type: text/html")
print()

# Load the config file.
config = configparser.ConfigParser()
config.read('db_config.ini')
dbConfig = {
    "host": config.get("database", "host"),
    "user": config.get("database", "user"),
    "password": config.get("database", "password"),
    "database": config.get("database", "database")
}

try:
    # Connect to the MariaDB server using a config file.
    conn = mysql.connector.connect(**dbConfig)
    conn.close()
    print("<h1>Connected successfully</h1>")
except mysql.connector.Error:
    print("<h1>Connection failed</h1>")