import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

import asyncio
from abc import ABC, abstractmethod
from typing import Any, Dict, List
from aiohttp import web
import time

import base64

from PIL import Image
from io import BytesIO

from pixtral import PixtralModel
from interface import ModelInterface


class InferenceServer:
    def __init__(self, timeout: int = 600):
        self.models: Dict[str, Dict[str, Any]] = {}
        self.timeout = timeout

    async def load_model(self, model_name: str, model_class: type) -> None:
        if model_name not in self.models:
            model = model_class()
            await asyncio.to_thread(model.load_model)
            self.models[model_name] = {
                "model": model,
                "last_used": time.time()
            }

    async def unload_model(self, model_name: str) -> None:
        if model_name in self.models:
            await asyncio.to_thread(self.models[model_name]["model"].unload_model)
            del self.models[model_name]

    async def run_inference(self, model_name: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        if model_name not in self.models:
            raise ValueError(f"Model {model_name} is not loaded")
        self.models[model_name]["last_used"] = time.time()
        return await self.models[model_name]["model"].run_inference(input_data)

    def is_model_loaded(self, model_name: str) -> bool:
        return model_name in self.models

    def get_model_parameter_info(self, model_name: str) -> Dict[str, Any]:
        if model_name not in self.models:
            raise ValueError(f"Model {model_name} is not loaded")
        return self.models[model_name]["model"].get_parameter_info()

    async def check_and_unload_inactive_models(self):
        current_time = time.time()
        for model_name in list(self.models.keys()):
            if current_time - self.models[model_name]["last_used"] > self.timeout:
                await self.unload_model(model_name)

def get_model_class(model_name: str) -> type:
    if model_name.lower() == "pixtral":
        return PixtralModel
    else:
        raise ValueError(f"Unknown model: {model_name}")


async def handle_inference(request):
    server = request.app['inference_server']
    try:
        data = await request.json()
        model_name = data.get('model_name')
        input_data = data.get('input_data')

        if not model_name or not input_data:
            return web.json_response({"error": "Both model_name and input_data are required"}, status=400)

        # Handle base64 image data
        if 'images' in input_data:
            processed_images = []
            for img in input_data['images']:
                if img.startswith('data:image'):
                    # Extract the base64 data
                    img_data = img.split(',')[1]
                    # Decode the base64 data
                    img_bytes = base64.b64decode(img_data)
                    # Open the image using PIL
                    img_obj = Image.open(BytesIO(img_bytes))
                    # Save the image to a temporary file
                    temp_path = f"/tmp/temp_image_{time.time()}.png"
                    img_obj.save(temp_path)
                    processed_images.append(temp_path)
                else:
                    # If it's not base64, assume it's a file path
                    processed_images.append(img)
            
            # Update the input_data with processed image paths
            input_data['images'] = processed_images

        if not server.is_model_loaded(model_name):
            logger.info(f"Loading model: {model_name}")
            model_class = get_model_class(model_name)
            await server.load_model(model_name, model_class)

        logger.info(f"Running inference for model: {model_name}")
        result = await server.run_inference(model_name, input_data)
        logger.info(f"Inference result: {result}")
        return web.json_response(result)
    except ValueError as e:
        logging.exception(e)
        return web.json_response({"error": str(e)}, status=400)
    except Exception as e:
        logging.exception(e)
        param_info = server.get_model_parameter_info(model_name) if server.is_model_loaded(model_name) else {}
        error_message = f"An error occurred: {str(e)}\nExpected parameters: {param_info}"
        return web.json_response({"error": error_message}, status=500)

async def background_tasks(app):
    while True:
        await app['inference_server'].check_and_unload_inactive_models()
        await asyncio.sleep(60)  # Check every minute

async def start_background_tasks(app):
    app['background_tasks'] = asyncio.create_task(background_tasks(app))
    await app['inference_server'].load_model("pixtral", PixtralModel)


async def cleanup_background_tasks(app):
    app['background_tasks'].cancel()
    await app['background_tasks']

def run_server():
    app = web.Application()
    app['inference_server'] = InferenceServer()
    app.router.add_post('/inference', handle_inference)
    app.on_startup.append(start_background_tasks)
    app.on_cleanup.append(cleanup_background_tasks)
    web.run_app(app, port=7997)

if __name__ == '__main__':
    run_server()
