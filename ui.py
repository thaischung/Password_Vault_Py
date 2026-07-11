from textual.app import App, ComposeResult
from textual.widgets import Static, DataTable, Input, Button
from textual.containers import Vertical, Horizontal
from textual.app import RenderResult
from textual.widget import Widget
from textual.reactive import reactive
from textual.screen import Screen

from rich.text import Text
from rich.table import Table

from entry import Entry
from password_helper import PasswordHelper
from datetime import datetime
from vault_database import VaultDatabase

ROWS = [
        ("ID", "SITE", "MFA", "FAVORITE"),
        (1, "google.com", "●", "★"),
        (2, "school.com", "●", "★"),
        (3, "abc.com", "○", "☆"),
        (4, "math.com", "●", "☆"),
    ]
# header row
class HeaderRow(Static):
    # content need to update when data changes
    content = reactive("")

    def __init__(self, label_name: str, content: str):
        # call parent constructor register the widget with Textual
        super().__init__()
        # header label
        self.label_name = label_name
        # content
        self.content = content

    # render the widget and set the contents    
    def render(self) -> RenderResult:
        text = Text()
        text.append(self.label_name + "\n", style="#4a5a6a")
        text.append(str(self.content), style="#00b4d8")
        return text
    
    # update the content value
    def set_content(self, value):
        self.content = str(value)

# widget for the entries 
class VaultPanel(Widget):
    def compose(self) -> ComposeResult:
        yield DataTable(id="vault_table")

    def on_mount(self) -> None:
        self.border_title = "VAULT"
        table = self.query_one(DataTable)
        table.cursor_type = "row"
        table.add_column("ID", width=10)
        table.add_column("SITE", width=25)
        table.add_column("MFA", width=25)
        table.add_column("FAVORITE", width=10)

        table.expand = True

        table.add_rows(ROWS[1:])

# widget for displaying commands and prompting for input
class CommandPanel(Widget):
    def compose(self) -> ComposeResult:
        yield Static(id="command_table")

    def on_mount(self) -> None:
        self.border_title = "COMMANDS"
        table = Table(box=None, show_header=False)

        table.add_row("[^A] Add", "[^E] Edit", "[^D] Delete", "[^S] Search", "[^P] Copy Password", "[^M] Copy MFA", "[?] Help")
       
        self.query_one("#command_table", Static).update(table)

# popout pannel for extra commands/options
class HelpScreen(Screen):
    BINDINGS = [("escape", "app.pop_screen", "Close")]

    def compose(self) -> ComposeResult:
        yield Static("Available Commands")

# popout pannel to enter in details for a new entry
class AddEntryScreen(Screen):
    def __init__(self, vault_db, key, **kwargs):
        super().__init__(**kwargs)
        self.vault_db = vault_db
        self.key = key

    def compose(self) -> ComposeResult:
        with Vertical(id="add_entry_vertical"):
            yield Input(placeholder="Site Name", id="site_name")
            yield Input(placeholder="url", id="url_input")
            yield Input(placeholder="username", id="username")
            yield Input(placeholder="password", password=True, id="password_input")
            yield Input(placeholder="MFA secret (optional)", id="mfa_input")
            yield Input(placeholder="notes", id="notes_input")
            with Horizontal(id="button_row"):
                yield Button("Cancel", id="cancel")
                yield Button("Save", id="save")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel":
            self.app.pop_screen()
        elif event.button.id == "save":
            site = self.query_one("#site_name", Input).value
            url = self.query_one("#url_input", Input).value
            username = self.query_one("#username", Input).value
            password = self.query_one("#password_input", Input).value
            mfa = self.query_one("#mfa_input", Input).value or None
            notes = self.query_one("#notes_input", Input).value or None
            
            # pass to backend here
            password_tuple = PasswordHelper.encrypt(password, self.key)
            encrypted_password = password_tuple[0]
            password_iv = password_tuple[1]

            # check if mfa was enabled or not
            if mfa:
                mfa_tuple = PasswordHelper.encrypt(mfa, self.key)
                encrypted_mfa = mfa_tuple[0]
                mfa_iv = mfa_tuple[1]
            else:
                encrypted_mfa = None
                mfa_iv = None
            
            strength = PasswordHelper.password_strength(password)

            # create a new entry and fill it with the new data
            entry = Entry(None, site, url, username, encrypted_password, password_iv, datetime.now().isoformat(), datetime.now().isoformat(), notes, 0, strength, encrypted_mfa, mfa_iv)

            # add the new entry to the
            self.vault_db.add_entry(entry)
            
            # display 
            self.app.pop_screen()


