import json
from jsonschema import validate

# CONFIGURATION FILES
DBCONFIGFILE = "config/cm_database_config.json"
HSMCONFIGFILE = "config/hsm_config.json"

# JSON schema for the DB config structure
DBSCHEMA = {
    "type": "object",
    "properties": {
        "host": {"type": "string"},
        "user": {"type": "string"},
        "password": {"type": "string"},
        "database": {"type": "string"},
        "port": {"type": "integer"},
    },
    "required": ["host", "user", "password"],
    "additionalProperties": False,
}

# JSON schema for the HSM config structure
HSMSCHEMA = {
    "type": "object",
    "properties": {
        "pkcs11": {"type": "string"},
        "slotid": {"type": "integer"},
        "password": {"type": "string"},
        "key": {"type": "string"},
    },
    "required": ["pkcs11", "slotid", "password", "key"],
    "additionalProperties": False,
}


def validateDict(inputDict, schema):
    """
    Validates a dictionary to check if it matches the expected JSON schema.

    Parameters:
        inputDict (dict): The dictionary to be validated.
        schema (dict) : The schema to be validated against.

    Returns:
        bool: True if the dictionary is valid, False otherwise.
        str: A message indicating the validation result.
    """

    try:
        validate(instance=inputDict, schema=schema)
        return True
    except:
        return False


def getDBConfig():
    """Returns a dictionary for database connection.

    Returns:
        dict : Dictionary containing all necessary information to connect to a mariaDB database.

    Raises:
        Exception: Failed to get database configuration.
    """
    try:
        with open(DBCONFIGFILE, "r") as f:
            data = json.load(f)
            if validateDict(data, DBSCHEMA):
                config = {
                    "user": data["user"],
                    "password": data["password"],
                    "host": data["host"],
                    "database": data["database"],
                    "raise_on_warnings": True,
                }
                return config
            else:
                raise Exception("Invalid DB configuration format.")
    except:
        raise FileNotFoundError("Failed to get database configuration.")


def getHsmConfig():
    """Returns a dictionary for hsm connection.

    Returns:
        dict : Dictionary containing all necessary information to connect to an hsm slot.
    """
    try:
        with open(HSMCONFIGFILE, "r") as f:
            data = json.load(f)
            if validateDict(data, HSMSCHEMA):
                config = {
                    "pkcs11": data["pkcs11"],
                    "slotId": data["slotid"],
                    "password": data["password"],
                    "key": data["key"],
                }
                return config
            else:
                raise Exception("Invalid HSM configuration format.")
    except:
        raise FileNotFoundError("Failed to get hsm configuration.")


DBCONFIG = getDBConfig()
HSMCONFIG = getHsmConfig()
