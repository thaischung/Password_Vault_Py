from textual.app import App, ComposeResult
from textual.widgets import Static, DataTable, Input, Button
from textual.containers import Vertical, Horizontal
from textual.app import RenderResult
from textual.widget import Widget
from textual.reactive import reactive
from textual.screen import Screen
from rich.text import Text
from rich.table import Table
from password_helper import PasswordHelper
from entry import Entry
import pyperclip
import os
from mfa import MFA

DUMMY_VAULT_DB = None
DUMMY_KEY = None

# display the header information
class HeaderRow(Static):
    content = reactive("")

    def __init__(self, label_name: str, content: str, **kwargs):
        super().__init__(**kwargs)
        self.label_name = label_name
        self.content = content

    def render(self) -> RenderResult:
        text = Text()
        text.append(self.label_name + "\n", style="#4a5a6a")
        text.append(str(self.content), style="#00b4d8")
        return text

    def set_content(self, content):
        self.content = content

# display all the entries
class VaultPanel(Widget):
    def __init__(self, vault_db, **kwargs):
        super().__init__(**kwargs)
        self.vault_db = vault_db

    def compose(self) -> ComposeResult:
        yield DataTable(id="vault_table", classes="box")

    def on_mount(self) -> None:
        # set panel title
        self.border_title = "VAULT"

        # finds a widget by type or css selector and allows you to call methods on it
        table = self.query_one(DataTable)

        # set the cursor to select the row rather than the column
        table.cursor_type = "row"

        # set up the columns 
        table.add_column("ID", width=10)
        table.add_column("SITE", width=25)
        table.add_column("MFA", width=25)
        table.add_column("FAVORITE", width=10)
        table.expand = True

        # if the ebale is not empty fill in the rows
        if self.vault_db is not None:
            # get all the entries from the database
            entries = self.vault_db.get_all_entries()
            # for each entry get the elements we want to display
            for entry in entries:
                # tenary operator do this if this condition else do this
                mfa = "●" if entry.totp_secret else "○"
                favorite = "★" if entry.favorite else "☆"
                table.add_row(entry.id, entry.site_name, mfa, favorite)

    def refresh_table(self):
        table = self.query_one("#vault_table", DataTable)
        table.clear()
        if self.vault_db is not None:
            entries = self.vault_db.get_all_entries()
            for entry in entries:
                mfa = "●" if entry.totp_secret else "○"
                favorite = "★" if entry.favorite else "☆"
                table.add_row(entry.id, entry.site_name, mfa, favorite)
    
# display the different commands that the user has access to
class CommandPanel(Widget):
    def compose(self) -> ComposeResult:
        yield Static(id="command_table")

    def on_mount(self) -> None:
        self.border_title = "COMMANDS"
        table = Table(box=None, show_header=False)
        table.add_row("[^A] Add", "[^E] Edit", "[^D] Delete", "[^S] Search", "[^Y] Copy Pass", "[^T] Copy MFA", "[?] Help")
        self.query_one("#command_table", Static).update(table)

