import aiohttp
import asyncio
import json
import logging
import time
import base64
import os
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

async def test_pixtral_inference():
    # Server details
    url = os.getenv("TNKOS_INFERENCE_URL", "http://localhost:7997") + "/inference"
    
    # Prepare the input data
    image_path = Path("test.png")
    if not image_path.exists():
        logger.error(f"Image file not found: {image_path}")
        return

    # Check if the server is local or remote
    if "localhost" in url:
        image_data = str(image_path.resolve())
    else:
        image_data = f"data:image/png;base64,{image_to_base64(image_path)}"

    input_data = {
        "model_name": "pixtral",
        "input_data": {
            "images": [image_data],
            "prompt": "Tell me what the post text says and any image attached to the post that isn't a profile picture. [IMG]"
        }
    }

    start_time = time.time()

    try:
        async with aiohttp.ClientSession() as session:
            request_start_time = time.time()
            async with session.post(url, json=input_data) as response:
                if response.status == 200:
                    result = await response.json()
                    request_end_time = time.time()
                    
                    logger.info("Inference successful")
                    logger.info(f"Model output: {result['output']}")
                    
                    # Log timing information
                    request_duration = request_end_time - request_start_time
                    logger.info(f"Request duration: {request_duration:.2f} seconds")
                else:
                    error_text = await response.text()
                    logger.error(f"Inference failed with status {response.status}")
                    logger.error(f"Error message: {error_text}")

    except aiohttp.ClientError as e:
        logger.error(f"Failed to connect to the server: {str(e)}")
    except json.JSONDecodeError:
        logger.error("Failed to parse the server response as JSON")
    except KeyError:
        logger.error("Unexpected response format from the server")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}")

    end_time = time.time()
    total_duration = end_time - start_time
    logger.info(f"Total process duration: {total_duration:.2f} seconds")

if __name__ == "__main__":
    asyncio.run(test_pixtral_inference())
