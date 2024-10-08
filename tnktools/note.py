import argparse
import asyncio
import sqlite3
import json
import os
import re
import sys
import httpx
from datetime import datetime
from pathlib import Path
from typing import Optional, List

from bs4 import BeautifulSoup

from tnkos.llm import LLM
from tnktools.grab_tweet import grab_tweet, describe_tweet_with_pixtral
from tnktools.llmjson import parse_llm_json
# Set up database path
DB_PATH = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")) / "notes.db"

def adapt_date_iso(val):
    """Adapt datetime.date to ISO 8601 date."""
    return val.isoformat()

def adapt_datetime_iso(val):
    """Adapt datetime.datetime to timezone-naive ISO 8601 date."""
    return val.isoformat()

def adapt_datetime_epoch(val):
    """Adapt datetime.datetime to Unix timestamp."""
    return int(val.timestamp())


sqlite3.register_adapter(datetime, adapt_datetime_iso)
sqlite3.register_adapter(datetime, adapt_datetime_epoch)

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
    tags = parse_llm_json(tags)  # Assuming the LLM returns a JSON string of tags
    
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

async def handle_twitter_link(url: str) -> str:
    try:
        image_path = await grab_tweet(url)
        description_json = await describe_tweet_with_pixtral(image_path)
        
        description = parse_llm_json(description_json)
        if description is None:
            return f"Failed to parse tweet content. Raw output: {description_json}"
        
        # Format the description into a note
        note_content = f"Tweet from {description.get('user_handle', 'Unknown User')}:\n\n"
        note_content += f"Content: {description.get('post_content', 'No content')}\n\n"
        if description.get('image_description'):
            note_content += f"Image: {description['image_description']}\n\n"
        note_content += f"Original URL: {url}"
        
        return note_content
    except Exception as e:
        return f"Error processing tweet: {str(e)}"


def fetch_and_distill_url(url: str) -> str:
    try:
        response = httpx.get(url)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract the text content from the body
        body = soup.find('body')
        if body:
            # Remove script and style elements
            for script in body(["script", "style"]):
                script.decompose()
            
            # Get text content
            text_content = body.get_text(separator='\n', strip=True)
        else:
            text_content = soup.get_text(separator='\n', strip=True)
        
        # Truncate the content if it's too long (adjust the limit as needed)
        max_chars = 10000  # Adjust this value based on your LLM's token limit
        if len(text_content) > max_chars:
            text_content = text_content[:max_chars] + "..."
        
        llm = LLM()
        distilled_content = llm.prompt_call("distill_content", content=text_content)
        return distilled_content
    except httpx.HTTPStatusError as e:
        return f"HTTP Error: {e.response.status_code} - {e.response.text}"
    except httpx.RequestError as e:
        return f"Request Error: Failed to fetch content from {url} - {str(e)}"
    except Exception as e:
        return f"Unexpected error when processing {url}: {str(e)}"

async def main():
    parser = argparse.ArgumentParser(description="CLI Note Management App")
    parser.add_argument("action", choices=["add", "remove", "rm", "search"], help="Action to perform")
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
                    print("twitter")
                    content = await handle_twitter_link(args.url)
                else:
                    content = fetch_and_distill_url(args.url)
                add_note(content, args.url)
            elif args.content:
                add_note(args.content)
            else:
                # Read from stdin if no content is provided
                print("Enter your note (press Ctrl+D when finished):")
                content = sys.stdin.read().strip()
                if content:
                    add_note(content)
                else:
                    print("Error: No content provided.")

        elif args.action == "remove" or args.action == "rm":
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

if __name__ == "__main__":
    asyncio.run(main=main())

      