# add a new entry to the vault
class AddEntryScreen(Screen):
    # commands to save or cancel the action
    BINDINGS = [
        ("escape", "app.pop_screen", "Cancel"),
        ("ctrl+s", "save", "Save"),
    ]

    def __init__(self, vault_db, key, entry=None, **kwargs):
        super().__init__(**kwargs)
        self.vault_db = vault_db
        self.key = key
        self.selected_entry = entry

    # display two different screens depending if there is a selected entry or not
    # if there is a selected entry then enter edit mode else enter add new entry mode
    def compose(self) -> ComposeResult:
        # title/subtitle 
        title = "EDIT VAULT ENTRY" if self.selected_entry else "ADD VAULT ENTRY"
        subtitle = "Edit an encrypted credential" if self.selected_entry else "Create a new encrypted credential"

        # layout 
        with Vertical(id="add_entry_vertical"):
            yield Static(title, id="add_form_title")
            yield Static(f"[#4a5a6a]{subtitle}[/#4a5a6a]", id="add_form_subtitle")
            yield Input(value=self.selected_entry.site_name if self.selected_entry else "", placeholder="Site", id="site_name")
            yield Input(value=self.selected_entry.url if self.selected_entry else "", placeholder="URL — https://example.com", id="url_input")
            yield Input(value=self.selected_entry.username if self.selected_entry else "", placeholder="Username", id="username")
            with Horizontal(id="password_row"):
                yield Input(placeholder="Password", password=True, id="password_input")
                yield Button("Show", id="toggle_password")
                yield Button("Generate", id="generate_password")
            yield Input(placeholder="MFA secret (optional)", id="mfa_input")
            yield Input(value=self.selected_entry.notes if self.selected_entry else "", placeholder="Notes", id="notes_input")
            yield Static("[#4a5a6a]AES-256-CBC  ◆  PBKDF2-HMAC-SHA256  ◆  Local Only[/#4a5a6a]", id="security_footer")
            with Horizontal(id="button_row"):
                yield Button("Cancel", id="cancel")
                yield Button("Save", id="save", variant="primary")

    # logic for when the user hits save
    def action_save(self):
        # encrypt password
        password = self.query_one("#password_input", Input).value
        if password:
            password_strength = PasswordHelper.password_strength(password)
            encrypted_password, iv = PasswordHelper.encrypt(password, self.key)
            
        elif self.selected_entry:
            encrypted_password = self.selected_entry.encrypted_password
            iv = self.selected_entry.iv
            password_strength = self.selected_entry.password_strength
        else:
            self.notify("Password is required", severity="warning")
            return

        # encrypt the totp if there is one
        totp = self.query_one("#mfa_input", Input).value
        if totp:
            encrypted_totp, totp_iv = PasswordHelper.encrypt(totp, self.key)
        else:
            encrypted_totp = self.selected_entry.totp_secret if self.selected_entry else None
            totp_iv = self.selected_entry.totp_iv if self.selected_entry else None

        site = self.query_one("#site_name", Input).value
        url = self.query_one("#url_input", Input).value
        username = self.query_one("#username", Input).value
        notes = self.query_one("#notes_input", Input).value
        current_time = self.vault_db.get_now()

        if self.selected_entry: 
            entry = Entry(self.selected_entry.id, site, url, username, encrypted_password, iv, self.selected_entry.created_at, current_time, notes, self.selected_entry.favorite, password_strength, encrypted_totp, totp_iv)
            self.vault_db.modify_entry(self.selected_entry.id, entry)
        else:
            entry = Entry(None, site, url, username, encrypted_password, iv, current_time, current_time, notes, 0, password_strength, encrypted_totp, totp_iv)
            self.vault_db.add_entry(entry)
        
        # close this screen and notify the parent screen
        # this triggers the callback passed into push_screen()
        # dismiss() return a result to the parent screen and exectutes the callback
        # unlike pop_screen(), which only removes the screen
        self.dismiss(True)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel":
            # close screen without saving
            self.dismiss(False)
        elif event.button.id == "save":
            self.action_save()
        elif event.button.id == "toggle_password":
            pw = self.query_one("#password_input", Input)
            pw.password = not pw.password
        elif event.button.id == "generate_password":
            pw = PasswordHelper.generate_password()
            self.query_one("#password_input", Input).value = pw

