# 🎵 Resonance

> Discover places that resonate with your music taste, powered by Spotify + Claude AI.

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://resonance-bugnvflidjkkn3ykwbevu6.streamlit.app/)

---

## What it does

Connect your Spotify account and choose a city. Resonance analyzes your top artists and genres, then uses Claude AI to recommend 5 places that match your musical identity. Not generic tourist spots, but places that actually fit your vibe.

**Example:** If you listen to Beach House, Videoclub and Jul, you'll get a mix of intimate indie venues, eclectic cultural bars and laid-back local spots, not the Eiffel Tower.

---

## Stack

| Layer | Tech |
|---|---|
| Music data | Spotify API (OAuth) |
| AI recommendations | Anthropic Claude API |
| Interface | Streamlit |
| Deployment | Streamlit Cloud |

---

## Run locally

```bash
git clone https://github.com/gaspbrue/resonance
cd resonance
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Create a `.streamlit/secrets.toml` file with:
```toml
SPOTIFY_CLIENT_ID = "..."
SPOTIFY_CLIENT_SECRET = "..."
ANTHROPIC_API_KEY = "..."
REDIRECT_URI = "http://127.0.0.1:8501"
```

---


## Docker

Run the app with Docker:

docker pull gaspardbrue/resonance


---


## Key technical decisions

**Spotify OAuth** uses the Authorization Code flow to access the user's real listening history (top artists, genres, recent tracks) without storing any credentials.

**Prompt engineering** sends the raw Spotify profile to Claude and instructs it to reason about the cultural identity behind the music before recommending places. The link between the music and each place is always made explicit.

**No generic recommendations** the prompt explicitly forbids tourist clichés unless they genuinely fit the profile.

---

*Built in 2026.*