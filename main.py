import discord
from discord.ext import tasks, commands
import requests
from bs4 import BeautifulSoup
import asyncio
import os
import re
from datetime import datetime
from flask import Flask
from threading import Thread

# Tạo Flask app để giữ repl live
app = Flask('')

@app.route('/')
def home():
    return "🤖 UTT News Bot is running!"

def run_flask():
    app.run(host='0.0.0.0', port=5000)

# Chạy Flask trong thread riêng
Thread(target=run_flask).start()

# Phần còn lại của bot code...
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)
NEWS_URL = "https://daotao.utt.edu.vn/congthongtin/Index.aspx"
last_news = {}

def get_news():
    return [{
        'title': '📢 Thông báo mẫu từ trường',
        'link': NEWS_URL,
        'date': datetime.now().strftime('%d/%m/%Y'),
        'content': 'Bot đang hoạt động!'
    }]

@bot.event
async def on_ready():
    print(f'{bot.user} đã kết nối thành công!')
    check_news.start()

@tasks.loop(minutes=5)
async def check_news():
    try:
        channel = bot.get_channel(int(os.environ['DISCORD_CHANNEL_ID']))
        if channel:
            news_items = get_news()
            for news in news_items:
                embed = discord.Embed(title=news['title'], description=news['content'], color=0x00ff00)
                await channel.send(embed=embed)
    except Exception as e:
        print(f"Lỗi: {e}")

# Chạy bot
if __name__ == "__main__":
    bot.run(os.environ['DISCORD_BOT_TOKEN'])