from rich import print as rprint
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from textual import events
from textual.app import App, ComposeResult
from textual.widgets import RichLog, Header, Static
from textual.containers import Vertical, Horizontal

class MyApp(App):
    CSS_PATH = "vault_layout.tcss"
    def compose(self):
        # header row
        yield Header()
        # vertically organize the vault and two lower screens 
        with Vertical():
            yield Static("Vault", id="vault", classes="box")
            # left box and right box within the vertical structure
            with Horizontal():
                yield Static("Command_Panel", id="command_panel", classes="box")
                yield Static("Entry_Panel", id="entry_panel", classes="box")

if __name__ == "__main__":
    app = MyApp()
    app.run()

'''
# make layout
layout = Layout(name="root")

# split the layout into the header, vault, and lower pannel
layout.split(
    Layout(name="header", ratio=1),
    Layout(name="vault_dashboard", ratio=4),
    Layout(name="lower_panel", ratio=3),
)
# split the lower pannel into two side by side pannels
layout["lower_panel"].split_row(
    Layout(name="command_panel"),
    Layout(name="entry_info"),
)

table = Table(box=None, show_header=False)

table.add_column("[KEY]", justify="left", style="#555555")
table.add_column("Action", justify="left", style="#555555")

table.add_row("^A", "Add Entry")
table.add_row("^M", "Modify Entry")
table.add_row("^D", "Delete Entry")
table.add_row("^S", "Search For Entry")
table.add_row("^U", "Copy Username")
table.add_row("^P", "Copy Password")
table.add_row("^T", "Copy TOTP")
table.add_row("^V", "View Entry Details")
table.add_row("^G", "Generate New Password")
table.add_row("^F", "Toggle Favorite")
table.add_row("^R", "Change Master Password")
table.add_row("^K", "Delete All Entries")
table.add_row("^Q", "Quit")

# command promt #00ff41
styled_command_panel = Panel(
    table,
    style="#000000",
    border_style="#3d3d3d"
)
layout["command_panel"].update(styled_command_panel)
'''