from jsonschema import validate, ValidationError
import json

# Schema which specifies the CM protocol structure used for client/server communication.
PROTOCOLSCHEMA = {
    "type": "object",
    "properties": {
        "header": {
            "type": "object",
            "properties": {
                "cmUser": {"type": "string"},
                "cmPassword": {"type": "string"},
                "cmRequest": {"type": "string"},
            },
            "required": ["cmUser", "cmPassword", "cmRequest"],
        },
        "payload": {
            "type": "object",
            "properties": {"args": {"type": "object"}},
            "required": ["args"],
        },
    },
    "required": ["header", "payload"],
}


def validatePacket(packet : str) -> bool:
    """Validates if a message form follows protocol guidelines.

    Args:
        message (dict): Message to validate, received from client.

    Returns:
        bool: True if the message is valid, else False.
    """
    try:
        packet = json.loads(packet)
        validate(instance=packet, schema=PROTOCOLSCHEMA)
        return True
    except ValidationError:
        return False