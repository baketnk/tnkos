# app.py

from textual.app import App
from textual.widgets import Header, Footer
from tnkos.shell_widget import ShellWidget
from textual import log
from textual.binding import Binding
class ShellApp(App):
    """A Textual app for a LLM-enhanced shell wrapper with syntax highlighting."""

    CSS = """
    ShellWidget {
        height: 100%;
    }
    """

    BINDINGS = [
        ("ctrl+d", "quit", "Quit"),
        Binding("ctrl+e", "explain_command", "Explain Command", priority=True)
    ]


    def compose(self):
        yield ShellWidget()
        yield Footer()

    def on_mount(self):
        self.query_one(ShellWidget).focus()

    def action_explain_command(self):
        """Trigger command explanation in ShellWidget."""
        log.debug("app triggered exlain")
        self.query_one(ShellWidget).action_explain_command()


if __name__ == "__main__":
    app = ShellApp()
    app.run()
