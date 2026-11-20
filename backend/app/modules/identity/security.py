from app.core.security import hash_token, new_url_token

new_action_token = new_url_token

__all__ = ["hash_token", "new_action_token", "new_url_token"]
