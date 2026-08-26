from abc import ABC, abstractmethod
from flask import session, redirect, url_for, render_template, request, jsonify
import chromadb
import os
import sqlite3
import logging
import hashlib
from datetime import datetime

logger = logging.getLogger(__name__)

class AuthInterface(ABC):
    @abstractmethod
    def get_user(self, flask_request) -> any:
        pass

    @abstractmethod
    def is_logged_in(self, user: any) -> bool:
        pass

    @abstractmethod
    def override_config_for_user(self, user: any, config: dict) -> dict:
        pass

    @abstractmethod
    def login_form(self) -> str:
        pass

    @abstractmethod
    def login_handler(self, flask_request) -> str:
        pass

    @abstractmethod
    def callback_handler(self, flask_request) -> str:
        pass

    @abstractmethod
    def logout_handler(self, flask_request) -> str:
        pass

class NoAuth(AuthInterface):
    def get_user(self, flask_request) -> any:
        return {}

    def is_logged_in(self, user: any) -> bool:
        return True

    def override_config_for_user(self, user: any, config: dict) -> dict:
        return config

    def login_form(self) -> str:
        return ''

    def login_handler(self, flask_request) -> str:
        return 'No login required'

    def callback_handler(self, flask_request) -> str:
        return 'No login required'

    def logout_handler(self, flask_request) -> str:
        return 'No login required'

