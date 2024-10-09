import os
from pathlib import Path
import subprocess
from .fuzzy import fuzzymatch_v2

HISTORY_FILE = Path.home() / ".tnkos_history"
SHELL_HISTORY_FILE = Path.home() / ".zsh_history"  # Adjust the file path based on your shell

def load_history():
    if not HISTORY_FILE.exists():
        return []
    with open(HISTORY_FILE, "r") as file:
        return file.read().splitlines()

def save_history(commands):
    with open(HISTORY_FILE, "w") as file:
        file.write("\n".join(commands))

def add_command_to_history(command):
    commands = load_history()
    commands.append(command)
    save_history(commands)

def search_command_history(query, max_items=50):
    tnikos_commands = load_history()
    shell_commands = load_shell_history()

    all_commands = tnikos_commands + shell_commands
    scored_commands = []
    for command in all_commands:
        result = fuzzymatch_v2(False, False, True, command, query, False)
        if result[0][0] != -1:
            scored_commands.append((command, result[0],))


    scored_commands.sort(key=lambda x: x[1], reverse=True)

    return scored_commands[:max_items]

def load_shell_history():
    if not SHELL_HISTORY_FILE.exists():
        return []
    with open(SHELL_HISTORY_FILE, "r") as file:
        return file.read().splitlines()

from textual.widgets import ListView, ListItem, Label, Static
from rich.text import Text 
from rich.style import Style

class HistoryView(ListView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initialized = False

    def update(self, query):
        scored_commands = search_command_history(query)

        if scored_commands:
            top_command, _ = scored_commands[0]

        items = []
        for command, (start_idx, end_idx, _) in scored_commands:
            if command == top_command:
                continue
            highlighted_command = Text(command[:start_idx])
            highlighted_command.append(command[start_idx:end_idx], style=Style(reverse=True))
            highlighted_command.append(command[end_idx:])
            items.append(highlighted_command)

        if scored_commands:
            highlighted_top_command = Text(top_command[:start_idx])
            highlighted_top_command.append(top_command[start_idx:end_idx], style=Style(reverse=True))
            highlighted_top_command.append(top_command[end_idx:])
            items.append(highlighted_top_command)

        # Limit items based on available rows
        available_rows = self.size.height
        if len(items) > available_rows:
            items = items[:available_rows]

        # Pad with blank items if needed
        while len(items) < available_rows:
            items.append(Text(""))

        items.reverse()

        if not self.initialized:
            self.extend(ListItem(Label(item)) for item in items)
            self.initialized = True
        else:
            # Update existing ListItems
            for index, item in enumerate(items[: len(self.children)]):
                self.children[index].label.update(item)

            # Add new ListItems if needed
            if len(items) > len(self.children):
                self.extend(ListItem(Label(item)) for item in items[len(self.children) :])

            # Remove excess ListItems if needed
            if len(items) < len(self.children):
                for _ in range(len(self.children) - len(items)):
                    self.children.pop()

    def get_selected_command(self):
        valid_index = self.validate_index(self.index) 
        if self.children and valid_index: 
            return self.children[self.index].label.plain
        return ""

    def previous_command(self):
        self.index = self.validate_index( self.index + 1 ) 


    def next_command(self):
        next_index = self.validate_index( self.index - 1 )
        if self.children[next_index].label.plain != "":
            self.index = next_index



