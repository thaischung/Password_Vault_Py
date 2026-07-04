import sqlite3
from datetime import datetime
import hmac

class UserDatabase:
    def __init__(self, filename="auth.db"):
        self.connection = sqlite3.connect(filename)

        self.cursor = self.connection.cursor()

        self.cursor.execute(
            "CREATE TABLE IF NOT EXISTS user ("
            "id INTEGER PRIMARY KEY, "
            "challenge_text TEXT, "
            "challenge_response_hash BLOB, "
            "username TEXT, "
            "password_hash BLOB, "
            "salt BLOB, "
            "failed_attempts INTEGER DEFAULT 0, "
            "lockout_timestamp TEXT, "
            "last_logon_timestamp TEXT, "
            "last_logout_timestamp TEXT, "
            "last_failed_attempt_timestamp TEXT, "
            "last_changed_timestamp TEXT, "
            "entry_changed INTEGER DEFAULT 0"
            ")"
        )

    # check if a user exists 
    def user_exists(self):
        self.cursor.execute("SELECT EXISTS (SELECT 1 FROM user)")
        return self.cursor.fetchone()[0] == 1
    
    # create the user
    def create_user(self, challenge_text, response, username, password, salt):
        # if a user already exists do not allow creation of another user
        if self.user_exists():
            print("A User Already Exists.")
            return
        
        self.cursor.execute(
            "INSERT INTO user (challenge_text, challenge_response_hash, username, password_hash, salt)"
            "VALUES (?, ?, ?, ?, ?)",
            (challenge_text, response, username, password, salt)
        )

        self.connection.commit()

    # checks that the challenge response is correct
    def verify_response(self, response):
        self.cursor.execute(
            "SELECT challenge_response_hash FROM user"
        )

        result = self.cursor.fetchone()[0]

        return hmac.compare_digest(result, response)
    
    # check the username
    def verify_username(self, username):
        self.cursor.execute(
            "SELECT username FROM user"
        )

        result = self.cursor.fetchone()[0]

        return result == username

    # checks that the password is correct
    def verify_password(self, password):
        self.cursor.execute(
            "SELECT password_hash FROM user"
        )

        result = self.cursor.fetchone()[0]

        return hmac.compare_digest(result, password)

    # set the last logon time
    def last_logon(self):
        now = datetime.now().isoformat()

        self.cursor.execute(
            "UPDATE user SET last_logon_timestamp = ?", (now, )
        )

        self.connection.commit()

    # set the last logout time
    def last_logout(self):
        now = datetime.now().isoformat()

        self.cursor.execute(
            "UPDATE user SET last_logout_timestamp = ?", (now, )
        )

        self.connection.commit()
    
    # set the last fail attempt time
    def last_failed_attempt(self):
        now = datetime.now().isoformat()

        self.cursor.execute(
            "UPDATE user SET last_failed_attempt_timestamp = ?", (now, )
        )

        self.connection.commit()

    # set the last changed time
    def last_changed(self):
        now = datetime.now().isoformat()

        self.cursor.execute(
            "UPDATE user SET last_changed_timestamp = ?", (now, )
        )

        self.connection.commit()
    
    # set the last entry changed
    def set_last_changed_entry(self, entry_number):
        self.cursor.execute(
            "UPDATE user SET entry_changed = ?", (entry_number,)
        )

    # increment the number of failed sign in attempts
    def increment_failed_attempts(self):
        self.cursor.execute(
            "UPDATE user SET failed_attempts = failed_attempts + 1"
        )

        self.connection.commit()

    # reset the number of failed sign in attempts
    def reset_failed_attempts(self):
        self.cursor.execute(
            "UPDATE user SET failed_attempts = 0"
        )

        self.connection.commit()

    # set the timestamp that the user was locked out
    def lockout_timestamp(self):
        now = datetime.now().isoformat()

        self.cursor.execute(
            "UPDATE user SET lockout_timestamp = ?", (now, )
        )

        self.connection.commit()
    
    # check if the user is currently locked out, if so calculate the time left
    def is_lockout(self):
        self.cursor.execute(
            "SELECT lockout_timestamp FROM user"
        )

        result = self.cursor.fetchone()[0]

        return result is not None
    
    # clear the lockout timestamp
    def clear_lockout(self):
        self.cursor.execute(
            "UPDATE user SET lockout_timestamp = NULL"
        )

        self.connection.commit()
        
    # get the salt
    def get_salt(self):
        self.cursor.execute(
            "SELECT salt FROM user"
        )

        return self.cursor.fetchone()[0]

    # get the number of failed sign in attempts
    def get_failed_attempts(self):
        self.cursor.execute(
            "SELECT failed_attempts FROM user"
        )

        return self.cursor.fetchone()[0]
    
    # get the challenge text
    def get_challenge_text(self):
        self.cursor.execute(
            "SELECT challenge_text FROM user"
        )

        return self.cursor.fetchone()[0]
    
    # get the last failed attempts
    def get_last_failed_attempts(self):
        self.cursor.execute(
            "SELECT last_failed_attempt_timestamp FROM user"
        )

        return self.cursor.fetchone()[0]
    
    