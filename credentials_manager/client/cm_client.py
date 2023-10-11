from credentialsManager import credentialsManager

try:
    client = credentialsManager.createClient()
    request = ("GET_CR", {"label" : "webappcr"})
    result = client.execute(request)
    print("Received message:", result)
except Exception as e:
    print(f"Error: {e}")


