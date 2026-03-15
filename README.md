# Twi Text Collector

Collect Twi text generated via Gemini from English news paragraphs.

---

## Requirements

- Python 3.8+
- Internet connection

**Install dependencies:**
```bash
pip install huggingface_hub pandas
```

**Linux only:**
```bash
sudo apt install python3-tk xclip wl-clipboard
```

---

## Setup

```bash
git clone https://github.com/GhanaNLP/twi-text-collector.git
cd twi-text-collector
pip install huggingface_hub pandas
python collector.py
```

Paste your volunteer code when prompted and click **"Download & Start →"**.

---

## How it works

1. App shows one English news paragraph at a time
2. Click **"✦ Gemini Prompt"** → paste into [gemini.google.com](https://gemini.google.com) → send
3. Copy Gemini's Twi response → paste into the app textarea
4. App validates length (~2000 words expected for 4-part text)
5. Click **"Save & Next →"** — auto-saves and moves to next paragraph
6. Every 10 texts are automatically uploaded to HuggingFace

---

## Tips

- If Gemini's output is too short/long, try regenerating or enable **Thinking Mode**
- Click **"Skip ⇥"** if you can't get valid output after several tries
- Click **"⬆ Push Now"** to manually upload before reaching 10 texts
- Your progress is saved — restart anytime and it will resume where you left off

---

## Troubleshooting

**Download fails**
Re-run `python collector.py` with your code — already downloaded data is cached.

**Push fails**
App will retry automatically on next save. Click **"⬆ Push Now"** once connection is restored.

**App won't open (Linux)**
Install: `sudo apt install python3-tk`

**Lost your code**
Contact the project coordinator.
