import os
import requests
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO
import shutil
import discord
from discord.ext import commands
import os

# إعداد Discord bot
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# إعداد توكن البوت وID القناة
DISCORD_TOKEN = os.environ['TOKEN']
CHANNEL_ID = 1255993654485717003

# بداية رقم الفصل ورابط الفصل
start_chapter_number = 95
start_url = f"https://teamxnovel.com/series/SL/{start_chapter_number}"

# عدد الفصول التي ترغب في تحميلها
num_chapters_to_download = 200  # ضع العدد الذي ترغب فيه

# دالة لتحميل وتحويل كل فصل إلى ملف PDF وإرساله
async def download_and_send_chapters(start_url, start_chapter_number, num_chapters_to_download):
    current_chapter_number = start_chapter_number

    for _ in range(num_chapters_to_download):
        chapter_url = f"https://teamxnovel.com/series/SL/{current_chapter_number}"
        pdf_path = await create_and_send_pdf_for_chapter(chapter_url, current_chapter_number)

        current_chapter_number += 1

# دالة لتحميل الصور وتحويلها إلى ملف PDF لكل فصل وإرساله إلى Discord
async def create_and_send_pdf_for_chapter(chapter_url, chapter_number):
    response = requests.get(chapter_url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # إنشاء مجلد مؤقت للصور
    temp_dir = "temp_images"
    os.makedirs(temp_dir, exist_ok=True)

    # العثور على جميع الصور في الصفحة
    image_tags = soup.find_all('img')
    image_urls = [img['src'] for img in image_tags if 'src' in img.attrs]

    # تنزيل الصور وحفظها في المجلد المؤقت
    for index, image_url in enumerate(image_urls):
        image_response = requests.get(image_url, stream=True)
        if image_response.status_code == 200:
            image = Image.open(BytesIO(image_response.content))
            # استخدام تنسيق ثلاثي الأرقام لضمان الترتيب الصحيح
            image_path = os.path.join(temp_dir, f"chapter_{chapter_number:03d}_{index + 1:03d}.png")
            image.save(image_path)

    # تحويل الصور إلى ملف PDF
    pdf_path = f"chapter_{chapter_number:03d}.pdf"
    image_files = sorted([os.path.join(temp_dir, f) for f in os.listdir(temp_dir) if f.endswith('.png')])
    images = [Image.open(f).convert('RGB') for f in image_files]

    # إنشاء ملف PDF
    if images:
        images[0].save(pdf_path, save_all=True, append_images=images[1:])

    # حذف المجلد المؤقت للصور
    shutil.rmtree(temp_dir)

    # إرسال ملف PDF إلى القناة في Discord
    channel = bot.get_channel(CHANNEL_ID)
    await channel.send(file=discord.File(pdf_path))

    # حذف ملف PDF بعد الإرسال
    os.remove(pdf_path) if os.path.exists(pdf_path) else None

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')

@bot.command()
async def st(ctx):
    await download_and_send_chapters(start_url, start_chapter_number, num_chapters_to_download)

# بدء البوت
bot.run(DISCORD_TOKEN)
