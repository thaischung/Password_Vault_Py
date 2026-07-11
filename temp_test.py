from textual.app import App, ComposeResult
from textual.widgets import Static, DataTable, Input, Button
from textual.containers import Vertical, Horizontal
from textual.app import RenderResult
from textual.widget import Widget
from textual.reactive import reactive
from textual.screen import Screen
from rich.text import Text
from rich.table import Table

ROWS = [
    ("ID", "SITE", "MFA", "FAVORITE"),
    (1, "google.com", "●", "★"),
    (2, "school.com", "●", "★"),
    (3, "abc.com", "○", "☆"),
    (4, "math.com", "●", "☆"),
]

DUMMY_VAULT_DB = None
DUMMY_KEY = None

#------------------------------------------------------------------------------
class HeaderRow(Static):
    content = reactive("")

    def __init__(self, label_name: str, content: str):
        super().__init__()
        self.label_name = label_name
        self.content = content

    def render(self) -> RenderResult:
        text = Text()
        text.append(self.label_name + "\n", style="#4a5a6a")
        text.append(str(self.content), style="#00b4d8")
        return text

#------------------------------------------------------------------------------
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

#------------------------------------------------------------------------------
class CommandPanel(Widget):
    def compose(self) -> ComposeResult:
        yield Static(id="command_table")

    def on_mount(self) -> None:
        self.border_title = "COMMANDS"
        table = Table(box=None, show_header=False)
        table.add_row("[^A] Add", "[^E] Edit", "[^D] Delete", "[^S] Search", "[^Y] Copy Pass", "[^M] Copy MFA", "[?] Help")
        self.query_one("#command_table", Static).update(table)

#------------------------------------------------------------------------------
class AddEntryScreen(Screen):
    BINDINGS = [
        ("escape", "app.pop_screen", "Cancel"),
        ("ctrl+s", "save", "Save"),
    ]

    def __init__(self, vault_db, key, entry=None, **kwargs):
        super().__init__(**kwargs)
        self.vault_db = vault_db
        self.key = key
        self.entry = entry

    def compose(self) -> ComposeResult:
        title = "EDIT VAULT ENTRY" if self.entry else "ADD VAULT ENTRY"
        subtitle = "Edit an encrypted credential" if self.entry else "Create a new encrypted credential"
        with Vertical(id="add_entry_vertical"):
            yield Static(title, id="add_form_title")
            yield Static(f"[#4a5a6a]{subtitle}[/#4a5a6a]", id="add_form_subtitle")
            yield Input(value=self.entry.site_name if self.entry else "", placeholder="Site", id="site_name")
            yield Input(value=self.entry.url if self.entry else "", placeholder="URL — https://example.com", id="url_input")
            yield Input(value=self.entry.username if self.entry else "", placeholder="Username", id="username")
            with Horizontal(id="password_row"):
                yield Input(placeholder="Password", password=True, id="password_input")
                yield Button("Show", id="toggle_password")
                yield Button("Generate", id="generate_password")
            yield Input(value=self.entry.totp_secret if self.entry else "", placeholder="MFA secret (optional)", id="mfa_input")
            yield Input(value=self.entry.notes if self.entry else "", placeholder="Notes", id="notes_input")
            yield Static("[#4a5a6a]AES-256-CBC  ◆  PBKDF2-HMAC-SHA256  ◆  Local Only[/#4a5a6a]", id="security_footer")
            with Horizontal(id="button_row"):
                yield Button("Cancel", id="cancel")
                yield Button("Save", id="save", variant="primary")

    def action_save(self):
        self.app.pop_screen()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel":
            self.app.pop_screen()
        elif event.button.id == "save":
            self.app.pop_screen()
        elif event.button.id == "toggle_password":
            pw = self.query_one("#password_input", Input)
            pw.password = not pw.password
        elif event.button.id == "generate_password":
            from password_helper import PasswordHelper
            pw = PasswordHelper.generate_password()
            self.query_one("#password_input", Input).value = pw

#------------------------------------------------------------------------------
class ConfirmationScreen(Screen):
    BINDINGS = [
        ("escape", "app.pop_screen", "Cancel"),
    ]

    def __init__(self, message, callback, **kwargs):
        super().__init__(**kwargs)
        self.message = message
        self.callback = callback

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
    BINDINGS = [("escape", "app.pop_screen", "Close")]

    def __init__(self, vault_db, key, **kwargs):
        super().__init__(**kwargs)
        self.vault_db = vault_db
        self.key = key

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
        table.add_column("SITE", width=40)
        table.add_column("MFA", width=10)
        table.expand = True

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "search_input":
            self.filter_results(event.value)

    def filter_results(self, query: str) -> None:
        table = self.query_one("#search_results", DataTable)
        table.clear()
        # will use vault_db.search_for_entry(query) when backend is wired
        for row in ROWS[1:]:
            if query.lower() in str(row[1]).lower():
                table.add_row(*row)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "close":
            self.app.pop_screen()

