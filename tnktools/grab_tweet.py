import webbrowser
import time
import pyautogui
import os
import httpx
import asyncio
import argparse
from pathlib import Path
from wand.image import Image as WandImage

async def grab_tweet(tweet_url):
    # Create screenshots folder if it doesn't exist
    screenshots_folder = Path(__file__).parent.parent / "screenshots"
    screenshots_folder.mkdir(exist_ok=True)

    # Open the tweet URL in the default browser
    webbrowser.open(tweet_url)
    
    # Wait for the page to load
    time.sleep(1.6)
    
    
    # Take a screenshot of the tweet container
    tweet_container = pyautogui.locateOnScreen('tweet_container_template.png', grayscale=True, confidence=0.15)
    screenshot = pyautogui.screenshot(region=tweet_container)
    
    # Save the screenshot temporarily
    temp_screenshot_path = screenshots_folder / f"temp_tweet_{int(time.time())}.png"
    screenshot.save(temp_screenshot_path)
    
    # Process the image with ImageMagick
    with WandImage(filename=str(temp_screenshot_path)) as img:
        # Resize to a maximum width of 800 pixels while maintaining aspect ratio
        img.transform(resize='800x')
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
    
    # Use the Pixtral model to describe the tweet
    description = await describe_tweet_with_pixtral(str(screenshot_path))
    
    return description

async def describe_tweet_with_pixtral(image_path):
    # Prepare the request to the local inference server
    url = "http://localhost:7997/inference"
    data = {
        "model_name": "pixtral",
        "input_data": {
            "images": [image_path],
            "prompt": "Describe the tweet in the center of this image. Ignore menus, tabs, and other non-centered content."
        }
    }
    
    try:
        # Send the request to the local inference server
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=data, timeout=60.0)
            response.raise_for_status()
        
        result = response.json()
        return result.get("output", "Failed to get a description from the model.")
    except httpx.HTTPStatusError as e:
        return f"HTTP Error: {e.response.status_code} - {e.response.text}"

async def main(tweet_url):
    description = await grab_tweet(tweet_url)
    print(description)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Grab a tweet and describe it using Pixtral model.")
    parser.add_argument("tweet_url", help="The URL of the tweet to grab and describe.")
    args = parser.parse_args()

    asyncio.run(main(args.tweet_url))
