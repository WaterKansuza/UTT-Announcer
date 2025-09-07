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
NEWS_URL = "https://daotao.utt.edu.vn/congthongtin/Index.aspx#tintuc"
last_news = {}

def get_news():
    """Chỉ lấy tin tức từ trang chính thức UTT daotao.utt.edu.vn/congthongtin/#tintuc"""
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'vi-VN,vi;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    # Thử truy cập trang tin tức chính thức UTT
    try:
        print(f"🔍 Đang kiểm tra trang tin tức chính thức: {NEWS_URL}")
        
        session = requests.Session()
        response = session.get(NEWS_URL, headers=headers, timeout=15, verify=False)
        
        print(f"Status code: {response.status_code}")
        print(f"Response length: {len(response.content)}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            page_text = soup.get_text().lower()
            
            # Kiểm tra xem có phải trang login không
            if 'login' in page_text or 'đăng nhập' in page_text:
                print("⚠️ Trang yêu cầu đăng nhập")
                return get_fallback_news("requires_login")
            
            # Tìm tin tức trên trang
            news_items = []
            
            # Tìm các element chứa tin tức
            news_elements = soup.find_all(['div', 'li', 'tr', 'td'], 
                                        string=re.compile(r'thông báo|tin tức|công bố|hướng dẫn', re.IGNORECASE))
            
            for element in news_elements[:5]:
                title_text = element.get_text(strip=True)
                if len(title_text) > 15 and len(title_text) < 150:
                    # Tìm link nếu có
                    link_element = element.find('a') or element.find_parent('a')
                    link = NEWS_URL
                    if link_element and link_element.get('href'):
                        href = link_element.get('href')
                        if href.startswith('http'):
                            link = href
                        elif href.startswith('/'):
                            link = 'https://daotao.utt.edu.vn' + href
                    
                    # Tìm ngày tháng nếu có
                    date_match = re.search(r'(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4})', title_text)
                    date = date_match.group(1) if date_match else datetime.now().strftime('%d/%m/%Y')
                    
                    news_items.append({
                        'title': f"📢 {title_text}",
                        'link': link,
                        'date': date,
                        'content': f"Tin từ trang chính thức UTT\n📅 Ngày: {date}\n🔗 [Chi tiết]({link})"
                    })
            
            if news_items:
                print(f"✅ Tìm thấy {len(news_items)} tin tức từ trang chính thức!")
                return news_items
            else:
                print("⚠️ Không tìm thấy tin tức trên trang")
                return get_fallback_news("no_news_found")
        
        else:
            print(f"❌ Không thể truy cập trang. Status: {response.status_code}")
            return get_fallback_news("access_error")
            
    except Exception as e:
        print(f"❌ Lỗi khi truy cập trang tin tức chính thức: {e}")
        return get_fallback_news("connection_error")

def get_fallback_news(reason):
    """Trả về tin tức hiện tại khi không thể truy cập trang chính thức"""
    
    current_news = {
        'title': '📢 THÔNG BÁO SỐ 1 (Trãi nghiệm VEC K76)',
        'link': NEWS_URL,
        'date': '07/09/2025',
        'content': '**Phòng Đào Tạo** thông báo về chương trình trãi nghiệm VEC K76.\n\n🎓 **Kỷ niệm 80 năm phúng sự và phát triển**\n📅 **Ngày**: 07/09/2025\n🏢 **Đơn vị**: Phòng Đào Tạo'
    }
    
    if reason == "requires_login":
        current_news['content'] += '\n\n🔒 **Lưu ý**: Trang tin tức UTT yêu cầu đăng nhập để xem nội dung mới nhất.'
    elif reason == "access_error":
        current_news['content'] += '\n\n⚠️ **Tình trạng**: Đang gặp khó khăn truy cập trang tin tức chính thức.'
    elif reason == "connection_error":
        current_news['content'] += '\n\n🔄 **Trạng thái**: Đang thử kết nối lại với hệ thống UTT.'
    
    return [current_news]

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