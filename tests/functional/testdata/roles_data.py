def create_role(name: str, permission_id: str):
    return {
        "name": name,
        "permissions": [
            {
                "value": "true",
                "id": permission_id
            }
        ]
    }
