# app.py
import sys
import os

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tnkos.shell_widget import ShellApp

def main():
    app = ShellApp()
    app.run()

if __name__ == "__main__":
    main()