class BasicAuth(AuthInterface):
    def __init__(self):
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(path="D:/Admin-Module/WAI")

        # Reset users collection to avoid stale data
        # try:
        #     self.client.delete_collection("users")
        #     logging.info("Deleted existing users collection to reset")
        # except:
        #     logging.info("No existing users collection to delete")

        # Create or get collections
        self.users_collection = self.client.get_or_create_collection(name="users")
        self.workspace_collection = self.client.get_or_create_collection(name="Workspaces")

        # Hardcoded users with SHA256 hashes
        self.users = {
            "superadmin": {
                "password_hash": hashlib.sha256("admin123".encode("utf-8")).hexdigest(),
                "role": "superadmin"
            },
            "admin": {
                "password_hash": hashlib.sha256("admin123".encode("utf-8")).hexdigest(),
                "role": "admin"
            },
            "user1": {
                "password_hash": hashlib.sha256("user123".encode("utf-8")).hexdigest(),
                "role": "user",
                "workspace": "No.2"  # Default workspace for testing
            }
        }

        # Sync hardcoded users to ChromaDB and log contents
        self._sync_users_to_db()
        self._debug_users_collection()
        


    # def _get_userid(self, username: str):
    #     # Connect to ChromaDB's SQLite database
    #     conn = sqlite3.connect("D:/Admin-Module/WAI/chroma.sqlite3")
    #     cursor = conn.cursor()

    #     # Your query
    #     query = """
    #     SELECT id FROM (
    #         SELECT em.*
    #         FROM embedding_metadata em
    #         JOIN embeddings e ON em.id = e.id
    #         JOIN segments s ON e.segment_id = s.id
    #         JOIN collections c ON s.collection = c.id
    #         WHERE c.name = 'users'
    #     ) WHERE key = 'username' AND string_value = ?
    #     """

    #     cursor.execute(query, (username,))
    #     result = cursor.fetchone()
    #     conn.close()

    #     if result:
    #         user_id = result[0]
    #         logging.info(f"User ID: {user_id}")
    #         return user_id
    #     else:
    #         logging.info("User not found")
    #         return
    
    def _get_userid(self, username: str):
        """
        Resolve the user's UUID stored in the ChromaDB users collection.

        Behavior:
        - Query self.users_collection.get() and iterate ids/metadatas.
        - Return the matching ids[i] where metadatas[i]['username'] == username.
        - If not found, fall back to the legacy chroma sqlite query (keeps backward compatibility).
        - Returns None if still not found.
        """
        if not username:
            logger.info("_get_userid: empty username provided")
            return None

        try:
            # Prefer using the ChromaDB collection (same source list_users() uses)
            results = self.users_collection.get()
            if results and results.get("ids"):
                ids = results.get("ids", [])
                metadatas = results.get("metadatas", [{}] * len(ids))
                # iterate and match username in metadata (case-sensitive same as stored)
                for i, uid in enumerate(ids):
                    md = metadatas[i] if i < len(metadatas) else {}
                    md_username = md.get("username", "")
                    if md_username == username:
                        logger.info(f"_get_userid: resolved UUID from users_collection: {uid} (username={username})")
                        return uid
        except Exception:
            logger.exception("_get_userid: failed to query users_collection (ChromaDB)")

        # Fallback: legacy ChromaDB sqlite lookup (keeps existing behavior if collection lookup fails)
        try:
            conn = sqlite3.connect("D:/Admin-Module/WAI/chroma.sqlite3")
            cursor = conn.cursor()
            query = """
            SELECT id FROM (
                SELECT em.*
                FROM embedding_metadata em
                JOIN embeddings e ON em.id = e.id
                JOIN segments s ON e.segment_id = s.id
                JOIN collections c ON s.collection = c.id
                WHERE c.name = 'users'
            ) WHERE key = 'username' AND string_value = ?
            """
            cursor.execute(query, (username,))
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            if result:
                user_id = result[0]
                logger.info(f"_get_userid: resolved id from chroma sqlite fallback: {user_id} (username={username})")
                return user_id
        except Exception:
            logger.exception("_get_userid: chroma sqlite fallback failed")

        logger.info(f"_get_userid: user id not found for username={username}")
        return None


    def _sync_users_to_db(self):
        """Sync hardcoded users to ChromaDB users collection."""
        for username, user_data in self.users.items():
            existing_user = self.users_collection.get(where={"username": username})
            if not existing_user.get("metadatas"):
                logger.info(f"Adding user {username} to ChromaDB", extra={"admin": True})
                self.users_collection.add(
                    ids=[username],
                    metadatas=[{
                        "username": username,
                        "password_hash": user_data["password_hash"],
                        "role": user_data["role"],
                        "workspace": user_data.get("workspace", "")
                    }],
                    documents=[username]
                )
            else:
                logger.info(f"Updating user {username} in ChromaDB", extra={"admin": True})
                # Preserve existing metadata (like agent_config)
                current_metadata = existing_user["metadatas"][0]
                current_metadata.update({
                    "username": username,
                    "password_hash": user_data["password_hash"],
                    "role": user_data["role"],
                    "workspace": user_data.get("workspace", "")
                })
                
                self.users_collection.update(
                    ids=[username],
                    metadatas=[current_metadata],
                    documents=[username]
                )

    def _debug_users_collection(self):
        """Log contents of users collection for debugging."""
        results = self.users_collection.get()
        logger.info(f"Users in ChromaDB collection: {results['metadatas']}", extra={"admin": True})

    def get_user(self, flask_request) -> any:
        username = session.get('username')
        if username:
            results = self.users_collection.get(where={"username": username}, limit=1)
            if results.get("metadatas"):
                user_record = results["metadatas"][0]
                return {
                    "username": username,
                    "role": user_record.get("role", "user"),
                    "workspace": user_record.get("workspace", "")
                }
        return None

    def is_logged_in(self, user: any) -> bool:
        return user is not None and 'username' in user

    def override_config_for_user(self, user: any, config: dict) -> dict:
        config_copy = config.copy()
        config_copy["allow_admin_access"] = (user and user.get("role") == "admin")
        return config_copy

    def login_form(self) -> str:
        return render_template('login.html')

    # def login_handler(self, flask_request, cache):
    def login_handler(self, flask_request):
        if flask_request.method == 'POST':
            username = flask_request.form.get('username', '').strip()
            password = flask_request.form.get('password', '')

            if not username or not password:
                logger.warning("Login attempt with missing username or password", extra={"admin": True})
                logger.warning("Login attempt with missing username or password", extra={"user": True})
                return render_template('login.html', error="Username and password are required")

            # Hash the input password using SHA256
            password_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()

            try:
                # Fetch user from ChromaDB
                users_collection = self.client.get_collection(name="users")
                results = users_collection.get(
                    where={"username": username},
                    limit=1
                )
                user_record = None
                if results.get("metadatas"):
                    user_record = results["metadatas"][0]
                    logger.info(f"Found user record for {username}: {user_record}", extra={"admin": True})
                    logger.info(f"Logged User: {username}", extra={"user": True})
                else:
                    logger.warning(f"No user record found for username: {username}", extra={"admin": True})
                    logger.warning(f"No user record found for username: {username}", extra={"user": True})
                    return render_template('login.html', error="Invalid username or password")

                if user_record and user_record.get("password_hash") == password_hash:
                    role = str(user_record.get("role", "user")).lower()
                    stored_workspace = user_record.get("workspace", "")

                    # Re-validate workspace live against ChromaDB (accepts name or ID).
                    # This corrects users whose workspace was saved as a UUID or bad value.
                    workspace_valid = user_record.get("workspace_valid", False)
                    if not workspace_valid and role not in ("superadmin", "admin"):
                        try:
                            ws_data = self.client.get_collection("workspaces").get()
                            ws_names = [md.get("name", "") for md in (ws_data.get("metadatas") or [])]
                            ws_ids   = ws_data.get("ids") or []
                            if stored_workspace and (stored_workspace in ws_names or stored_workspace in ws_ids):
                                workspace_valid = True
                                logger.info(f"Live workspace re-validation passed for {username} (stored='{stored_workspace}')", extra={"admin": True})
                        except Exception as _ws_err:
                            logger.warning(f"Live workspace re-validation failed for {username}: {_ws_err}", extra={"admin": True})

                    if not workspace_valid and role not in ("superadmin", "admin"):
                        logger.warning(f"Workspace not valid for user {username}", extra={"admin": True})
                        logger.warning(f"Workspace not valid for user {username}", extra={"user": True})
                        return render_template('login.html', error="User is restricted. Please contact admin.")
                    user_id = self._get_userid(username)
                    session['username'] = username
                    session['user_id'] = user_id
                    # cache.refresh_cache_for_user(user_id)
                    # logger.info(f"Cache updated: {cache}")
                    session['role'] = role
                    login_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    session['login_time'] = login_time
                    logger.info(f"Session details from auth.py: \nusername:{username}\nuser_id:{user_id}\nrole:{role}\nlogin_time:{login_time}", extra={"session":True})
                    logger.info(f"User {username} authenticated with role {role} Login time {login_time}", extra={"admin": True})
                    logger.info(f"User {username} authenticated with role {role} Login time {login_time}", extra={"user": True})

                    try:
                        if role == "superadmin":
                            logger.info("Redirecting to superadmin endpoint", extra={"admin": True})
                            return redirect(url_for('superadmin'))
                        elif role == "admin":
                            logger.info("Redirecting to admin endpoint", extra={"admin": True})
                            return redirect(url_for('admin'))
                        else:
                            logger.info("Redirecting to user endpoint", extra={"admin": True})
                            return redirect(url_for('user'))
                    except Exception as e:
                        logger.error(f"Redirection error for {username}: {e}", extra={"admin": True})
                        return render_template('login.html', error="Redirection failed. Please try again.")

                else:
                    logger.warning(f"Invalid password for username: {username}", extra={"admin": True})
                    logger.warning(f"Invalid password for username: {username}", extra={"user": True})
                    return render_template('login.html', error="Invalid username or password")

            except Exception as e:
                logger.error(f"Login error for {username}: {e}", extra={"admin": True})
                logger.error(f"Login error for {username}: {e}", extra={"user": True})
                return render_template('login.html', error="Login failed due to server error")

        logger.info("Rendering login page for GET request")
        return render_template('login.html')

    def callback_handler(self, flask_request) -> str:
        logger.info("Handling callback, redirecting to login", extra={"admin": True})
        return redirect(url_for('login'))

    def logout_handler(self, flask_request) -> str:
        logger.info(f"Session before logout: {session}", extra={"admin": True})
        session.clear()
        logger.info("User logged out", extra={"admin": True})
        logger.info("User logged out", extra={"user": True})
        return redirect(url_for('login'))  


    def get_user_workspace_id(self, username):
        """Fetch workspace_id for a user from ChromaDB."""
        try:
            # Fetch user from users collection
            user_results = self.users_collection.get(where={"username": username}, limit=1)
            if not user_results.get("metadatas"):
                logger.warning(f"No user record found for {username}", extra={"admin": True})
                logger.warning(f"No user record found for {username}", extra={"user": True})
                return None

            user_record = user_results["metadatas"][0]
            workspace_name = user_record.get("workspace")
            logger.info(f"Inside get_user_workspace_id: {workspace_name}")
            if not workspace_name:
                logger.warning(f"No workspace assigned for user {username}", extra={"admin": True})
                logger.warning(f"No workspace assigned for user {username}", extra={"user": True})
                return None

            # Fetch workspace_id from Workspaces collection
            workspace_results = self.workspace_collection.get(where={"name": workspace_name}, limit=1)
            if not workspace_results.get("metadatas"):
                logger.warning(f"No workspace found with name {workspace_name}", extra={"admin": True})
                logger.warning(f"No workspace found with name {workspace_name}", extra={"user": True})
                return None

            workspace_id = workspace_results["ids"][0]  # Assuming id is stored in ids
            logger.info(f"Found workspace_id {workspace_id} for user {username} and workspace {workspace_name}", extra={"admin": True})
            logger.info(f"Found workspace_id {workspace_id} for user {username} and workspace {workspace_name}", extra={"user": True})
            return workspace_id

        except Exception as e:
            logger.error(f"Error fetching workspace_id for {username}: {e}", extra={"admin": True})
            logger.error(f"Error fetching workspace_id for {username}: {e}", extra={"user": True})
            return None

    def update_user_config(self, user_id: str, agent_config: list) -> bool:
        """
        Update the agent_config for a specific user in ChromaDB.
        """
        try:
            # Check if user exists
            results = self.users_collection.get(ids=[user_id], limit=1)
            if not results or not results.get("ids"):
                logger.warning(f"User ID {user_id} not found for config update", extra={"admin": True})
                return False
            
            # Get current metadata to preserve other fields
            current_metadata = results["metadatas"][0]
            
            # Update agent_config (store as JSON string)
            import json
            current_metadata["agent_config"] = json.dumps(agent_config)
            
            self.users_collection.update(
                ids=[user_id],
                metadatas=[current_metadata]
            )
            logger.info(f"Updated agent_config for user {user_id}", extra={"admin": True})
            return True
        except Exception as e:
            logger.error(f"Error updating user config for {user_id}: {e}", extra={"admin": True})
            return False