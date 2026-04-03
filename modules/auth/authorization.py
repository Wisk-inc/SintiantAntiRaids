import json
import os
from tinydb import TinyDB, Query

class AuthorizationSystem:
    def __init__(self):
        os.makedirs("data", exist_ok=True)
        self.db = TinyDB("data/auth_registry.json")
        self.registry = self.db.table("registry")

    def is_authorized(self, guild_id, user_id):
        # Owner is always authorized
        # Check database for authorized users
        User = Query()
        result = self.registry.get((User.guild_id == guild_id) & (User.user_id == user_id))
        return result is not None

    def authorize_user(self, guild_id, user_id):
        User = Query()
        if not self.is_authorized(guild_id, user_id):
            self.registry.insert({"guild_id": guild_id, "user_id": user_id})
            return True
        return False

    def deauthorize_user(self, guild_id, user_id):
        User = Query()
        result = self.registry.remove((User.guild_id == guild_id) & (User.user_id == user_id))
        return len(result) > 0

    def get_authorized_users(self, guild_id):
        User = Query()
        results = self.registry.search(User.guild_id == guild_id)
        return [res["user_id"] for res in results]
