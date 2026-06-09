import os
import random
import requests
import feedparser
from bs4 import BeautifulSoup
from google import genai
from dotenv import load_dotenv
import time

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHANNEL_ID = "@Bit_Quote"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
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


def process_single_post(history):
    SOURCES = [
        {"name": "OMg! Ubuntu", "url": "https://feeds.feedburner.com/d0od"},
        {"name": "Phoronix (Linux Hardware & Kernel)", "url": "https://www.phoronix.com/phoronix-rss.php"},
        {"name": "Linux Today", "url": "https://www.linuxtoday.com/feed/"},
        {"name": "Hacker News (Top Stories)", "url": "https://news.ycombinator.com/rss"},
        {"name": "The Next Web (Tech)", "url": "https://thenextweb.com/feed"},
        {"name": "InfoQ (Software Development)", "url": "https://feed.infoq.com/"},
        {"name": "Ars Technica (Software & Sci)", "url": "https://feeds.arstechnica.com/arstechnica/index"}
    ]

    random.shuffle(SOURCES)
    target_entry = None
    selected_source = None

    for source in SOURCES:
        print(f"Scraping from: {source['name']}...")
        feed = feedparser.parse(source['url'])
        if not feed.entries:
            continue

        for entry in feed.entries:
            if entry.link not in history:
                target_entry = entry
                selected_source = source
                break
        if target_entry:
            break

    if not target_entry:
        print("⚠️ No new articles found across all sources.")
        return False

    title = target_entry.title
    summary_text = target_entry.summary if 'summary' in target_entry else target_entry.description
    article_url = target_entry.link

    clean_summary = BeautifulSoup(summary_text, "html.parser").get_text()
    raw_content = f"Source Site: {selected_source['name']}\nTitle: {title}\n\nContent/Summary: {clean_summary}"
    print(f"✅ Article found: {title}")

    PROMPT_FILE = 'prompt.txt'
    if os.path.exists(PROMPT_FILE):
        with open(PROMPT_FILE, 'r', encoding='utf-8') as f:
            system_prompt = f.read().strip()
    else:
        system_prompt = "تو یک ژورنالیست علمی برای کانال تلگرام هستی."

    full_instruction = f"{system_prompt}\n\nمتن علمی برای خلاصه‌سازی:\n{raw_content}"
    final_post = None

    print("🤖 Trying Layer 1: Gemini 2.5 Flash...")
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=full_instruction
        )
        final_post = response.text
        print("✅ Successfully generated using Gemini!")
    except Exception as gemini_err:
        print(f"⚠️ Gemini Failed: {str(gemini_err)}")

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com"
    }

    if not final_post:
        print("🤖 Trying Layer 2: Kimi K2.6...")
        data = {
            "model": "moonshotai/kimi-k2.6:free",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": full_instruction}
            ],
            "temperature": 0.7
        }

        MAX_RETRIES = 3
        retry_delay = 5
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                res = requests.post(openrouter_url, json=data, headers=headers, timeout=25)
                if res.status_code == 429:
                    raise Exception("Rate limited")
                if res.status_code == 200:
                    final_post = res.json()['choices'][0]['message']['content']
                    print("✅ Successfully generated using Kimi!")
                    break
                else:
                    raise Exception(f"Status {res.status_code}")
            except Exception as e:
                print(f"⚠️ Kimi attempt {attempt} failed: {str(e)}")
                if attempt < MAX_RETRIES:
                    time.sleep(retry_delay)
                    retry_delay *= 2

    HF_TOKEN = os.getenv("HF_TOKEN")


    if not final_post and HF_TOKEN:
        print("🤖 Trying Layer 4: Qwen 2.5 72B (Hugging Face Serverless)...")
        hf_url = "https://api-inference.huggingface.co/models/Qwen/Qwen2.5-72B-Instruct"
        hf_headers = {"Authorization": f"Bearer {HF_TOKEN}"}

        formatted_prompt = f"<|im_start|>system\n{system_prompt}<|im_end|>\n<|im_start|>user\n{full_instruction}<|im_end|>\n<|im_start|>assistant\n"
        hf_payload = {
            "inputs": formatted_prompt,
            "parameters": {"max_new_tokens": 1024, "temperature": 0.7}
        }

        try:
            res = requests.post(hf_url, json=hf_payload, headers=hf_headers, timeout=30)
            if res.status_code == 200:
                raw_out = res.json()[0]['generated_text']
                # پاک کردن کانتکست ورودی از متن تولید شده
                final_post = raw_out.replace(formatted_prompt, "").strip()
                print("✅ Successfully generated using Hugging Face Qwen!")
            else:
                print(f"⚠️ HF Qwen returned status {res.status_code}: {res.text}")
        except Exception as hf_err:
            print(f"⚠️ Hugging Face Layer 4 Failed: {str(hf_err)}")


    if not final_post and HF_TOKEN:
        print("🤖 Trying Layer 5: Mixtral 8x7B (Hugging Face Serverless)...")
        hf_url = "https://api-inference.huggingface.co/models/mistralai/Mixtral-8x7B-Instruct-v0.1"
        hf_headers = {"Authorization": f"Bearer {HF_TOKEN}"}

        formatted_prompt = f"<s>[INST] {system_prompt}\n\n{full_instruction} [/INST]"
        hf_payload = {
            "inputs": formatted_prompt,
            "parameters": {"max_new_tokens": 1024, "temperature": 0.7}
        }

        try:
            res = requests.post(hf_url, json=hf_payload, headers=hf_headers, timeout=30)
            if res.status_code == 200:
                raw_out = res.json()[0]['generated_text']
                final_post = raw_out.replace(formatted_prompt, "").strip()
                print("✅ Successfully generated using Hugging Face Mixtral!")
            else:
                print(f"⚠️ HF Mixtral returned status {res.status_code}")
        except Exception as hf_err:
            print(f"⚠️ Hugging Face Layer 5 Failed: {str(hf_err)}")


    if not final_post:
        print("🤖 Trying Layer 3: Llama 3.3 70B...")
        data = {
            "model": "meta-llama/llama-3.3-70b-instruct:free",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": full_instruction}
            ],
            "temperature": 0.7
        }
        try:
            res = requests.post(openrouter_url, json=data, headers=headers, timeout=25)
            if res.status_code == 200:
                final_post = res.json()['choices'][0]['message']['content']
                print("✅ Successfully generated using Llama 3.3!")
            else:
                print(f"⚠️ Llama 3.3 returned status {res.status_code}")
        except Exception as llama_err:
            print(f"⚠️ Llama 3.3 Failed: {str(llama_err)}")

    if not final_post:
        print("❌ All AI models failed to generate content.")
        return False

    print("Sending to Telegram...")
    telegram_url = f"https://api.telegram.org/{TELEGRAM_TOKEN}/sendMessage"
    telegram_data = {"chat_id": CHANNEL_ID, "text": final_post, "parse_mode": "HTML"}

    telegram_res = requests.post(telegram_url, json=telegram_data, timeout=15)

    if telegram_res.status_code == 400 and "parse entities" in telegram_res.text:
        print("⚠️ Telegram HTML parse error. Retrying as plain text...")
        telegram_data.pop("parse_mode", None)
        telegram_res = requests.post(telegram_url, json=telegram_data, timeout=15)

    if telegram_res.status_code == 200:
        print("Post sent successfully!")
        save_to_history(article_url)
        history.add(article_url)
        return True
    else:
        print(f"Err sending to Telegram: {telegram_res.text}")
        return False


def main():


    try:
        POSTS_PER_RUN = 1
        DELAY_BETWEEN_POSTS = 7200
        current_history = load_history()

        for i in range(POSTS_PER_RUN):
            print(f"\n--- Packaged Post Execution {i + 1}/{POSTS_PER_RUN} ---")
            success = process_single_post(current_history)

            if i < POSTS_PER_RUN - 1 and success:
                print(f"💤 Sleeping for {DELAY_BETWEEN_POSTS} seconds (2 hours) before next post...")
                time.sleep(DELAY_BETWEEN_POSTS)

    except Exception as e:
        print(f"Fatal unknown err: {str(e)}")


if __name__ == "__main__":
    main()