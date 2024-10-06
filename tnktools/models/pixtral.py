import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

import os
from urllib.parse import urljoin
from urllib.request import pathname2url
from typing import Dict, Any, List, Union
from transformers import LlavaForConditionalGeneration, AutoProcessor
from PIL import Image
import torch
import aiohttp
import aiofiles
from io import BytesIO
from interface import ModelInterface

class PixtralModel(ModelInterface):
    def __init__(self):
        self.model = None
        self.processor = None
        self.model_id = "mistral-community/pixtral-12b"
        if torch.backends.mps.is_available():
            self.device = "mps"
        elif torch.cuda.is_available():
            self.device = "cuda"
        else:
            self.device = "cpu"
        print("pixtral using "+self.device)

    def load_model(self) -> None:
        try:
            model_path = os.path.expanduser("~/models/pixtral-12b")
            self.model = LlavaForConditionalGeneration.from_pretrained(self.model_id, cache_dir=model_path).to(self.device)
            self.processor = AutoProcessor.from_pretrained(self.model_id, cache_dir=model_path)
        except Exception as e:
            raise RuntimeError(f"Failed to load model: {str(e)}")

    def unload_model(self) -> None:
        if self.model:
            del self.model
        if self.processor:
            del self.processor
        torch.cuda.empty_cache()
        self.model = None
        self.processor = None

    async def load_image_from_url_or_path(self, path_or_url):
        if os.path.isfile(path_or_url):
            # local path
            try:
                async with aiofiles.open(path_or_url, mode='rb') as file:
                    image_data = await file.read()
                    image = Image.open(BytesIO(image_data)).convert('RGB')
                return image
            except Exception as e:
                logger.error(f"Unable to load image from path: {e}")
                return None
        else:
            # url path
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(path_or_url) as response:
                        response.raise_for_status()
                        image_data = await response.read()
                        image = Image.open(BytesIO(image_data)).convert('RGB')
                return image
            except Exception as e:
                logger.error(f"Unable to load image from URL: {e}")
                return None

    async def run_inference(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        if not self.model or not self.processor:
            raise RuntimeError("Model not loaded. Call load_model() first.")

        try:
            logger.debug(f"Input data: {input_data}")
            image_sources = input_data.get("images", [])
            prompt = input_data.get("prompt", "")

            
            if not image_sources or not prompt:
                raise ValueError("Both 'images' and 'prompt' are required.")

            # Load images
            loaded_images = []
            for source in image_sources:
                image = await self.load_image_from_url_or_path(source)
                if image:
                    loaded_images.append(image)
                else:
                    raise ValueError(f"Failed to load image from {source}")

            logger.debug(f"Loaded {len(loaded_images)} images")

            # Check and correct [IMG] placeholders in the prompt
            img_placeholders_count = prompt.count('[IMG]')
            if img_placeholders_count < len(loaded_images):
                missing_placeholders = len(loaded_images) - img_placeholders_count
                prompt += '\n' + '[IMG]' * missing_placeholders
                logger.info(f"Added {missing_placeholders} missing [IMG] placeholder(s) to the prompt")
            if "[INST]" not in prompt:
                prompt = f"<s>[INST]{prompt}[/INST]"

            logger.debug(f"Final prompt: {prompt}")

            # Process images and text
            inputs = self.processor(images=loaded_images, text=prompt, return_tensors="pt").to(self.device)

            logger.debug("Processed inputs")
            
            with torch.no_grad():
                generate_ids = self.model.generate(**inputs, max_new_tokens=320)
            
            logger.debug("generated output")
            output = self.processor.batch_decode(generate_ids, skip_special_tokens=True, clean_up_tokenization_spaces=False)[0]
            
            logger.debug(f"Decoded output: {output}")
            return {"output": output}
        except Exception as e:
            logger.exception(e)
            return {"error": str(e)}



    async def _load_images(self, image_sources: List[str]) -> List[Image.Image]:
        images = []
        for source in image_sources:
            try:
                if source.startswith(('http://', 'https://')):
                    img = await self._load_image_from_url(source)
                else:
                    img = await self._load_image_from_file(source)
                images.append(img)
            except Exception as e:
                raise ValueError(f"Failed to load image from {source}: {str(e)}")
        return images

    async def _load_image_from_url(self, url: str) -> Image.Image:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    image_data = await response.read()
                    return Image.open(BytesIO(image_data))
                else:
                    raise ValueError(f"Failed to load image from {url}: HTTP status {response.status}")

    async def _load_image_from_file(self, file_path: str) -> Image.Image:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Image file not found: {file_path}")
        
        async with aiofiles.open(file_path, mode='rb') as file:
            image_data = await file.read()
            return Image.open(BytesIO(image_data))

    def get_parameter_info(self) -> Dict[str, Any]:
        return {
            "images": {
                "type": "list",
                "description": "List of image sources. Can be URLs or local file paths."
            },
            "prompt": {
                "type": "string",
                "description": "Text prompt for the model"
            }
        }
