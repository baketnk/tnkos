import argparse
import sqlite3
import os
import httpx
from datetime import datetime
from pathlib import Path
from typing import Optional, List
import json
from tnkos.llm import LLM

# Set up database path
DB_PATH = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")) / "notes.db"

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY,
                content TEXT,
                created_at TIMESTAMP,
                due_at TIMESTAMP,
                tags TEXT,
                url TEXT
            )
        """)

def add_note(content: str, url: Optional[str] = None):
    llm = LLM()
    tags = llm.prompt_call("generate_tags", content=content)
    tags = json.loads(tags)  # Assuming the LLM returns a JSON string of tags
    
    should_have_due_date = llm.prompt_call("should_have_due_date", content=content)
    due_at = datetime.now() if should_have_due_date.lower() == "true" else None
    
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO notes (content, created_at, due_at, tags, url) VALUES (?, ?, ?, ?, ?)",
            (content, datetime.now(), due_at, json.dumps(tags), url)
        )
    print("Note added successfully.")

def remove_note(note_id: int):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    print(f"Note with ID {note_id} removed successfully.")

def search_notes(query: str):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute(
            "SELECT * FROM notes WHERE content LIKE ? OR tags LIKE ?",
            (f"%{query}%", f"%{query}%")
        )
        notes = cursor.fetchall()
    
    if notes:
        for note in notes:
            print(f"ID: {note[0]}, Content: {note[1]}, Created: {note[2]}, Due: {note[3]}, Tags: {note[4]}, URL: {note[5]}")
    else:
        print("No notes found.")

def handle_twitter_link(url: str) -> str:
    # This is a stub function and should be implemented to handle Twitter/X links
    return f"Content from Twitter link: {url}"

def fetch_and_distill_url(url: str) -> str:
    try:
        response = httpx.get(url)
        llm = LLM()
        distilled_content = llm.prompt_call("distill_content", content=response.text)
        return distilled_content
    except httpx.RequestError:
        return f"Failed to fetch content from {url}"

def main():
    parser = argparse.ArgumentParser(description="CLI Note Management App")
    parser.add_argument("action", choices=["add", "remove", "search"], help="Action to perform")
    parser.add_argument("content", nargs="?", help="Note content or search query")
    parser.add_argument("--id", type=int, help="Note ID for removal")
    parser.add_argument("--url", help="URL to fetch content from")

    args = parser.parse_args()

    # Initialize the database
    init_db()

    try:
        if args.action == "add":
            if args.url:
                if "twitter.com" in args.url or "x.com" in args.url:
                    content = handle_twitter_link(args.url)
                else:
                    content = fetch_and_distill_url(args.url)
                add_note(content, args.url)
            elif args.content:
                add_note(args.content)
            else:
                print("Error: Please provide content or a URL to add a note.")
        elif args.action == "remove":
            if args.id:
                remove_note(args.id)
            else:
                print("Error: Please provide a note ID to remove.")
        elif args.action == "search":
            if args.content:
                search_notes(args.content)
            else:
                print("Error: Please provide a search query.")
    except sqlite3.Error as e:
        print(f"An error occurred with the database: {e}")
    except httpx.RequestError as e:
        print(f"An error occurred while fetching the URL: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
      
