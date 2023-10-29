#!/usr/bin/python3

import cgi
import mysql.connector
import os


print("Content-Type: text/html")
print()

try:
    # Connect to the MariaDB server using credentials stored in environment variables
    conn = mysql.connector.connect(
        host=os.environ.get("DATABASE_HOST"),
        user=os.environ.get("DATABASE_USER"),
        password=os.environ.get("DATABASE_PASSWORD"),
        database=os.environ.get("DATABASE_NAME"),
    )
    conn.close()
    print("<h1>Connected successfully</h1>")
except mysql.connector.Error:
    print("<h1>Connection failed</h1>")
