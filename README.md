[![Auto Post Packager](https://github.com/nima-htm/SomeLandForMen-Bot/actions/workflows/cron.yml/badge.svg)](https://github.com/nima-htm/SomeLandForMen-Bot/actions/workflows/cron.yml)

# Some Land For Men Telegram Bot 🤖
An automated Python bot that scrapes tech, open-source, and Linux RSS feeds, intelligently summarizes and critiques the articles using a resilient multi-layer AI framework, and publishes them to a Telegram channel.

It runs efficiently on GitHub Actions with built-in human-like behavior simulation.

## Features

- **RSS Scraper**: Automatically tracks and parses top tech feeds (Phoronix, Ars Technica, Hacker News, etc.) while maintaining a history to prevent duplicate posts.
- **5-Layer AI Resiliency**: Avoids API rate limits or downtime by cascading through multiple fallback layers:
  1. Gemini 2.5 Flash (Direct API)
  2. Kimi K2.6 (OpenRouter Free)
  3. Llama 3.3 70B (OpenRouter Free)
  4. Qwen 2.5 72B (Hugging Face Serverless)
  5. Mixtral 8x7B (Hugging Face Serverless)
- **Human Behavior Simulation**: Operates on a smart Cron schedule combined with a randomized execution delay (30s to 10m) to mimic natural human administration.
- **HTML Safety**: Automatically falls back to plain text if Telegram throws an HTML parse error.

## Setup Environment
Clone the project and setup environment varibales like this:
```text
SomeLandforMen-Bot
└── .env
```

You must setup 4 environment varibales:
```text
TELEGRAM_TOKEN = "YOUR_BOTFATHER_TOKEN"
GEMINI_API_KEY = "YOUR_GOOGLE_AI_TOKEN"
OPENROUTER_API_KEY = "YOUR_OPEN_ROUTER_KEY"
HF_TOKEN = "YOUR_HUGGING_FACE_KEY"
```

Feel free to fork and star if you liked this project 🩷
