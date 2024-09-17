#bot.py
import discord
from discord.ext import commands
from discord import app_commands
import fireworks_ai
import typing
from discord.ui import Select, View
import stable_diffusion_3
import Danbooru
import io
from discord.ui import Button
import requests
import bing_api
import threading
from dotenv import load_dotenv
import os

# 加載 .env 文件中的環境變量
load_dotenv()

def search_image_from_api(keywords):
    try:
        response = requests.get(f'http://127.0.0.1:5000/search_image', params={'keywords': keywords})
        response.raise_for_status()  # Raise an exception for HTTP errors
    
        if response.status_code == 200:
            return io.BytesIO(response.content)
        else:
            try:
                error_message = response.json().get('error', 'Unknown error')
            except requests.exceptions.JSONDecodeError:
                error_message = 'Unable to decode error response as JSON'
            print(f"Error: {error_message}")
            return None
    
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None
    
class RegenerateButton(Button):
    def __init__(self, selected_tag=None, search_tool=None):
        super().__init__(label="重新生成", style=discord.ButtonStyle.primary)
        self.selected_tag = selected_tag
        self.search_tool = search_tool

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message("重新生成圖像...", ephemeral=True)
        image_bytes = None

        if self.search_tool == "Danbooru(default)" and self.selected_tag:
            # 處理 `waifu` 命令的重新生成
            search_results = Danbooru.search_images(self.selected_tag)
            image_bytes = search_results
        elif self.search_tool == "Bing(not recommendad)":
            image_bytes = search_image_from_api(self.selected_tag)

        if image_bytes:
            try:
                # 發送新的圖像和按鈕
                await interaction.followup.send(file=discord.File(image_bytes, "regenerated_image.jpg"))
            except discord.NotFound:
                await interaction.followup.send("無法找到原始訊息，無法更新圖像。")
        else:
            await interaction.followup.send("重新生成圖像失敗。")



class TagSelect(Select):
    def __init__(self, tag_counts, search_tool=None):
        self.search_tool = search_tool
        # Create options with tag names and their respective image counts
        options = [discord.SelectOption(label=f"{tag} ({count} images)", value=tag) for tag, count in tag_counts.items()]
        super().__init__(placeholder="請選擇一個標籤", options=options, custom_id="tag_select_menu")

    async def callback(self, interaction: discord.Interaction):
        selected_tag = self.values[0]
        await interaction.response.send_message(f"您選擇了: {selected_tag}", ephemeral=True)

        # 調用 search_images 函數進行標籤搜索

        search_results = Danbooru.search_images(selected_tag)  

        if search_results:
            regenerate_button = RegenerateButton(selected_tag=selected_tag, search_tool=self.search_tool)
            view = View()
            view.add_item(regenerate_button)
            await interaction.followup.send(file=discord.File(search_results, "Danbooru_image.jpg"), view=view)
        else:
            await interaction.followup.send("沒有找到圖片。")




def run_discord_bot():
    TOKEN = os.getenv('DISCORD_TOKEN')

    bot = commands.Bot(command_prefix = None, intents = discord.Intents.all())
    
    @bot.event
    async def on_ready(): 
        print(f'{bot.user} is now running!')
        print(f"Registered commands: {[cmd.name for cmd in bot.tree.get_commands()]}")
        
        custom_activity = discord.Activity(type=discord.ActivityType.watching, name="kurumi")
        await bot.change_presence(activity=custom_activity, status=discord.Status.idle)
        
        try:
            synced = await bot.tree.sync()
            print(f"Synced {len(synced)} command(s)")
        except Exception as e:
            print(e)

        threading.Thread(target=lambda: bing_api.app.run(port=5000, debug=True, use_reloader=False)).start()

    async def search_tool_autocompletion(
        interaction: discord.Interaction,
        current: str
    ) -> typing.List[app_commands.Choice[str]]:
        data = []
        for search_tool_choice in["Danbooru(default)", "Bing(not recommendad)"]:
            if current.lower() in search_tool_choice.lower():
                data.append(app_commands.Choice(name=search_tool_choice, value=search_tool_choice))
        return data 


    @bot.tree.command(name="waifu", description="搜索動漫角色圖片")
    @app_commands.autocomplete(search_tool=search_tool_autocompletion)
    @app_commands.describe(character="輸入動漫角色的名字。", search_tool="選擇搜索工具。")
    async def waifu(interaction: discord.Interaction, character: str, search_tool: str = "Danbooru(default)"):
        await interaction.response.send_message(f"正在使用 {search_tool} 搜索 {character}...", ephemeral=True)

        if search_tool == "Danbooru(default)":
            # 使用 Danbooru 進行搜索
            similar_tags = await Danbooru.search_tags(character)
            
            if not similar_tags:
                await interaction.followup.send("没有找到相似的標籤。")
                return
            
            # 發送選擇菜單到用户的私密消息
            tag_select = TagSelect(similar_tags, search_tool=search_tool)
            view = View()
            view.add_item(tag_select)

            user_dm = await interaction.user.create_dm()
            await user_dm.send("請選擇一個標籤:", view=view)
        
        elif search_tool == "Bing(not recommendad)":
            
            # 使用 Bing 搜索
            image_bytes = search_image_from_api(character)
            
            if image_bytes:
                regenerate_button = RegenerateButton(selected_tag=character, search_tool=search_tool)
                view = View()
                view.add_item(regenerate_button)
                await interaction.followup.send(file=discord.File(image_bytes, "bing_image.jpg"), view=view)
            else:
                await interaction.followup.send("使用 Bing 搜索没有找到圖片。")
        else:
            await interaction.followup.send("選擇的搜索工具無效。請選擇 'Danbooru' 或 'Bing'。")


    async def model_autocompletion(
        interaction: discord.Interaction,
        current: str
    ) -> typing.List[app_commands.Choice[str]]:
        data = []
        for main_model_choice in['Firework AI - Stable Diffusion XL', 
            "Firework AI - Segmind Stable Diffusion 1B (SSD-1B)",
            "Firework AI - Playground v2 1024",
            "Firework AI - Japanese Stable Diffusion XL",
            "Stable Diffusion 3 - SD3 Medium",
            "Stable Diffusion 3 - SD3 Large",
            "Stable Diffusion 3 - SD3 Large Turbo"]:
            if current.lower() in main_model_choice.lower():
                data.append(app_commands.Choice(name=main_model_choice, value=main_model_choice))
        return data 

    @bot.tree.command(name="imagine", description="Generate an image with AI")
    @app_commands.autocomplete(model=model_autocompletion)
    @app_commands.describe(prompt="Enter a prompt for image generation.")
    async def imagine(interaction: discord.Interaction, prompt: str, model: str = "Firework AI - Stable Diffusion XL"):
        await interaction.response.send_message(f"Model chosen: {model}", ephemeral=True)
        await interaction.followup.send("Generating image, please wait...")
        
        try:
            image_bytes = None
            
            if model in ['Firework AI - Stable Diffusion XL', 'Firework AI - Segmind Stable Diffusion 1B (SSD-1B)',
                          'Firework AI - Playground v2 1024', 'Firework AI - Japanese Stable Diffusion XL']:
                image_bytes = await fireworks_ai.generate_image(prompt, model)
            else :
                image_bytes = await stable_diffusion_3.generate_image(prompt, model)
            
            if image_bytes:
                await interaction.followup.send(file=discord.File(fp=image_bytes, filename="generated_image.jpg"))
            else:
                await interaction.followup.send("Failed to generate the image.")
        
        except Exception as e:
            await interaction.followup.send(f"An error occurred: {e}")



    bot.run(TOKEN)




