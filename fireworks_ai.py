# firework_ai.py
from fireworks.client.image import ImageInference, Answer #提供了與 Fireworks AI API 互動的方法
from io import BytesIO #這裡是用來將生成的圖像保存為二進制格式，以便後續處理。
from dotenv import load_dotenv
import os
import logging #用來記錄日誌信息，用於跟踪程式的執行狀態和錯誤信息

# 加載 .env 文件中的環境變量
load_dotenv()

FIREWORKS_API_KEY = os.getenv('FIREWORKS_API_KEY')

logging.basicConfig(level=logging.INFO)

async def generate_image(prompt: str, model: str) -> BytesIO:
    model_map= {"Firework AI - Stable Diffusion XL" : "stable-diffusion-xl-1024-v1-0", 
            "Firework AI - Segmind Stable Diffusion 1B (SSD-1B)" : "SSD-1B",
            "Firework AI - Playground v2 1024" : "playground-v2-1024px-aesthetic",
            "Firework AI - Japanese Stable Diffusion XL" : "japanese-stable-diffusion-xl" }
    for i in model_map:
        if i == model:
            model = model_map[i]
    # Initialize the ImageInference client
    inference_client = ImageInference(model=model, api_key=FIREWORKS_API_KEY)
    try:
        logging.info("Starting image generation")
        answer: Answer = await inference_client.text_to_image_async(
            prompt=prompt,
            cfg_scale=7,
            height=1024,
            width=1024,
            sampler=None,
            steps=100,
            seed=0,
            safety_check=False,
            output_image_format="JPG",
        )
        
        logging.info("Image generated successfully")

        if answer.image is None:
            raise RuntimeError(f"No return image, {answer.finish_reason}")
        
        image_bytes = BytesIO()
        answer.image.save(image_bytes, format='JPEG')
        image_bytes.seek(0)
        return image_bytes

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        raise


















































