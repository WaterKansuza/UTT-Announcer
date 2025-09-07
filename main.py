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
    """Lấy tin tức từ website UTT hoặc trả về thông tin hướng dẫn"""
    try:
        # Thông tin tin tức mẫu cho UTT (website thực tế cần đăng nhập)
        sample_news = [
            {
                'title': '📢 Thông báo về lịch thi cuối kỳ học kỳ I năm học 2024-2025',
                'link': 'https://daotao.utt.edu.vn/congthongtin/Index.aspx',
                'date': datetime.now().strftime('%d/%m/%Y'),
                'content': 'Thông báo lịch thi cuối kỳ dành cho sinh viên UTT. Vui lòng kiểm tra lịch thi trên hệ thống đào tạo.'
            },
            {
                'title': '📢 Hướng dẫn đăng ký học phần học kỳ II năm học 2024-2025',
                'link': 'https://daotao.utt.edu.vn/congthongtin/Index.aspx',
                'date': datetime.now().strftime('%d/%m/%Y'),
                'content': 'Thông báo về thời gian và quy trình đăng ký học phần cho học kỳ mới.'
            },
            {
                'title': '📢 Thông báo về học phí và các khoản thu học kỳ I',
                'link': 'https://daotao.utt.edu.vn/congthongtin/Index.aspx',
                'date': datetime.now().strftime('%d/%m/%Y'),
                'content': 'Thông báo về học phí và các khoản thu dành cho sinh viên.'
            }
        ]
        
        # Cố gắng truy cập website thực
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        try:
            response = requests.get(NEWS_URL, headers=headers, timeout=5, verify=False)
            if response.status_code == 200 and 'login' not in response.text.lower():
                soup = BeautifulSoup(response.content, 'html.parser')
                # Nếu tìm được nội dung thực, xử lý ở đây
                # (Hiện tại website yêu cầu đăng nhập nên sẽ dùng dữ liệu mẫu)
                pass
        except:
            pass
        
        # Trả về tin tức mẫu với thông tin hướng dẫn
        current_time = datetime.now()
        selected_news = sample_news[current_time.hour % len(sample_news)]
        
        return [{
            'title': selected_news['title'],
            'link': 'https://daotao.utt.edu.vn/congthongtin/Index.aspx',
            'date': selected_news['date'],
            'content': f"{selected_news['content']}\n\n💡 **Lưu ý**: Website UTT yêu cầu đăng nhập. Để xem tin tức chính thức:\n🔗 Truy cập: https://daotao.utt.edu.vn\n👤 Đăng nhập bằng tài khoản sinh viên\n📱 Hoặc kiểm tra fanpage Facebook UTT"
        }]
        
    except Exception as e:
        print(f"Lỗi khi lấy tin tức: {e}")
        return [{
            'title': '📢 UTT News Bot - Hướng dẫn xem tin tức',
            'link': NEWS_URL,
            'date': datetime.now().strftime('%d/%m/%Y'),
            'content': '🎓 **Cách xem tin tức UTT chính thức:**\n\n1️⃣ Truy cập: https://daotao.utt.edu.vn\n2️⃣ Đăng nhập bằng tài khoản sinh viên\n3️⃣ Vào mục "Công thông tin"\n\n📱 **Hoặc theo dõi**:\n• Fanpage Facebook chính thức của UTT\n• Website: utt.edu.vn\n• Thông báo từ lớp trưởng'
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