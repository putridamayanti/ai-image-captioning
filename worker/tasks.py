# worker/tasks.py
import base64
import logging
from io import BytesIO

import requests
from PIL import Image

# use relative import so Celery can import this module as part of the worker package
from .celery_app import celery
import time

# Defer heavy ML model imports until the task runs to avoid import-time side effects
processor = None
model = None


def _load_model():
    """Lazy-load the processor and model. Safe to call multiple times."""
    global processor, model
    if processor is None or model is None:
        from transformers import BlipProcessor, BlipForConditionalGeneration
        processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base", use_fast=True)
        model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
        model.eval()


def download_image(image_url: str):
    response = requests.get(image_url, timeout=10)
    response.raise_for_status()
    return Image.open(BytesIO(response.content)).convert("RGB")

def is_base64(s):
    try:
        base64.b64decode(s.encode('utf-8'))
        return True
    except base64.binascii.Error:
        return False

def load_from_base64(b64_string: str):
    import base64
    image_data = base64.b64decode(b64_string)
    return Image.open(BytesIO(image_data)).convert("RGB")

@celery.task(name="caption.generate")
def generate_caption(target_arg: str):
    try:
        # ensure models are loaded in worker process
        print("Loading model")
        _load_model()
        print("Model loaded.")
        if not is_base64(target_arg):
            logging.info(f"Downloading image from: {target_arg}")

            try:
                image = download_image(target_arg)
                logging.info(f"Image downloaded. Size: {image.size}")
            except Exception as e:
                logging.error(f"Failed to download image: {e}")
                return {"error": "could not download image"}
        else:
            logging.info("Loading image from base64 string")
            try:
                image = load_from_base64(target_arg)
                logging.info(f"Image loaded from base64. Size: {image.size}")
            except Exception as e:
                logging.error(f"Failed to load image from base64: {e}")
                return {"error": "could not load image from base64"}

        logging.info("Generating caption ...")
        time.sleep(2)

        inputs = processor(image, return_tensors="pt")
        output = model.generate(**inputs)
        caption = processor.decode(output[0], skip_special_tokens=True)

        return {
            "caption": caption,
            # "image_url": image_url,
            "width": image.size[0],
            "height": image.size[1]
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise e
