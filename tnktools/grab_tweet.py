import webbrowser
import time
import pyautogui
import os
import httpx
import asyncio
import argparse
from pathlib import Path
from wand.image import Image as WandImage
import base64
import json
INFERENCE_URL = os.getenv("TNKOS_INFERENCE_URL", "http://localhost:7997")


def image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

async def grab_tweet(tweet_url):
    # Create screenshots folder if it doesn't exist
    screenshots_folder = Path(__file__).parent.parent / "screenshots"
    screenshots_folder.mkdir(exist_ok=True)

    # Open the tweet URL in the default browser
    webbrowser.open(tweet_url)
    
    # Wait for the page to load
    time.sleep(1.6)
    
    
    # Take a screenshot of the tweet container
    screenshot = pyautogui.screenshot()
    
    # Save the screenshot temporarily
    temp_screenshot_path = screenshots_folder / f"temp_tweet_{int(time.time())}.png"
    screenshot.save(temp_screenshot_path)
    
    # Process the image with ImageMagick
    with WandImage(filename=str(temp_screenshot_path)) as img:
        # Get original dimensions
        width, height = img.size
        
        # Calculate crop dimensions
        crop_width = width*2 // 5  # Middle third of width
        crop_height = int(height * 2 / 3)  # Top 2/3rds of height
        left = (width - crop_width) // 2
        top = 0
        
        # Crop the image
        img.crop(left=left, top=top, width=crop_width, height=crop_height)

        # Enhance contrast
        img.contrast_stretch(black_point=0.15, white_point=0.85)
        # Save the processed image
        screenshot_path = screenshots_folder / f"tweet_{int(time.time())}.png"
        img.save(filename=str(screenshot_path))
    
    # Remove the temporary screenshot
    os.remove(temp_screenshot_path)
    
    # Close the tab (Ctrl+W on Windows/Linux, Cmd+W on macOS)
    if os.name == 'posix':  # macOS
        pyautogui.hotkey('command', 'w')
    else:  # Windows/Linux
        pyautogui.hotkey('ctrl', 'w')
    return screenshot_path

async def describe_tweet_with_pixtral(image_path):
    # Prepare the request to the local inference server
    url = f"{INFERENCE_URL}/inference"
    print(f"url={url}")
    if "localhost" in url:
        image_data = image_path
    else:
        image_data = f"data:image/png;base64,{image_to_base64(image_path)}"
        
    data = {
        "model_name": "pixtral",
        "input_data": {
            "images": [image_data],
            "prompt": """Describe the post in this format: ```json
{
  user_handle: string, 
  post_content: string, 
  image_description: string|null
}``` 
No yapping, just output the requested JSON format and *only* the requested format."""
        }
    }
    
    try:
        # Send the request to the local inference server
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=data, timeout=60.0)
            response.raise_for_status()
        
        result = response.json()
        print(json.dumps(result))
        return result.get("output", "Failed to get a description from the model.")
    except httpx.HTTPStatusError as e:
        return f"HTTP Error: {e.response.status_code} - {e.response.text}"

async def main(tweet_url):
    image_path = await grab_tweet(tweet_url)
    description = await describe_tweet_with_pixtral(image_path)
    print(description)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Grab a tweet and describe it using Pixtral model.")
    parser.add_argument("tweet_url", help="The URL of the tweet to grab and describe.")
    args = parser.parse_args()

    asyncio.run(main(args.tweet_url))
