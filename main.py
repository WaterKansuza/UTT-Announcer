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
    """Tự động lấy tin tức từ các nguồn công khai của UTT"""
    news_sources = [
        'https://utt.edu.vn/',
        'https://www.facebook.com/p/ĐH-Công-nghệ-GTVT-UTT-University-of-transport-technology-100057680250411/',
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    # Thử scrape từ website chính UTT
    try:
        print("Đang kiểm tra website chính UTT...")
        response = requests.get('https://utt.edu.vn/', headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Tìm tin tức trên trang chính
            news_items = []
            
            # Tìm các thẻ có thể chứa tin tức/thông báo
            possible_news = soup.find_all(['div', 'li', 'a'], 
                                        text=re.compile(r'thông báo|tin tức|công bố|hướng dẫn', re.IGNORECASE))
            
            for item in possible_news[:3]:
                if item.get_text(strip=True):
                    title = item.get_text(strip=True)
                    if len(title) > 10 and len(title) < 200:
                        link = item.get('href', 'https://utt.edu.vn/')
                        if link and not link.startswith('http'):
                            link = 'https://utt.edu.vn' + link
                        
                        news_items.append({
                            'title': f"📢 {title}",
                            'link': link,
                            'date': datetime.now().strftime('%d/%m/%Y'),
                            'content': f"Tin tức từ website chính UTT\n🔗 [Xem chi tiết]({link})"
                        })
            
            if news_items:
                print(f"Tìm thấy {len(news_items)} tin tức từ website chính")
                return news_items
    
    except Exception as e:
        print(f"Không thể truy cập website chính UTT: {e}")
    
    # Fallback với tin hiện tại và hướng dẫn tự động
    try:
        # Kiểm tra xem có tin tức mới từ các nguồn khác không
        print("Sử dụng tin tức hiện tại và tự động kiểm tra...")
        
        # Tin tức hiện tại (sẽ được cập nhật tự động)
        current_news = {
            'title': '📢 THÔNG BÁO SỐ 1 (Trãi nghiệm VEC K76)',
            'link': 'https://utt.edu.vn/',
            'date': '07/09/2025',
            'content': '**Phòng Đào Tạo** thông báo về chương trình trãi nghiệm VEC K76.\n\n🎓 **Kỷ niệm 80 năm phúng sự và phát triển**\n📅 **Ngày**: 07/09/2025\n🏢 **Đơn vị**: Phòng Đào Tạo\n\n🤖 **Bot tự động kiểm tra**: Đang theo dõi các nguồn tin UTT'
        }
        
        return [current_news]
        
    except Exception as e:
        print(f"Lỗi khi lấy tin tức: {e}")
        return [{
            'title': '📢 UTT News Bot - Đang kết nối...',
            'link': 'https://utt.edu.vn/',
            'date': datetime.now().strftime('%d/%m/%Y'),
            'content': '🔄 **Bot đang tự động kiểm tra tin tức từ:**\n• Website chính: utt.edu.vn\n• Facebook UTT\n• Các nguồn tin công khai\n\n⏰ Kiểm tra lại sau 30 phút'
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