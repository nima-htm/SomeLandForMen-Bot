import os
import random
import requests
import feedparser
from bs4 import BeautifulSoup
from google import genai
from dotenv import load_dotenv
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHANNEL_ID = "@someLandForMen"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
openrouter_url = "https://openrouter.ai/api/v1/chat/completions"

HISTORY_FILE = 'urls_history.txt'


def load_history():

    if not os.path.exists(HISTORY_FILE):
        return set()
    with open(HISTORY_FILE, 'r') as f:
        return set(line.strip() for line in f if line.strip())


def save_to_history(url):

    with open(HISTORY_FILE, 'a') as f:
        f.write(f"{url}\n")


def main():

    if random.random() > 0.5:
        print("")
        return

    try:
        SOURCES = [
            {"name": "OMg! Ubuntu", "url": "https://feeds.feedburner.com/d0od"},
            {"name": "Phoronix (Linux Hardware & Kernel)", "url": "https://www.phoronix.com/phoronix-rss.php"},
            {"name": "Linux Today", "url": "https://www.linuxtoday.com/feed/"},
            {"name": "Hacker News (Top Stories)", "url": "https://news.ycombinator.com/rss"},
            {"name": "The Next Web (Tech)", "url": "https://thenextweb.com/feed"},
            {"name": "InfoQ (Software Development)", "url": "https://feed.infoq.com/"},
            {"name": "Ars Technica (Software & Sci)", "url": "https://feeds.arstechnica.com/arstechnica/index"}
        ]


        selected_source = random.choice(SOURCES)
        print(f"Scraping from: {selected_source['name']}...")

        feed = feedparser.parse(selected_source['url'])

        if not feed.entries:
            print(f"Err: No articles found in {selected_source['name']}")
            return


        first_entry = feed.entries[0]

        title = first_entry.title
        summary_text = first_entry.summary if 'summary' in first_entry else first_entry.description
        article_url = first_entry.link

        # پاک‌سازی تگ‌های HTML احتمالی در خلاصه RSS
        from bs4 import BeautifulSoup
        clean_summary = BeautifulSoup(summary_text, "html.parser").get_text()

        raw_content = f"Source Site: {selected_source['name']}\nTitle: {title}\n\nContent/Summary: {clean_summary}"
        print(f"✅ Article found: {title}")

        # خواندن پرامپت از prompt.txt
        PROMPT_FILE = 'prompt.txt'
        if os.path.exists(PROMPT_FILE):
            with open(PROMPT_FILE, 'r', encoding='utf-8') as f:
                system_prompt = f.read().strip()
        else:
            system_prompt = "تو یک ژورنالیست علمی برای کانال تلگرام هستی."

        # ۵. ارسال متن به API رسمی گوگل با استفاده از SDK
        print("Send data to Gemini...")


        client = genai.Client(api_key=GEMINI_API_KEY)
        full_instruction = f"{system_prompt}\n\nمتن علمی برای خلاصه‌سازی:\n{raw_content}"


        MAX_RETRIES = 4
        retry_delay = 3
        final_post = None

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=full_instruction
                )
                final_post = response.text
                print("✅ Raw response from Gemini catched.")
                break
            except Exception as e:
                print(f"⚠️ Attempt {attempt} failed with error: {str(e)}")
                if attempt < MAX_RETRIES:
                    import time
                    print(f"Waiting {retry_delay} seconds before retrying...")
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    print("❌ All retry attempts failed for Gemini.")
                    return



        print("Sending to Telegram...")
        telegram_url = f"https://api.telegram.org/{TELEGRAM_TOKEN}/sendMessage"
        telegram_data = {
            "chat_id": CHANNEL_ID,
            "text": final_post,
            "parse_mode": "Markdown"
        }

        telegram_res = requests.post(telegram_url, json=telegram_data, timeout=15)

        if telegram_res.status_code == 200:
            print("Post sent!")

            save_to_history(article_url)
        else:
            print(f"Err sending to Telegram: {telegram_res.text}")

    except Exception as e:
        print(f"Fatal unknown err: {str(e)}")


if __name__ == "__main__":
    main()