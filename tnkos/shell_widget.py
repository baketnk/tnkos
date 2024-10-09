import asyncio
from textual.widgets import Input, Static,  RichLog, MarkdownViewer
from textual.containers import Vertical, Container, ScrollableContainer
from textual.message import Message
from textual.reactive import reactive
from rich.syntax import Syntax
from rich.console import Console
from rich.theme import Theme
from rich.text import Text
import subprocess
import os
from .suggestions import get_suggestions_async
from .llm import LLM
from textual import log 

from datetime import datetime
import time

from textual.app import App
from textual.widgets import Header, Footer
from textual.binding import Binding


from .history import HistoryView, add_command_to_history, search_command_history

class ShellApp(App):

    """A custom widget for a shell-like interface with syntax highlighting."""

    class SuggestionsUpdated(Message):
        def __init__(self, suggestions):
            self.suggestions = suggestions
            super().__init__()

    suggestions = reactive([])
    command_history = reactive([])
    current_directory = reactive(os.getcwd())
    input_mode = "command"

    BINDINGS = [
        ("ctrl+d", "quit", "Quit"),
        Binding("ctrl+e", "explain_command", "Explain Command", priority=True),
        Binding("ctrl+r", "reverse_search", "Reverse Search", priority=True),
        Binding("ctrl+s", "select_suggestion", "Select Suggestion", priority=True),
        # Binding("ctrl+c", "keyboard_interrupt", "Keyboard Interrupt", priority=True),
        Binding("escape", "multi_escape", priority=True),
        Binding("up", "multi_up", priority=True),
        Binding("down", "multi_down", priority=True),
    ]

    CSS = """
    #app-grid { 
        layout: grid;
        grid-size: 2;
        grid-columns: 1fr;
        grid-rows: 1fr;
    }
    #left-pane {
        width: 100%;
        height: 100%;
        background: $panel;
        border: dodgerblue;
    }
    #right-pane {
        height: 100%;
        background: $panel;
        border: mediumvioletred;
    }
    .box {
    }
    .scrollable {
        overflow-y: auto;
    }
    #maininput {
        border: solid $success;
        dock: bottom;
    }
    """
    

    def __init__(self):
        super().__init__()
        self.console = Console(theme=Theme({"prompt": "cyan", "command": "green"}))
        self.suggestion_task = None
        self.llm = LLM()

    def compose(self):
        with Container(id="app-grid"):
            with Vertical(id="left-pane"):
                yield RichLog(highlight=True, markup=True, wrap=True, id="output", classes="box")
                yield HistoryView(id="history-view", classes="scrollable")
                yield Static(id="suggestions", classes="box")
                yield Input(id="maininput", placeholder="Enter a command...", classes="box")
            with Vertical(id="right-pane"):
                yield MarkdownViewer("# Advice Widget", id="advisor", show_table_of_contents=False, classes="box")

    def on_mount(self):
        self.input = self.query_one("#maininput")
        self.input.focus()
        self.output = self.query_one("#output")
        self.suggestions_widget = self.query_one("#suggestions")
        self.output_container = self.output
        self.advisor_viewer = self.query_one("#advisor")
        self.advisor = self.advisor_viewer.document

        self.history_view = self.query_one("#history-view")
        self.history_view.display = False

        self.main_views = [
                self.output,
                self.history_view
        ]
        self.input_mode = "command"
        self.call_after_refresh(self.initial_layout)

    def initial_layout(self):
        log.info(f"Initial layout - Container: {self.output_container.size}, Output: {self.output.size}")

    def prefix(self):
        # TODO: add cwd or whatever prefix from zsh here?
        return datetime.now().isoformat() + " % "

    async def explain_command(self):
        """Generate and display an explanation for the current command."""
        command = self.input.value
        if not command:
            return

        log.debug(f"explaining {command}")
        self.advisor.update("Loading...")
        try:
            explanation = self.llm.prompt_call(
                "explain_command",
                command=command,
                current_dir=self.current_directory
            )

            self.advisor.update(f"# Command Explanation\n\n{explanation}")
        except Exception as e:
            log.error(f"Error generating command explanation: {str(e)}")
            self.advisor.update("# Error\n\nFailed to generate command explanation.")

    def action_explain_command(self):
        """Action to trigger command explanation."""
        log.debug("setting up call later")
        self.call_later(self.explain_command)

    def highlight_input(self, text):
        """Apply syntax highlighting to the input text."""
        return Text.from_markup(f"[prompt]$[/prompt] [command]{text}[/command]")

    def highlight_output(self, text, lexer="bash"):
        """Apply syntax highlighting to the output text."""
        syntax = Syntax(text, lexer, theme="monokai", line_numbers=False)
        with self.console.capture() as capture:
            self.console.print(syntax)
        return Text.from_ansi(capture.get())

    async def update_suggestions(self, value):
        """Debounced method to update suggestions."""
        await asyncio.sleep(0.5)  # Reduced debounce delay
        suggestions = await get_suggestions_async(value, self.current_directory, self.command_history)
        self.suggestions = suggestions
        self.display_suggestions(suggestions)
        self.post_message(self.SuggestionsUpdated(suggestions))

    def display_suggestions(self, suggestions):
        """Display suggestions below the input."""
        suggestion_text = "\n".join(suggestions)
        self.suggestions_widget.update(suggestion_text)

    def update_main_view(self):
        for v in self.main_views:
            v.display = False
        if self.input_mode == "command":
            self.output.display = True
        elif self.input_mode == "history":
            self.history_view.display = True

    def keyboard_interrupt(self):
        # if there's a running process, transmit sigterm
        # if the user pressed recently, issue sigterm/quit
        # otherwise set the flag to quit again
        if self.interrupt_pressed is not None:
            self.app.quit()
            return
        self.interrupt_pressed = time.time()
        self.suggestions_widget.update("press Ctrl+C again to quit")

    def action_multi_escape(self):
        if self.input_mode == "history":
            self.input_mode = "command"
            self.update_main_view()
        else:
            pass

    def action_multi_up(self):
        if self.input_mode == "command":
            # tab backwarsd through commands
            pass
        elif self.input_mode == "history":
            self.history_view.previous_command()

    def action_multi_down(self):
        if self.input_mode == "command":
            # tab foward through commands until reach stored current line
            pass
        elif self.input_mode == "history":
            self.history_view.next_command()

    def action_select_suggestion(self):
        selected_suggestion = self.suggestions[self.suggestions_widget.highlighted_line]
        self.input.value = selected_suggestion

    def action_reverse_search(self):
        self.input.value = ""
        self.input.placeholder = "Search history (press Enter to select, Esc to cancel)"
        self.input.focus()
        self.input_mode = "history"
        self.update_main_view()

    def append_output(self, new_content):
        if isinstance(new_content, Text):
            self.output.write(new_content)
        elif isinstance(new_content, str):
            self.output.write(new_content)
        else:
            log.warning(f"Unexpected content type: {type(new_content)}")
            return

        # self.output.write("\n")
        
        # self.output_container.refresh(laye)
        # self.output.scroll_end()
        
    def on_input_submitted(self, message):
        command = message.value
        log.info(f"Command submitted: {command}")
        if self.input_mode == "history":
            selected_command = self.history_view.get_selected_command()
            self.input.value = selected_command
            self.input_mode = "command"
            self.update_main_view()
            return
        
        # highlighted_input = self.highlight_input(command)
        # self.append_output(highlighted_input)
        self.output.write(self.prefix()+command)
        add_command_to_history(command)
        # self.output.refresh()
        
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, cwd=self.current_directory)
            output = result.stdout if result.returncode == 0 else result.stderr
            highlighted_output = output # self.highlight_output(output)
            log.debug(f"Highlighted output type: {type(highlighted_output)}")
            self.append_output(highlighted_output)

            # Update command history
            self.command_history.append(command)
            if len(self.command_history) > 500:  # Keep last 50o commands
                self.command_history.pop(0)

            # Update current directory if the command was 'cd'
            if command.startswith('cd '):
                new_dir = command[3:].strip()
                self.current_directory = os.path.abspath(os.path.join(self.current_directory, new_dir))
                log.info(f"Changed directory to: {self.current_directory}")

        except Exception as e:
            error_output = Text.from_markup(f"[red]Error: {str(e)}[/red]")
            self.append_output(error_output)
            log.error(f"Error executing command: {str(e)}")

        self.input.value = ""
        
    def on_input_changed(self, message):
        """Handle immediate input updates."""
        current_input = message.value

        if self.input_mode == "history":
            # search history instead of / in addition to LLM stuff
            self.history_view.update(current_input)
        else:
            # Cancel the previous suggestion task if it exists
            if self.suggestion_task:
                self.suggestion_task.cancel()

            # Start a new suggestion task
            self.suggestion_task = asyncio.create_task(self.update_suggestions(current_input))



