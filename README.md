# Friendly Telegram Chat Bot 🤖💬

A Telegram bot with:
- ✅ Human verification (simple math captcha via buttons)
- 👋 Friendly welcome message
- 💬 Casual, emoji-friendly AI chat powered by OpenRouter

---

## 1. Rotate your keys first ⚠️

You shared a live bot token and API key earlier — treat both as compromised.

- **Telegram:** message [@BotFather](https://t.me/BotFather) → `/revoke` on the old token, get a new one.
- **OpenRouter:** go to your OpenRouter dashboard → API Keys → delete the old key → create a new one.

Never paste real keys into chat or commit them to GitHub. This project reads them from environment variables instead.

---

## 2. Local testing

```bash
git clone <your-repo-url>
cd telegram-bot
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# then edit .env and paste your NEW bot token + API key
```

Load the `.env` file before running (or use a tool like `python-dotenv` if you want it automatic), then:

```bash
python bot.py
```

Open Telegram, find your bot, send `/start`.

---

## 3. Push to GitHub

```bash
git init
git add .
git commit -m "Initial commit: telegram chat bot"
git branch -M main
git remote add origin https://github.com/<your-username>/<your-repo>.git
git push -u origin main
```

`.gitignore` already excludes `.env`, so your real secrets won't be pushed. Good — keep it that way.

---

## 4. Deploy on Choreo.dev

1. Log in to [Choreo](https://console.choreo.dev/) and create a new **Component** → choose **Service** (or "Scheduled/Background" type if offered — this bot runs continuously via polling, so a long-running service component fits best).
2. Connect your GitHub repo and select this project's branch.
3. Choreo will detect it as a Python app via `requirements.txt`. Set the **start command** to:
   ```
   python bot.py
   ```
4. In the Choreo dashboard, go to **Configs & Secrets** and add:
   - `BOT_TOKEN` = your new Telegram bot token
   - `OPENROUTER_API_KEY` = your new OpenRouter key
   - `OPENROUTER_MODEL` = `openai/gpt-4o-mini` (or any model you prefer)
5. Deploy. Choreo will build and run the service — since it's polling Telegram (not waiting for inbound HTTP), it just needs to stay alive, no public URL required.
6. Check the build/runtime logs in Choreo to confirm you see `Bot starting...` with no errors.

---

## How it works

- `/start` → shows a welcome message + a 2-number addition captcha as buttons.
- Tapping the correct answer marks the user "verified" (in memory — resets if the bot restarts; swap in a real database for persistence).
- Once verified, any message the user sends gets a friendly AI-generated reply via OpenRouter, with a casual tone and emoji baked into the system prompt.
- Basic greetings (hi/hello/hey) get an instant canned friendly reply without needing an AI call.

## Notes on "24/7"

No free tier guarantees literal 100% uptime forever — but Choreo's free tier will keep a long-running service like this alive continuously. Keep an eye on Choreo's usage limits/dashboard if you're on a free plan, since limits can change.
