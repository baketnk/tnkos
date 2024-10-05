import urwid
from datetime import datetime

class TerminalApp:
    def __init__(self):
        self.output_widget = urwid.ListBox(urwid.SimpleFocusListWalker([]))
        self.suggestion_widget = urwid.Text("")
        self.input_widget = urwid.Edit("> ")
        self.command_counter = 0

        layout = urwid.Pile([
            ('weight', 70, self.output_widget),
            ('pack', urwid.LineBox(urwid.BoxAdapter(urwid.Filler(self.suggestion_widget), 6))),
            ('pack', self.input_widget)
        ])

        self.loop = urwid.MainLoop(layout, unhandled_input=self.handle_input)
        self.loop.widget.focus_position = 2

    def prefix(self):
        self.command_counter += 1
        return f"{datetime.now().isoformat()}[{self.command_counter}]$"

    def handle_input(self, key):
        if key == 'enter':
            self.process_input(self.input_widget.edit_text)

    def process_input(self, text):
        # Add input to output area
        self.output_widget.body.append(urwid.Text(f"{self.prefix()} {text}"))
        
        # Clear input field
        self.input_widget.edit_text = ""

        # Process command (simple echo for this example)
        self.output_widget.body.append(urwid.Text(f"You entered: {text}"))

        # Update suggestion area (simple example)
        self.suggestion_widget.set_text(f"Suggestion: Try entering 'hello' or 'quit'")

        # Scroll to bottom of output
        self.output_widget.focus_position = len(self.output_widget.body) - 1

    def run(self):
        self.loop.run()

if __name__ == "__main__":
    app = TerminalApp()
    app.run()
