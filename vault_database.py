from entry import Entry # first one is the module second is the class
import sqlite3

class VaultDatabase:

    def __init__(self):   
        # connect to database (creates it if it doesn't exist)
        self.connection = sqlite3.connect("vault.db")

        # create a cursor to execute commands
        self.cursor = self.connection.cursor()

        # create a table if it is not already created
        # BLOB is for binary data 
        self.cursor.execute(
            "CREATE TABLE IF NOT EXISTS entries ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "site_name TEXT NOT NULL, "
            "url TEXT, "
            "username TEXT NOT NULL, "
            "encrypted_password BLOB NOT NULL, "
            "iv BLOB, "
            "created_at TEXT, "
            "modified_at TEXT, "
            "notes TEXT, "
            "favorite INTEGER DEFAULT 0, "
            "password_strength INTEGER, "
            "totp_secret BLOB"
            ")"
        )
    
    # add entry
    def add_entry(self, entry):
        # insert the new entry values into the database using parameterized queries to prevent SQL injection
        # ? sanitizes the input automatically 
        self.cursor.execute(
            "INSERT INTO entries (site_name, url, username, encrypted_password, iv, created_at, modified_at, notes, favorite, password_strength, totp_secret)"
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (entry.site_name, entry.url, entry.username, entry.encrypted_password, entry.iv, entry.created_at, entry.modified_at, entry.notes, entry.favorite, entry.password_strength, entry.totp_secret)
        )

        # commit changes to have the database save the changes
        self.connection.commit()

    # remove entry
    def remove_entry(self, id):
        # delete the row where the id matches the id
        self.cursor.execute(f"DELETE FROM entries WHERE id = ?", (id,))

        # commit changes to have the database save the changes
        self.connection.commit()

    # modify entry
    def modify_entry(self, id, new_entry):
        # check if the entry exists
        self.cursor.execute("SELECT EXISTS (SELECT 1 FROM entries WHERE id = ?)", (id,))     

        # if there is not entry found exit
        if(self.cursor.fetchone()[0] != 1):
            print("No Entry Found")
            return
        
        self.cursor.execute(
            "UPDATE entries SET site_name = ?, url = ?, username = ?, encrypted_password = ?, iv = ?, created_at = ?, modified_at = ?, notes = ?, favorite = ?, password_strength = ?, totp_secret = ? WHERE id = ?",
            (new_entry.site_name, new_entry.url, new_entry.username, new_entry.encrypted_password, new_entry.iv, new_entry.created_at, new_entry.modified_at, new_entry.notes, new_entry.favorite, new_entry.password_strength, new_entry.totp_secret, id)    
        )

        # commit changes to have the database save the changes
        self.connection.commit()

    # get entry
    def get_entry(self, id):
        # check if the entry exists
        self.cursor.execute("SELECT EXISTS (SELECT 1 FROM entries WHERE id = ?)", (id,))     

        # if there is not entry found exit
        if(self.cursor.fetchone()[0] != 1):
            print("No Entry Found")
            return
        
        self.cursor.execute(
            f"SELECT * FROM entries WHERE id=?", (id,)
        )

        # save the entry fetched from the database and save it in a variable 
        # return the row
        row = self.cursor.fetchone()
        return Entry.from_row(row)

    # search
    def search_for_entry(self, search):
        # select all entries where the site_name contains the search 
        self.cursor.execute(
            f"SELECT * FROM entries WHERE site_name LIKE ?", (search + "%",)
        )

        # store the results in a variable 
        results = self.cursor.fetchall()

        # append each result into a list of entries 
        entries = []
        for row in results:
            entries.append(Entry.from_row(row))

        # return the list of entires 
        return entries

    # delete all entries
    def delete_all_entries(self):
        # remove all entires 
        self.cursor.execute("DELETE FROM entries")

        # save the database state
        self.connection.commit()

    # get all entries 
    def get_all_entries(self):
        # select all entries from the database
        self.cursor.execute("SELECT * FROM entries")

        # save all entires into a variable
        entries = self.cursor.fetchall()

        # go through each element in entires and save it to a list of entries 
        all_entries = []
        for row in entries:
            all_entries.append(Entry.from_row(row))
        
        return all_entries