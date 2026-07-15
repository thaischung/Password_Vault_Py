from vault_database import VaultDatabase
from user_database import UserDatabase
from password_helper import PasswordHelper
from ui import PasswordVault
import sys
import os 
import getpass
import time
import os


class App:
    def __init__(self, VDB = "vault.db", UDB = "auth.db"):
        self.max_attempts = 5
        self.userDB = UserDatabase(UDB)
        self.vaultDB = VaultDatabase(VDB)

        if self.userDB.is_lockout():
            print("VAULT NOT SECURED!\nLOCKOUT ENABLED")
            sys.exit(1)
        
        self._boot()
    
    # application boot
    def _boot(self):
        if not self.userDB.user_exists():
            self._first_run()
        else:
            self._login()

    # the first time the user runs the app need to set up user
    def _first_run(self):
        # prompt for cred creation 
        self._type_effect("Challenge Text:")
        challenge_text = input("> ")

        self._type_effect("Response:")
        response = input("> ")
        
        self._type_effect("Username:")
        username = input("> ")

        self._type_effect("Password:")
        password = getpass.getpass("> ")

        self._type_effect("Re-type Password:")
        password_confimation = getpass.getpass("> ")

        while password_confimation != password:
            self._type_effect("Re-type Password:")
            password_confimation = getpass.getpass("> ")

        # gerneate a random 16 byte salt
        salt = os.urandom(16)

        # hash both the password and response using the salt we generated
        response_hash = PasswordHelper.sha256_hash_util(response, salt)
        password_hash = PasswordHelper.sha256_hash_util(password, salt)

        # derive our key for symmetirc encryption
        self.key = PasswordHelper.derive_key(password.encode(), salt)

        # create the user
        self.userDB.create_user(challenge_text, response_hash, username, password_hash, salt)

        self.userDB.last_logon()

        self._vault()
    
    # if a user exists login screen 
    def _login(self):
        # first check if the lockout sequence is initiated
        if self.userDB.is_lockout():
            self._type_effect("Lockout.")
            sys.exit(1)

        # promt for the response to the challenge text
        self._type_effect(self.userDB.get_challenge_text())
        response = input("> ")
        
        # get the user's salt
        salt = self.userDB.get_salt()
        
        # hash the response since we are storing the response hashed in the db
        hashed_response = PasswordHelper.sha256_hash_util(response, salt)

        # if the response is wrong display the message and kill the process
        if not self.userDB.verify_response(hashed_response):
            self._type_effect("Authentication Failed.")
            sys.exit(1)

        # promt for the username
        self._type_effect("Username:")
        username = input("> ")
        
        # promt for the password
        self._type_effect("Password:")
        password = getpass.getpass("> ")

        # hash the password
        hashed_password = PasswordHelper.sha256_hash_util(password, salt)
        
        # while the username or password is wrong prompt the user until we reach max attempts 
        while (not self.userDB.verify_username(username) or not self.userDB.verify_password(hashed_password)) and self.userDB.get_failed_attempts() < self.max_attempts:
            self.userDB.increment_failed_attempts()

            self._type_effect("Username:")
            username = input("> ")

            self._type_effect("Password:")
            password = getpass.getpass("> ")
            hashed_password = PasswordHelper.sha256_hash_util(password, salt)
        
        # if the number of failed login attemps have reached the max then lockout
        if self.userDB.get_failed_attempts() == self.max_attempts:
            self._type_effect("Authentication Failed.")
            os.system('cls' if os.name == 'nt' else 'clear')
            self._type_effect("Lockout Initiated.")

            # set the timestamp that the lockout happened
            self.userDB.lockout_timestamp()
            sys.exit(1)

        self.key = PasswordHelper.derive_key(password.encode(), salt)

        # loading
        os.system('cls' if os.name == 'nt' else 'clear')
        self._type_effect("Initilizing Vault...")
        time.sleep(3)
        
        os.system('cls' if os.name == 'nt' else 'clear')
        self._type_effect(f"Welcome Back {username}")
        time.sleep(3)

        self.userDB.reset_failed_attempts()
        self.userDB.last_logon()
        # move to vault screen
        self._vault()
    
    def _type_effect(self, text, delay=0.09):
        # loop through the text and print the characters one by one
        for char in text:
            # print the char, prevent automatic line breaks with end='', print instantly with flush=True
            print(char, end='', flush=True)
            # pause for x amount of delay
            time.sleep(delay)
        # print a newline character    
        print()

    def _vault(self):
        ui = PasswordVault(self.vaultDB, self.key, self.userDB)
        ui.run()

