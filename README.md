Password Vault

A local CLI password manager and TOTP authenticator built in Python. All data is stored and encrypted locally — nothing is sent online.

Built with AES-256-CBC encryption, PBKDF2-HMAC-SHA256 key derivation, and a hand-rolled TOTP engine verified against Google Authenticator.

**Features**
AES-256-CBC encrypted vault entries
PBKDF2-HMAC-SHA256 master key derivation
TOTP / MFA code generation
Challenge-response authentication
Lockout after 5 failed login attempts
Copy password, username, and MFA codes to clipboard
Search, add, edit, delete, and favorite entries
Change master password with full re-encryption of all entries
Terminal UI built with Textual

**Requirements**
Python 3.10 or higher
pip
Git

**Setup — Linux (Ubuntu/Debian)**
1. Clone the repository
bash
git clone https://github.com/thaischung/PasswordVault.git
cd PasswordVault

2. Make the setup script executable and run it
bash
chmod +x setup.sh
./setup.sh

This will:
Create a Python virtual environment
Install all dependencies (textual, pycryptodome, pyperclip, rich)
Detect X11 or Wayland and install the correct clipboard support automatically

3. Make the run script executable
bash
chmod +x run.sh

4. Launch the app
bash
./run.sh

**Setup — macOS**
1. Clone the repository
bash
git clone https://github.com/thaischung/PasswordVault.git
cd PasswordVault

2. Make the setup script executable and run it
bash
chmod +x mac_setup.sh
./mac_setup.sh

3. Make the run script executable
bash
chmod +x run.sh

4. Launch the app
bash
./run.sh

macOS has native clipboard support — no additional clipboard install needed.

**First Run**
On first launch you will be prompted to create:

A username
A master password — used to derive the encryption key, never stored in plaintext
A challenge question and response — used to verify your identity before the password prompt


After setup you will be taken directly to the vault.

**Keyboard Shortcuts**
Key	Action
Ctrl+A	Add entry
Ctrl+E	Edit entry
Ctrl+D	Delete entry
Ctrl+S	Search
Ctrl+Y	Copy password
Ctrl+U	Copy username
Ctrl+T	Copy MFA code
Ctrl+F	Toggle favorite
Ctrl+C	Change master password
Ctrl+K	Delete all entries
?	Help screen
ESC	Close / Cancel

**Security**
All vault entries are encrypted with AES-256-CBC
Master key is derived using PBKDF2-HMAC-SHA256 with 10,000 iterations
Passwords are salted and hashed using SHA-256
IV is stored per-entry
Vault locks for 24 hours after 5 failed login attempts
Changing master password re-encrypts all entries with a new key and salt
No data leaves your machine

**Notes**
'vault.db and auth.db are created automatically on first run and stored locally
These files are excluded from version control via .gitignore
Compatible with Linux (X11 and Wayland) and macOS
