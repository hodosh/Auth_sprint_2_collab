import uuid

register_data = {
    "password": "password",
    "password_confirm": "password",
    "email": f"{uuid.uuid4()}@admin.admin",
}

passwords_mismatch_data = {
    "password": "1",
    "password_confirm": "2",
    "email": f"{uuid.uuid4()}@admin.admin",
}

register_base_data = {
    "password": "password",
    "password_confirm": "password",
    "email": "user@admin.admin",
}

update_user_data = {
    "old_password": "password",
    "new_password_confirm": "password1",
    "new_password": "password1",
    "email": f"{uuid.uuid4()}@admin.admin",
}
