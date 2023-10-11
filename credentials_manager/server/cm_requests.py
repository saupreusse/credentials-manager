import credentials as cr
import users
import permissions as perms

# Executable functions for different requests
def getCr(user : users.cmUser, label : str):
    if perms.verifyPermission(user.cmUsername, label):
        credentials = cr.fetchCredentials(label)
        return credentials


# Dispatch table mapping commands to functions
REQUESTS = {
    "GET_CR": getCr,
}


def requestHandler(packet):
    """Handles incoming CM packets depending on their request type
    and executes the corresponding functions.

    Args:
        packet (_type_): _description_

    Raises:
        PacketError: _description_
        PacketError: _description_
        PacketError: _description_

    Returns:
        _type_: _description_
    """
    # Extract header and payload
    header = packet["header"]
    payload = packet["payload"]

    user = users.cmUser(cmUsername=header["cmUser"], cmPassword=header["cmPassword"])
    requestType = header["cmRequest"]
    args = list(payload["args"].values())

    if requestType in REQUESTS:
        try:
            # Try executing the request with the provided arguments
            return REQUESTS[requestType](user, *args)
        except TypeError as e:
            # Handle arguments gracefully
            raise PacketError(f"Error: Incorrect number of arguments for '{requestType}'. {e}")
        except Exception as e:
            # Handle all other exceptions
            raise PacketError(f"Error: {e}")
    else:
        raise PacketError("Error: Invalid packet structure.")

class PacketError(Exception):
    pass