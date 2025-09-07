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
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(NEWS_URL, headers=headers, timeout=10)
        response.encoding = 'utf-8'
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            news_items = []
            
            # Tìm các thông báo trên trang
            # Thử tìm các thẻ li chứa thông báo
            announcements = soup.find_all('li') + soup.find_all('tr') + soup.find_all('div', class_=re.compile('news|announcement|title'))
            
            for item in announcements[:5]:  # Lấy 5 tin đầu tiên
                title_element = item.find('a') or item.find('span') or item
                if title_element and title_element.get_text(strip=True):
                    title = title_element.get_text(strip=True)
                    if len(title) > 20 and not any(skip in title.lower() for skip in ['menu', 'button', 'javascript']):
                        link = title_element.get('href', NEWS_URL)
                        if link and not link.startswith('http'):
                            link = 'https://daotao.utt.edu.vn' + link
                        
                        # Tìm ngày tháng nếu có
                        date_text = item.get_text()
                        date_match = re.search(r'(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4})', date_text)
                        date = date_match.group(1) if date_match else datetime.now().strftime('%d/%m/%Y')
                        
                        news_items.append({
                            'title': f"📢 {title[:100]}..." if len(title) > 100 else f"📢 {title}",
                            'link': link,
                            'date': date,
                            'content': f"Ngày: {date}\n🔗 [Xem chi tiết]({link})"
                        })
            
            if news_items:
                return news_items
            
        # Fallback nếu không scrape được
        return [{
            'title': '📢 Không thể tải tin tức mới',
            'link': NEWS_URL,
            'date': datetime.now().strftime('%d/%m/%Y'),
            'content': f'Vui lòng kiểm tra trực tiếp tại: {NEWS_URL}'
        }]
        
    except Exception as e:
        print(f"Lỗi khi lấy tin tức: {e}")
        return [{
            'title': '📢 Lỗi khi tải tin tức',
            'link': NEWS_URL,
            'date': datetime.now().strftime('%d/%m/%Y'),
            'content': f'Có lỗi xảy ra. Vui lòng kiểm tra: {NEWS_URL}'
        }]

@bot.event
async def on_ready():
    print(f'{bot.user} đã kết nối thành công!')
    check_news.start()

@bot.command(name='news')
async def get_latest_news(ctx):
    """Lấy tin tức mới nhất từ UTT"""
    try:
        news_items = get_news()
        if news_items:
            # Gửi tin đầu tiên (mới nhất)
            news = news_items[0]
            embed = discord.Embed(
                title=news['title'], 
                description=news['content'], 
                color=0x00ff00
            )
            embed.add_field(name="Ngày", value=news['date'], inline=True)
            embed.add_field(name="Link", value=f"[Xem thêm]({news['link']})", inline=True)
            await ctx.send(embed=embed)
        else:
            await ctx.send("❌ Không thể lấy tin tức lúc này.")
    except Exception as e:
        print(f"Lỗi khi gửi tin tức: {e}")
        await ctx.send("❌ Có lỗi xảy ra khi lấy tin tức.")

@tasks.loop(minutes=30)
async def check_news():
    try:
        channel = bot.get_channel(int(os.environ['DISCORD_CHANNEL_ID']))
        if channel:
            news_items = get_news()
            if news_items:
                # Chỉ gửi tin đầu tiên để tránh spam
                news = news_items[0]
                # Kiểm tra xem tin này đã gửi chưa (đơn giản)
                if news['title'] not in last_news:
                    embed = discord.Embed(
                        title=news['title'], 
                        description=news['content'], 
                        color=0x00ff00
                    )
                    embed.add_field(name="Ngày", value=news['date'], inline=True)
                    await channel.send(embed=embed)
                    last_news[news['title']] = True
    except Exception as e:
        print(f"Lỗi: {e}")

# Chạy bot
if __name__ == "__main__":
    bot.run(os.environ['DISCORD_BOT_TOKEN'])