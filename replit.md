# UTT News Bot

## Project Overview
Discord bot that automatically scrapes news and announcements from the University of Transport and Technology (UTT) website and posts them to a designated Discord channel.

## Current Status
- ✅ Bot successfully connected to Discord as UTT-Announcer#3441
- ✅ Flask keepalive server running on port 5000
- ✅ Environment secrets configured (DISCORD_BOT_TOKEN, DISCORD_CHANNEL_ID)
- ✅ Monitoring news every 5 minutes

## Project Architecture
- **main.py**: Main bot file with Discord client and Flask server
- **Flask Server**: Runs on port 5000 to keep the Repl alive
- **Discord Bot**: Monitors UTT news and posts updates to Discord channel
- **News Source**: https://daotao.utt.edu.vn/congthongtin/Index.aspx

## Features
- Automatic news checking every 5 minutes
- Discord embed formatting for news posts
- Flask web interface showing bot status
- Error handling and logging

## Recent Changes (September 7, 2025)
- Set up complete Discord bot project
- Configured environment secrets
- Established Flask keepalive server
- Bot successfully connected to Discord

## Dependencies
- discord.py==2.3.2
- requests==2.31.0
- beautifulsoup4==4.12.2
- flask==2.3.3