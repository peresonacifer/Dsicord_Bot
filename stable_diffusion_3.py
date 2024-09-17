#stable_diffusion_3.py
import requests
from io import BytesIO
from dotenv import load_dotenv
import os

# 加載 .env 文件中的環境變量
load_dotenv()

api_key = os.getenv('Stable_Diffusion_3')

async def generate_image(prompt: str, model: str) -> BytesIO:
    model_map= {"Stable Diffusion 3 - SD3 Medium" : "sd3-medium",
            "Stable Diffusion 3 - SD3 Large" : "sd3-large",
            "Stable Diffusion 3 - SD3 Large Turbo" : "sd3-large-turbo"}
    for i in model_map:
        if i == model:
            model = model_map[i]
    response = requests.post(
        f"https://api.stability.ai/v2beta/stable-image/generate/sd3",
        headers={
            "authorization": api_key,
            "accept": "image/*"
        },
        files={"none": ''},
        data={
            "prompt": prompt,
            "output_format": "jpeg",
            "model": model,
        },
    )
    if response.status_code == 200:
        image_bytes = BytesIO(response.content)
        image_bytes.seek(0)  # Ensure the stream is at the beginning
        return image_bytes
    else:
        raise Exception(str(response.json()))
    
    