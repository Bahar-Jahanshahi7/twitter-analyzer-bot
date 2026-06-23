import os
import asyncio
import xml.etree.ElementTree as ET
import urllib.request
import urllib.parse
import html
from telegram import Bot

TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

# لیست اکانت‌ها و کلمات کلیدی شما
TWITTER_ACCOUNTS = ['elonmusk', 'Binance', 'VitalikButerin']
KEYWORDS = ['crypto', 'bitcoin', 'btc', 'eth', 'launch', 'tesla', 'ai']

bot = Bot(token=TELEGRAM_BOT_TOKEN)

async def main_pipeline():
    print("Checking tweets via Google News RSS Pipeline...")
    
    for account in TWITTER_ACCOUNTS:
        try:
            query = f'from:{account} site:twitter.com OR site:x.com'
            encoded_query = urllib.parse.quote(query)
            rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
            
            req = urllib.request.Request(rss_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response:
                xml_data = response.read()
            
            root = ET.fromstring(xml_data)
            items = root.findall('.//item')[:3]
            
            if not items:
                print(f"No recent indexed tweets found for @{account} on Google News right now.")
                continue

            for item in items:
                title = item.find('title').text if item.find('title') is not None else ""
                tweet_link = item.find('link').text if item.find('link') is not None else ""
                
                tweet_text = title.split(' - ')[0] if ' - ' in title else title
                
                contains_keyword = any(keyword.lower() in tweet_text.lower() for keyword in KEYWORDS)
                
                if contains_keyword:
                    # استفاده از HTML برای فرار از ارور کاراکترهای خاص تلگرام
                    safe_tweet_text = html.escape(tweet_text)
                    
                    final_message = (
                        f"🔔 <b>توییت جدید از: @{account}</b>\n\n"
                        f"📝 <b>متن توییت:</b>\n{safe_tweet_text}\n\n"
                        f"🔗 <a href='{tweet_link}'>لینک منبع</a>"
                    )
                    
                    try:
                        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=final_message, parse_mode="HTML")
                        print(f"Message sent for @{account} successfully!")
                    except Exception as tg_err:
                        print(f"Error sending Telegram: {tg_err}")
                        
        except Exception as e:
            print(f"Error checking @{account}: {e}")

if __name__ == "__main__":
    # اجرای کل پروسه
    asyncio.run(main_pipeline())
