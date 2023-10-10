#!/usr/bin/python3
import sys
import json

sys.path.append("/home/julian/.local/lib/python3.9/site-packages")

print("Content-Type: text/html")
print()
print("<h1> Credentials Manager Test Page </h1>")
try:
    import mysql.connector

    print("<p>MySQL connector imported successfully.</p>")
    from credentialsManager import credentialsManager

    print("<p>CM imported successfully.</p>")
except Exception as e:
    print(f"Error: {e}")

try:
    client = credentialsManager.createClient()
    request = ("GET_CR", {"label": "webappcr"})
    result = client.execute(request)
except Exception as e:
    print(f"Error: {e}")

config = json.loads(result)
print(f"<p>Credentials: {config}</p>")

try:
    # Connect to MariaDB
    conn = mysql.connector.connect(**config)
    cursor = conn.cursor()

    # For demonstration purposes, we'll just fetch the version of MariaDB
    cursor.execute("SELECT VERSION()")
    version = cursor.fetchone()

    print(f"<h2>Connected to MariaDB</h2>")
    print(f"<p>Version: {version[0]}</p>")

except mysql.connector.Error as err:
    print(f"<p>Error connecting to MariaDB:</p>")
    print(f"<p>{err}</p>")

finally:
    if "cursor" in locals() and cursor:
        cursor.close()
    if "conn" in locals() and conn:
        conn.close()
