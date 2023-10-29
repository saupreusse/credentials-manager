#!/usr/bin/python3

import cgi
import mysql.connector


print("Content-Type: text/html")
print()

try:
    # Connect to the MariaDB server using hardcoded plaintext credentials.
    conn = mysql.connector.connect(
        host="localhost",
        user="wepapp",
        password="webapppassword",
        database="testdatabase",
    )
    conn.close()
    print("<h1>Connected successfully</h1>")
except mysql.connector.Error:
    print("<h1>Connection failed</h1>")
