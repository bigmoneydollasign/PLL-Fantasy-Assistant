# 🥍 PLL Fantasy Assistant

A Streamlit web app that answers **Premier Lacrosse League fantasy questions** using real 2025 player data from the official PLL website.

This assistant analyzes player performance across:

* Regular Season
* Postseason
* Champ Series

and provides **start/sit advice, rankings, comparisons, and insights** using an OpenAI model.

---

## 🚀 Features

* Ask natural language PLL fantasy questions
* Uses real 2025 PLL player stats pulled from the official PLL website
* Combines multiple competition stages intelligently
* Provides:

  * Start/sit recommendations
  * Player comparisons
  * Position rankings
  * Value picks and sleepers
* Clean Streamlit interface
* Deployable to Streamlit Community Cloud

---

## 📂 Project Structure

```
pll-fantasy-assistant/
│
├── app.py                          # Streamlit frontend
├── pll_assistant.py               # Backend logic + AI integration
├── pll-player-stats-regular.csv   # 2025 regular season data
├── pll-player-stats-post.csv      # 2025 postseason data
├── pll-player-stats-champ.csv     # 2025 champ series data
├── requirements.txt
├── README.md
└── .gitignore
```

---

## ⚙️ Installation

1. Clone the repository:

```bash
git clone https://github.com/YOUR_USERNAME/PLL-Fantasy-Assistant.git
cd PLL-Fantasy-Assistant
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

---

## 🔑 API Key Setup

This project uses OpenAI for generating fantasy insights.

### 🔹 Local Development

Create a `.env` file:

```
OPENAI_API_KEY=your_api_key_here
```
⚠️ **Do not commit these files to GitHub**

---

### 🔹 Streamlit Cloud Deployment

1. Go to **App Settings → Secrets**
2. Add:

```toml
OPENAI_API_KEY = "your_api_key_here"
```

---

## ▶️ Running the App

```bash
streamlit run app.py
```

---

## 💬 Example Questions

* Based on 2025 performance, who are the best PLL fantasy players to start?
* Who are the best attackmen in PLL fantasy?
* Compare the top PLL goalies.
* Which midfielders have the best floor vs upside?
* Who are the best faceoff specialists for fantasy?
* Give me 10 undervalued PLL players.

---

## 🧠 How It Works

1. Loads 2025 PLL datasets
2. Combines all competition stages
3. Computes fantasy-style scoring
4. Formats structured player data
5. Sends context + question to OpenAI
6. Returns a clean, readable answer

---

## 📊 Data Notes

* Regular season = primary signal
* Postseason = supporting context
* Champ Series = additional context

All answers are based on **2025 data only**

---

## ⚠️ Important Notes

* Do NOT upload `.env` or `secrets.toml`
* The app requires an OpenAI API key to function
* Performance depends on dataset size and prompt length

---

## 🌐 Deployment

This app is designed for:

👉 **Streamlit Community Cloud**

Steps:

1. Push repo to GitHub
2. Connect repo on Streamlit Cloud
3. Set `app.py` as main file
4. Add secrets
5. Deploy

---

## 🛠 Tech Stack

* Python
* Streamlit
* Pandas
* OpenAI API

---

## 📜 License

MIT License

---

## 🙌 Acknowledgements

* Premier Lacrosse League (PLL)
* Streamlit
* OpenAI

---

## Streamlit App

https://pllfantasyassistant.streamlit.app/
* Try it out for yourself!

---

## Author

* Made by Jalen Layog

