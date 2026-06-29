class Entry:
    def __init__(self, id, site_name, url, username, encrypted_password, iv, created_at, modified_at, notes, favorite, password_strength, totp_secret=None):
        self.id = id
        self.site_name = site_name
        self.url = url
        self.username = username
        self.encrypted_password = encrypted_password
        self.iv = iv
        self.totp_secret = totp_secret
        self.created_at = created_at
        self.modified_at = modified_at
        self.notes = notes
        self.favorite = favorite
        self.password_strength = password_strength

    def to_dict(self):
        entry = {"id" : self.id, "site_name" : self.site_name, "url" : self.url, "username" : self.username, "encrypted_password" : self.encrypted_password, "iv" : self.iv, "totp_secret" : self.totp_secret, "created_at" : self.created_at, "modified_at" : self.modified_at, "notes" : self.notes, "favorite" : self.favorite, "password_strength" : self.password_strength}
        return entry
    
    # class method belongs to the class, needed when we need to create an object
    @classmethod
    def from_dict(cls, entry_data):
        return cls(entry_data["id"], entry_data["site_name"], entry_data["url"], entry_data["username"], entry_data["encrypted_password"], entry_data["iv"], entry_data["created_at"], entry_data["modified_at"], entry_data["notes"], entry_data["favorite"], entry_data["password_strength"], entry_data["totp_secret"])
    
    # return a list of tuples 
    @classmethod
    def from_row(cls, row):
        id, site_name, url, username, encrypted_password, iv, created_at, modified_at, notes, favorite, password_strength, totp_secret = row
        return cls(id, site_name, url, username, encrypted_password, iv, created_at, modified_at, notes, favorite, password_strength, totp_secret)
    

    