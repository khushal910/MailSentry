def get_me(user: dict) -> dict:
    """
    Formats the raw MongoDB user document into the shape the frontend expects:
    {
        "id":    str,
        "name":  str,   # stored as 'username' in MongoDB
        "email": str,
        "role":  str,
    }
    """
    return {
        "id": str(user["_id"]),
        "name": user.get("username", ""),
        "email": user.get("email", ""),
        "role": user.get("role", "user"),
    }
