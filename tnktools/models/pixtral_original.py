
from transformers import LlavaForConditionalGeneration, AutoProcessor
from PIL import Image

model_id = "mistral-community/pixtral-12b"
# NOTE TO LLM: configure the model to be saved to ~/models instead of the hf default
model = LlavaForConditionalGeneration.from_pretrained(model_id).to("cuda")
processor = AutoProcessor.from_pretrained(model_id)

IMG_URLS = [
    "https://picsum.photos/id/237/400/300",
    "https://picsum.photos/id/231/200/300",
    "https://picsum.photos/id/27/500/500",
    "https://picsum.photos/id/17/150/600",
]
PROMPT = "<s>[INST]Describe the images.\n[IMG][IMG][IMG][IMG][/INST]"

inputs = processor(images=IMG_URLS, text=PROMPT, return_tensors="pt").to("cuda")
generate_ids = model.generate(**inputs, max_new_tokens=500)
output = processor.batch_decode(generate_ids, skip_special_tokens=True, clean_up_tokenization_spaces=False)[0]

EXPECTED_GENERATION = """
Describe the images.
Sure, let's break down each image description:

1. **Image 1:**
   - **Description:** A black dog with a glossy coat is sitting on a wooden floor. The dog has a focused expression and is looking directly at the camera.
   - **Details:** The wooden floor has a rustic appearance with visible wood grain patterns. The dog's eyes are a striking color, possibly brown or amber, which contrasts with its black fur.

2. **Image 2:**
   - **Description:** A scenic view of a mountainous landscape with a winding road cutting through it. The road is surrounded by lush green vegetation and leads to a distant valley.
   - **Details:** The mountains are rugged with steep slopes, and the sky is clear, indicating good weather. The winding road adds a sense of depth and perspective to the image.

3. **Image 3:**
   - **Description:** A beach scene with waves crashing against the shore. There are several people in the water and on the beach, enjoying the waves and the sunset.
   - **Details:** The waves are powerful, creating a dynamic and lively atmosphere. The sky is painted with hues of orange and pink from the setting sun, adding a warm glow to the scene.

4. **Image 4:**
   - **Description:** A garden path leading to a large tree with a bench underneath it. The path is bordered by well-maintained grass and flowers.
   - **Details:** The path is made of small stones or gravel, and the tree provides a shaded area with the bench invitingly placed beneath it. The surrounding area is lush and green, suggesting a well-kept garden.

Each image captures a different scene, from a close-up of a dog to expansive natural landscapes, showcasing various elements of nature and human interaction with it.
"""