#------------------------------------------------------------------------------
class ConfirmationScreen(Screen):
    BINDINGS = [
        ("escape", "app.pop_screen", "Cancel"),
        ("ctrl+s", "save", "Save"),
    ]

    def __init__(self, message, callback, user_db, **kwargs):
        super().__init__(**kwargs)
        self.message = message
        self.callback = callback
        self.user_db = user_db

    def compose(self) -> ComposeResult:
        with Vertical(id="confirmation_vertical"):
            yield Static(f"[#e05252]{self.message}[/#e05252]", id="confirmation_message")
            yield Static("[#4a5a6a]Enter your master password to confirm[/#4a5a6a]", id="confirmation_subtitle")
            yield Input(placeholder="Master password", password=True, id="confirmation_input")
            with Horizontal(id="confirmation_buttons"):
                yield Button("Cancel", id="cancel")
                yield Button("Confirm", id="confirm", variant="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel":
            self.app.pop_screen()
        elif event.button.id == "confirm":
            password = self.query_one("#confirmation_input", Input).value
            if self.callback:
                self.callback(password)
            self.app.pop_screen()

#------------------------------------------------------------------------------
class SearchScreen(Screen):
    BINDINGS = [
        ("escape", "app.pop_screen", "Close"),
        ("ctrl+s", "save", "Save"),
    ]

    def __init__(self, vault_db, **kwargs):
        super().__init__(**kwargs)
        self.vault_db = vault_db

    def compose(self) -> ComposeResult:
        with Vertical(id="search_vertical"):
            yield Static("SEARCH VAULT", id="search_title")
            yield Static("[#4a5a6a]Search by site name[/#4a5a6a]", id="search_subtitle")
            yield Input(placeholder="Type to search...", id="search_input")
            yield DataTable(id="search_results")
            with Horizontal(id="search_button_row"):
                yield Button("Close", id="close")

    def on_mount(self) -> None:
        table = self.query_one("#search_results", DataTable)
        table.cursor_type = "row"
        table.add_column("ID", width=10)
        table.add_column("SITE", width=25)
        table.add_column("MFA", width=25)
        table.add_column("FAVORITE", width=10)

        table.expand = True

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "search_input":
            self.filter_results(event.value)

    def filter_results(self, query: str) -> None:
        table = self.query_one("#search_results", DataTable)
        table.clear()
        if self.vault_db is not None:
            results = self.vault_db.search_for_entry(query)
            for entry in results:
                mfa = "●" if entry.totp_secret else "○"
                favorite = "★" if entry.favorite else "☆"                
                table.add_row(entry.id, entry.site_name, mfa, favorite)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "close":
            self.app.pop_screen()

#------------------------------------------------------------------------------
class ChangeMasterPasswordScreen(Screen):
    BINDINGS = [("escape", "app.pop_screen", "Cancel"),
                ("ctrl+s", "save", "Save"),]

    def __init__(self, vault_db, user_db, key, **kwargs):
        super().__init__(**kwargs)
        self.vault_db = vault_db
        self.user_db = user_db
        self.key = key

    def compose(self) -> ComposeResult:
        with Vertical(id="change_password_vertical"):
            yield Static("CHANGE MASTER PASSWORD", id="change_pw_title")
            yield Static("[#4a5a6a]Enter your current password to continue[/#4a5a6a]", id="change_pw_subtitle")
            yield Input(placeholder="Current password", password=True, id="current_password")
            yield Input(placeholder="New password", password=True, id="new_password")
            yield Input(placeholder="Confirm new password", password=True, id="confirm_password")
            yield Static("[#4a5a6a]AES-256-CBC  ◆  PBKDF2-HMAC-SHA256  ◆  Local Only[/#4a5a6a]", id="change_pw_footer")
            with Horizontal(id="change_pw_buttons"):
                yield Button("Cancel", id="cancel")
                yield Button("Change Password", id="save", variant="primary")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel":
            self.app.pop_screen()
        # if the user tries to update the password
        elif event.button.id == "save":
            # get the old password
            old_pw = self.query_one("#current_password", Input).value
            new_hashed_pw = PasswordHelper.sha256_hash_util(old_pw, self.user_db.get_salt())
            # if the old password matches what is on record 
            if self.user_db.verify_password(new_hashed_pw):
                # get the new password and the re-typed password
                new_pw = self.query_one("#new_password", Input).value
                conf_pw = self.query_one("#confirm_password", Input).value

                # if the new passwords match
                if new_pw == conf_pw:
                    # since we are updating the user password
                    # we need to generate a new salt
                    new_salt = os.urandom(16)

                    # since the salt is new derive a new key to be used to encrypt the entries passwords
                    new_derived_key = PasswordHelper.derive_key(new_pw.encode(), new_salt)

                    # get all entries
                    entries = self.vault_db.get_all_entries()

                    # decrypt all the entry passwords with the old key
                    # re-encrypt each of the entry passwords with the new key
                    for entry in entries:
                        decrypted_password = PasswordHelper.decrypt(entry.encrypted_password, self.key, entry.iv)
                        re_encrypted_password, new_iv = PasswordHelper.encrypt(decrypted_password.decode(), new_derived_key)

                        if entry.totp_secret:
                            decrypted_mfa = PasswordHelper.decrypt(entry.totp_secret, self.key, entry.totp_iv)
                            re_encrypted_mfa, new_mfa_iv = PasswordHelper.encrypt(decrypted_mfa.decode(), new_derived_key)
                        else:
                            re_encrypted_mfa = None
                            new_mfa_iv = None

                        entry = Entry(entry.id, entry.site_name, entry.url, entry.username, re_encrypted_password, new_iv, entry.created_at, self.vault_db.get_now(), entry.notes, entry.favorite, entry.password_strength, re_encrypted_mfa, new_mfa_iv)

                        self.vault_db.modify_entry(entry.id, entry)
                    hashed_new_password = PasswordHelper.sha256_hash_util(new_pw, new_salt)
                    self.user_db.change_password(hashed_new_password)
                    self.user_db.update_salt(new_salt)

                    # get the instance of PasswordVault and update the value of the key for subsequent decryption/encryption
                    self.app.key = new_derived_key

                    self.notify("Password changed successfully")
                    self.app.pop_screen()

                # if they don't match display a warning
                else:
                    self.notify("Passwords do not match", severity="warning")                


#------------------------------------------------------------------------------
class HelpScreen(Screen):
    BINDINGS = [("escape", "app.pop_screen", "Close")]

    def on_mount(self):
        self.query_one("#help_commands", Static).focus()

    def compose(self) -> ComposeResult:
        with Vertical(id="help_vertical"):
            yield Static("AVAILABLE COMMANDS", id="help_title")
            yield Static("[#4a5a6a]Keyboard shortcuts[/#4a5a6a]", id="help_subtitle")
            yield Static(
                "[#00b4d8]^A[/#00b4d8]  [#4a5a6a]Add Entry[/#4a5a6a]\n"
                "[#00b4d8]^E[/#00b4d8]  [#4a5a6a]Edit Entry[/#4a5a6a]\n"
                "[#00b4d8]^D[/#00b4d8]  [#4a5a6a]Delete Entry[/#4a5a6a]\n"
                "[#00b4d8]^S[/#00b4d8]  [#4a5a6a]Search[/#4a5a6a]\n"
                "[#00b4d8]^Y[/#00b4d8]  [#4a5a6a]Copy Password[/#4a5a6a]\n"
                "[#00b4d8]^U[/#00b4d8]  [#4a5a6a]Copy Username[/#4a5a6a]\n"
                "[#00b4d8]^T[/#00b4d8]  [#4a5a6a]Copy MFA Code[/#4a5a6a]\n"
                "[#00b4d8]^F[/#00b4d8]  [#4a5a6a]Toggle Favorite[/#4a5a6a]\n"
                "[#00b4d8]^C[/#00b4d8]  [#4a5a6a]Change Master Password[/#4a5a6a]\n"
                "[#00b4d8]^K[/#00b4d8]  [#4a5a6a]Delete All Entries[/#4a5a6a]\n"
                "[#00b4d8]?[/#00b4d8]   [#4a5a6a]This help screen[/#4a5a6a]\n"
                "[#00b4d8]ESC[/#00b4d8] [#4a5a6a]Close / Cancel[/#4a5a6a]",
                id="help_commands"
            )
            yield Button("Close", id="close")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "close":
            self.app.pop_screen()

#------------------------------------------------------------------------------
class EntryPanel(Widget):
    def __init__(self, key, **kwargs):
        super().__init__(**kwargs)
        self.entry = None
        self.key = key

    def compose(self) -> ComposeResult:
        yield Static(id="selected_table", classes="box")

    def on_mount(self) -> None:
        self.border_title = "ENTRY DETAILS"
        table = Table(box=None, show_header=False)
        table.add_column(style="#4a5a6a", justify="left")
        table.add_column(style="#00b4d8", justify="left")
        table.add_row("site", "—")
        table.add_row("url", "—")
        table.add_row("user", "—")
        table.add_row("pswd", "—")
        table.add_row("mfa", "—")
        table.add_row("notes", "—")
        self.query_one("#selected_table", Static).update(table)

#------------------------------------------------------------------------------
# main application to hold all widgets
class PasswordVault(App):
    # tcss file (styling file)
    CSS_PATH = "vault_layout.tcss"
    
    # list of commands (key commands)
    BINDINGS = [
        ("ctrl+a", "add_entry", "Add Entry"),
        ("ctrl+e", "edit_entry", "Edit Entry"),
        ("ctrl+d", "delete_entry", "Delete Entry"),
        ("ctrl+s", "search", "Search"),
        ("ctrl+y", "copy_password", "Copy Password"),
        ("ctrl+u", "copy_username", "Copy Username"),
        ("ctrl+t", "copy_mfa", "Copy MFA"),
        ("ctrl+f", "toggle_favorite", "Toggle Favorite"),
        ("ctrl+c", "change_password", "Change Password"),
        ("ctrl+k", "delete_all", "Delete All"),
        ("?", "push_screen('help')", "Help"),
    ]

    # help screen for extra commandsm
    SCREENS = {"help": HelpScreen}

    # constructor for the appliction, passes the vault database, user database
    # **kwargs takes the extra arguments that Textual might pass (id, classes, name)
    def __init__(self, vault_db, key, user_db, **kwargs):
        # registers the widget with textual
        super().__init__(**kwargs)
        self.vault_db = vault_db
        self.key = key
        self.user_db = user_db
        self.selected_entry = None

    # when the user uses the key command to add an entry
    # when the add entry screen closes refresh the vault table and header row
    def action_add_entry(self):
        self.push_screen(
            AddEntryScreen(self.vault_db, self.key),
            # pass the function for AddEntryScreen to use
            callback=self._entry_screen_closed
        )

    # when the user uses the key command to edit an entry
    # when the edit screen closes, refresh the vault table and header row
    def action_edit_entry(self):
        if self.selected_entry is None:
            self.notify("Select an entry first", severity="warning")
        else:
            self.push_screen(
                AddEntryScreen(self.vault_db, self.key, entry=self.selected_entry),
                # pass the function
                callback=self._entry_screen_closed
            )

    # refresh the vault table and header when the add/edit screen closes
    def _entry_screen_closed(self, result=None):
        # refresh the header row with new values
        self._refresh_header()
        # refresh the vault table with the new vault table
        self.query_one("#vault", VaultPanel).refresh_table()

    # when the user uses the key command to delete an entry
    def action_delete_entry(self):
        if self.selected_entry is None:
            self.notify("Select an entry first", severity="warning")
        else:
            self.push_screen(ConfirmationScreen(
                "This will permanently delete this entry.",
                self._confirm_del_entry,
                self.user_db
            ))

    def _confirm_del_entry(self, password):
        salt = self.user_db.get_salt()
        hashed_password = PasswordHelper.sha256_hash_util(password, salt)
    
        if self.user_db.verify_password(hashed_password):
            self.vault_db.remove_entry(self.selected_entry.id)
        else:
            self.notify("Invalid Password", severity="warning")
        self.selected_entry = None
        self._refresh_header()

    # when the user uses the key command to search for an entry
    def action_search(self):
        self.push_screen(SearchScreen(self.vault_db))

    # when the user uses the key command to copy a password
    def action_copy_password(self):
        if self.selected_entry is None:
            self.notify("Select an entry first", severity="warning")
        else:
            decrypted_password = PasswordHelper.decrypt(self.selected_entry.encrypted_password, self.key, self.selected_entry.iv)
            pyperclip.copy(decrypted_password.decode())
            self.notify("Password copied to clipboard", severity="information")

    # when the user uses the key command to copy a username
    def action_copy_username(self):
        if self.selected_entry is None:
            self.notify("Select an entry first", severity="warning")
        else:
            pyperclip.copy(self.selected_entry.username)
            self.notify("Username copied to clipboard", severity="information")

    # when the user uses the key command to copy a MFA
    def action_copy_mfa(self):
        if self.selected_entry is None:
            self.notify("Select an entry first", severity="warning")
        else:
            if self.selected_entry.totp_secret:
                decrypted_mfa = PasswordHelper.decrypt(self.selected_entry.totp_secret, self.key, self.selected_entry.totp_iv)
                pyperclip.copy(MFA.get_code(decrypted_mfa.decode()))
                self.notify("MFA code copied to clipboard", severity="information")
            else:
                self.notify(f"MFA not enabled for entry with id:{self.selected_entry.id}", severity="warning")
                return

    # when the user uses the key command to toggle favorite
    def action_toggle_favorite(self):
        if self.selected_entry is None:
            self.notify("Select an entry first", severity="warning")
        else:
            new_favorite = 0 if self.selected_entry.favorite else 1
            self.vault_db.toggle_favorite(new_favorite, self.selected_entry.id)
            self.selected_entry.favorite = new_favorite

    # when the user uses the key command to change the user's password
    def action_change_password(self):
        self.push_screen(ChangeMasterPasswordScreen(self.vault_db, self.user_db, self.key))

    # when the user uses the key command to delete all entries
    def action_delete_all(self):
        self.push_screen(ConfirmationScreen(
            "This will permanently delete ALL entries.",
            self._confirm_del_all,
            self.user_db
        ))
       
    def _confirm_del_all(self, password):
        salt = self.user_db.get_salt()
        hashed_password = PasswordHelper.sha256_hash_util(password, salt)

        if self.user_db.verify_password(hashed_password):
            self.vault_db.delete_all_entries()
        else:
            self.notify("Invalid Password", severity="warning")
        self.selected_entry = None
        self._refresh_header()

    # get the row that the user "selects" clicks on
    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        # get the key of the selected row
        row_key = event.row_key
        
        # get the raw data from the selected row as a list
        row_data = self.query_one("#vault_table", DataTable).get_row(row_key)

        # get the id by selecting the first element of the row
        entry_id = row_data[0]

        # set the selected entry to the vault database entry with the corresponding id
        self.selected_entry = self.vault_db.get_entry(entry_id)

    def _refresh_header(self):
        if self.vault_db:
            self.query_one("#total_entries", HeaderRow).set_content(str(self.vault_db.count()))
            self.query_one("#total_mfa", HeaderRow).set_content(str(self.vault_db.count_mfa()))

    def on_screen_resume(self):
        self._refresh_header()
        self.query_one("#vault", VaultPanel).refresh_table()
                
    # display them all to the terminal 
    def compose(self):
        with Horizontal(id="header_horizontal"):
            yield HeaderRow("TOTAL ENTRIES", "0", id="total_entries")
            yield HeaderRow("MFA ACTIVE", "0", id="total_mfa")
            yield HeaderRow("LAST LOGIN", "N/A", id="last_logon")
        with Vertical(id="app_vertical"):
            yield VaultPanel(self.vault_db, id="vault", classes="box")
            with Horizontal():
                yield CommandPanel(id="command_panel", classes="box")
                yield EntryPanel(self.key, id="entry_panel", classes="box")

    def on_mount(self):
        if self.vault_db:
            total_entries = self.vault_db.count()
            total_mfa = self.vault_db.count_mfa()

            self.query_one("#total_entries", HeaderRow).set_content(str(total_entries))
            self.query_one("#total_mfa", HeaderRow).set_content(str(total_mfa))
        
        if self.user_db:
            last_logon = self.user_db.get_last_logon()
            self.query_one("#last_logon", HeaderRow).set_content(str(last_logon))
