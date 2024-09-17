import requests
import io
from PIL import Image
import random
import re

def bing_get_image_url_using_api(keywords, max_number=10000, face_only=False, proxy=None, proxy_type=None):
    proxies = None
    if proxy and proxy_type:
        proxies = {"http": "{}://{}".format(proxy_type, proxy),
                   "https": "{}://{}".format(proxy_type, proxy)}                             
    start = 1
    image_urls = []
    g_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    while start <= max_number:
        url = 'https://www.bing.com/images/async?q={}&first={}&count=35'.format(keywords, start)
        res = requests.get(url, proxies=proxies, headers=g_headers)
        res.encoding = "utf-8"
        image_urls_batch = re.findall('murl&quot;:&quot;(.*?)&quot;', res.text)
        if len(image_urls) > 0 and image_urls_batch[-1] == image_urls[-1]:
            break
        image_urls += image_urls_batch
        start += len(image_urls_batch)
    return image_urls

def search_original_image(keywords, max_images=50, face_only=False, proxy=None, proxy_type=None):
    image_urls = bing_get_image_url_using_api(keywords, max_number=max_images, face_only=face_only, proxy=proxy, proxy_type=proxy_type)
    
    if not image_urls:
        print("No images found.")
        return None

    # 限制最大圖片數量
    if len(image_urls) > max_images:
        image_urls = image_urls[:max_images]
        # Print all found image URLs for debugging
        for i, url in enumerate(image_urls):
            print(f"Image {i}: {url}")

    # Randomly select one image URL
    image_url = random.choice(image_urls)
    print(f"Selected image URL: {image_url}")

    # Download and return the original image
    image_content = requests.get(image_url)
    if image_content.status_code != 200:
        raise ValueError("Failed to download image")
    image_file = io.BytesIO(image_content.content)
    
    # Verify the image format and return BytesIO object
    try:
        image = Image.open(image_file)
        if image.mode != 'RGB':
            image = image.convert('RGB')
        image_bytes = io.BytesIO()
        image.save(image_bytes, format='JPEG')
        image_bytes.seek(0)
        return image_bytes
    except Exception as e:
        print(f"Image format error: {e}")
        return None