# popout pannel to enter in details for a new entry
class EditEntryScreen(Screen):
    def __init__(self, vault_db, entry, key, **kwargs):
        super().__init__(**kwargs)
        self.vault_db = vault_db
        self.entry = entry
        self.key = key

    def compose(self) -> ComposeResult:
        with Vertical(id="add_entry_vertical"):
            yield Input(self.entry.site_name, placeholder="Site Name", id="site_name")
            yield Input(self.entry.url, placeholder="url", id="url_input")
            yield Input(self.entry.username, placeholder="username", id="username")
            yield Input(self.entry.encrypted_password, placeholder="password", password=True, id="password_input")
            yield Input(self.entry.totp_secret, placeholder="MFA secret (optional)", id="mfa_input")
            yield Input(self.entry.notes, placeholder="notes", id="notes_input")
            with Horizontal(id="button_row"):
                yield Button("Cancel", id="cancel")
                yield Button("Save", id="save")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel":
            self.app.pop_screen()
        elif event.button.id == "save":
            site = self.query_one("#site_name", Input).value
            url = self.query_one("#url_input", Input).value
            username = self.query_one("#username", Input).value
            password = self.query_one("#password_input", Input).value
            mfa = self.query_one("#mfa_input", Input).value or None
            notes = self.query_one("#notes_input", Input).value or None
            
            # pass to backend here
            password_tuple = PasswordHelper.encrypt(password, self.key)
            encrypted_password = password_tuple[0]
            password_iv = password_tuple[1]

            # check if mfa was enabled or not
            if mfa:
                mfa_tuple = PasswordHelper.encrypt(mfa, self.key)
                encrypted_mfa = mfa_tuple[0]
                mfa_iv = mfa_tuple[1]
            else:
                encrypted_mfa = None
                mfa_iv = None
            
            strength = PasswordHelper.password_strength(password)

            # create a new entry and fill it with the new data
            entry = Entry(self.entry.id, site, url, username, encrypted_password, password_iv, self.entry.created_at, datetime.now().isoformat(), notes, 0, strength, encrypted_mfa, mfa_iv)

            # add the new entry to the
            self.vault_db.modify_entry(self.entry.id, entry)
            
            # display 
            self.app.pop_screen()

# Entry panel widget
class EntryPanel(Widget):
    # get all remaining keyword arguments into a dictionary 
    def __init__(self, **kwargs):
        # call parent constructor bc Widget as a constructor that registers the widget with Textual
        super().__init__(**kwargs)
        self.entry = None
    
    def compose(self) -> ComposeResult:
        yield Static(id="selected_table")
    
    def on_mount(self) -> None:
        self.border_title = "ENTRY DETAILS"
        table = Table(box=None, show_header=False)

        table.add_column(style="#4a5a6a", justify="left")
        table.add_column(style="#00b4d8", justify="left")

        table.add_row("site", "site_name")
        table.add_row("url", "username")
        table.add_row("user", "username")
        table.add_row("pswd", "*********")
        table.add_row("mfa", "token")
        table.add_row("notes", "entry notes")
        
        self.query_one("#selected_table", Static).update(table)

    # set the entry that the user selects
    def set_entry(self, entry):
        self.entry = entry

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# main app to display all the different components 
class PasswordVault(App):
    CSS_PATH = "vault_layout.tcss"
    BINDINGS = [
        ("ctrl+a", "add_entry", "Add Entry"),
        ("ctrl+e", "edit_entry", "Edit Entry"),
        ("ctrl+d", "delete_entry", "Delete Entry"),
        ("ctrl+s", "search_entry", "Search Entry"),
        ("ctrl+p", "copy_password", "Copy Password"),
        ("ctrl+m", "copy_mfa", "Copy MFA"),
        ("?", "help", "Help"),
                ]
    SCREENS = {"help": HelpScreen}

    def __init__(self, vault_db, key, **kwargs):
        super().__init__(**kwargs)
        self.vault_db = vault_db
        self.key = key

    # action for add entry
    def action_add_entry(self):
        self.push_screen(AddEntryScreen(self.vault_db, self.key))

    # action for editing an entry
    def action_edit_entry(self):
        self.push_screen(EditEntryScreen(self.vault_db, selected_entry, self.key))


    def compose(self):
        # header row
        with Horizontal(id="header_horizontal"):
            yield HeaderRow("TOTAL ENTRIES", "0")
            yield HeaderRow("MFA ACTIVE", "0")
            yield HeaderRow("LAST LOGIN", "N/A")
        # vertically organize the vault and two lower screens 
        with Vertical():
            yield VaultPanel(id="vault", classes="box")
            # left box and right box within the vertical structure
            with Horizontal():
                yield CommandPanel(id="command_panel", classes="box")
                yield EntryPanel(id="entry_panel", classes="box")

