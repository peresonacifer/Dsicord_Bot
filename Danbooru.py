import requests
import aiohttp
import asyncio
import random
from io import BytesIO

BASE_URL_TAGS = "https://danbooru.donmai.us/tags.json"
BASE_URL_POSTS = "https://danbooru.donmai.us/posts.json"

# 儲存每個標籤的最後一頁頁數
tag_page_count = {}

def search_tags_containing(query, limit=500):
    """搜索包含 'query' 的標籤"""
    params = {
        "search[name_matches]": f"*{query}*",  # 查找包含 'query' 的標籤
        "limit": limit
    }

    try:
        response = requests.get(BASE_URL_TAGS, params=params)
        response.raise_for_status()  # 如果請求失敗，拋出 HTTPError
        tags = response.json()
        if tags:
            return [tag['name'] for tag in tags]
        return []
    except requests.RequestException as e:
        print(f"請求失败：{e}")
        return []

async def get_total_image_count(session, tag, limit=1000, max_pages=1000):
    total_count = 0
    last_page = 0  # 紀錄最後一頁的頁數
    for page in range(1, max_pages + 1):
        params = {
            "tags": tag,
            "limit": limit,
            "page": page
        }
        try:
            async with session.get(BASE_URL_POSTS, params=params) as response:
                if response.status != 200:
                    print(f"請求失敗，狀態碼：{response.status}，URL：{response.url}")
                    break
                content_type = response.headers.get('Content-Type', '')
                if 'application/json' not in content_type:
                    print(f"返回的内容類型錯誤：{content_type}，URL：{response.url}")
                    break
                data = await response.json()
                if len(data) == 0:
                    break  # 如果當前頁没有圖片，則終止循環
                total_count += len(data)
                last_page = page # 更新最後一頁的頁數
                await asyncio.sleep(0.001)  # 請求間隔，避免請求過於頻繁
        except Exception as e:
            print(f"請求發生錯誤：{e}")
            break
    tag_page_count[tag] = last_page #保存該標籤的最後一頁頁數    
    return total_count

async def get_tags_with_image_counts(tags, max_concurrent_requests=6):
    semaphore = asyncio.Semaphore(max_concurrent_requests)
    
    async def fetch_with_semaphore(tag):
        async with semaphore:
            return await get_total_image_count(session, tag)
    
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_with_semaphore(tag) for tag in tags]
        counts = await asyncio.gather(*tasks)
        return dict(zip(tags, counts))

async def search_tags(query):
    tags = search_tags_containing(query)
    if not tags:
        print("没有找到包含 'kurumi' 的標籤。")
        return []

    tag_counts = await get_tags_with_image_counts(tags)
    
    # 過濾掉圖片數為零的標籤，並按圖片數排序
    filtered_sorted_tags = sorted(
        [(tag, count) for tag, count in tag_counts.items() if count > 0],
        key=lambda x: x[1],
        reverse=True
    )

    # 返回前十個標籤
    top_ten_tags = filtered_sorted_tags[:10]


    print("圖片數量最多的前十个標籤：")
    for idx, (tag, count) in enumerate(top_ten_tags):
        print(f"{idx + 1}. 標籤: {tag}, 圖片數量: {count}")

    return dict(top_ten_tags)
    # return top_ten_tags

def search_images(tags, limit=20):
    # 隨機選擇頁碼
    max_page = tag_page_count.get(tags, 1)
    page = random.randint(1, max_page)    
    
    # 構建請求參數
    params = {
        "tags": tags,
        "limit": limit,  # 下載圖片的數量
        "page": page
    }
    headers = {
        "User-Agent": "Danbooru Image Downloader",
    }
    # 發出請求
    response = requests.get(BASE_URL_POSTS, params=params, headers=headers)
    
    # 打印響應狀態碼和URL
    print(f"Request URL: {response.url}")
    print(f"Response Status Code: {response.status_code}")
    
    response.raise_for_status()

    # 打印返回的 JSON 數據
    print(f"Response JSON: {response.json()}")

   # 獲取 JSON 數據
    posts = response.json()
    
    if not posts:
        print("No images found for the given tags.")
        return None
    random_post = random.choice(posts)
    image_url = random_post.get("file_url")

    if not image_url:
        print("No image URL found.")
        return None

    # 下載圖片
    image_response = requests.get(image_url)
    image_response.raise_for_status()
    
    # 將圖像轉换為字節流
    image_bytes = BytesIO(image_response.content)
    image_bytes.seek(0)
    
    return image_bytes


if __name__ == "__main__":
    asyncio.run(search_tags("kurumi"))
