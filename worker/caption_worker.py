# worker/caption_worker.py
import logging
from io import BytesIO

import requests
from PIL import Image

from celery_app import celery
import time

from transformers import BlipProcessor, BlipForConditionalGeneration
import torch

processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")


def download_image(image_url: str):
    response = requests.get(image_url, timeout=10)
    response.raise_for_status()
    return Image.open(BytesIO(response.content)).convert("RGB")

@celery.task(name="caption.generate")
def generate_caption(image_url: str):
    logging.info(f"Downloading image from: {image_url}")

    try:
        image = download_image(image_url)
        logging.info(f"Image downloaded. Size: {image.size}")
    except Exception as e:
        logging.error(f"Failed to download image: {e}")
        return {"error": "could not download image"}

    logging.info("Generating caption ...")
    time.sleep(2)

    inputs = processor(image, return_tensors="pt")
    output = model.generate(**inputs)
    caption = processor.decode(output[0], skip_special_tokens=True)

    return {
        "caption": caption,
        "image_url": image_url,
        "width": image.size[0],
        "height": image.size[1]
    }