#------------------------------------------------------------------------------
class ChangeMasterPasswordScreen(Screen):
    BINDINGS = [("escape", "app.pop_screen", "Cancel")]

    def __init__(self, user_db, key, **kwargs):
        super().__init__(**kwargs)
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
        elif event.button.id == "save":
            self.app.pop_screen()

#------------------------------------------------------------------------------
class HelpScreen(Screen):
    BINDINGS = [("escape", "app.pop_screen", "Close")]

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
                "[#00b4d8]^M[/#00b4d8]  [#4a5a6a]Copy MFA Code[/#4a5a6a]\n"
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
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.entry = None

    def compose(self) -> ComposeResult:
        yield Static(id="selected_table")

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
class PasswordVault(App):
    CSS_PATH = "vault_layout.tcss"
    BINDINGS = [
        ("ctrl+a", "add_entry", "Add Entry"),
        ("ctrl+e", "edit_entry", "Edit Entry"),
        ("ctrl+d", "delete_entry", "Delete Entry"),
        ("ctrl+s", "search", "Search"),
        ("ctrl+y", "copy_password", "Copy Password"),
        ("ctrl+u", "copy_username", "Copy Username"),
        ("ctrl+m", "copy_mfa", "Copy MFA"),
        ("ctrl+f", "toggle_favorite", "Toggle Favorite"),
        ("ctrl+c", "change_password", "Change Password"),
        ("ctrl+k", "delete_all", "Delete All"),
        ("?", "push_screen('help')", "Help"),
    ]
    SCREENS = {"help": HelpScreen}

    def __init__(self, vault_db, key, **kwargs):
        super().__init__(**kwargs)
        self.vault_db = vault_db
        self.key = key
        self.selected_entry = None

    def action_add_entry(self):
        self.push_screen(AddEntryScreen(self.vault_db, self.key))

    def action_edit_entry(self):
        if self.selected_entry is None:
            self.notify("Select an entry first", severity="warning")
        else:
            self.push_screen(AddEntryScreen(self.vault_db, self.key, entry=self.selected_entry))

    def action_delete_entry(self):
        if self.selected_entry is None:
            self.notify("Select an entry first", severity="warning")
        else:
            self.push_screen(ConfirmationScreen(
                "This will permanently delete this entry.",
                lambda pw: None  # wire vault_db.remove_entry later
            ))

    def action_search(self):
        self.push_screen(SearchScreen(self.vault_db, self.key))

    def action_copy_password(self):
        if self.selected_entry is None:
            self.notify("Select an entry first", severity="warning")
        else:
            self.notify("Password copied to clipboard", severity="information")

    def action_copy_username(self):
        if self.selected_entry is None:
            self.notify("Select an entry first", severity="warning")
        else:
            self.notify("Username copied to clipboard", severity="information")

    def action_copy_mfa(self):
        if self.selected_entry is None:
            self.notify("Select an entry first", severity="warning")
        else:
            self.notify("MFA code copied to clipboard", severity="information")

    def action_toggle_favorite(self):
        if self.selected_entry is None:
            self.notify("Select an entry first", severity="warning")
        else:
            self.notify("Favorite toggled", severity="information")

    def action_change_password(self):
        self.push_screen(ChangeMasterPasswordScreen(None, self.key))

    def action_delete_all(self):
        self.push_screen(ConfirmationScreen(
            "This will permanently delete ALL entries.",
            lambda pw: None  # wire vault_db.delete_all_entries later
        ))

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        row_key = event.row_key
        row_data = self.query_one(DataTable).get_row(row_key)
        self.selected_entry = row_data

    def compose(self):
        with Horizontal(id="header_horizontal"):
            yield HeaderRow("TOTAL ENTRIES", "4")
            yield HeaderRow("MFA ACTIVE", "3")
            yield HeaderRow("LAST LOGIN", "today 09:41")
        with Vertical(id="app_vertical"):
            yield VaultPanel(id="vault", classes="box")
            with Horizontal():
                yield CommandPanel(id="command_panel", classes="box")
                yield EntryPanel(id="entry_panel", classes="box")

#------------------------------------------------------------------------------
if __name__ == "__main__":
    app = PasswordVault(DUMMY_VAULT_DB, DUMMY_KEY)
    app.run()