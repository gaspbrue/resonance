# Resonance

Resonance connects your Spotify listening history to places worth visiting. Enter a city and the app analyzes your top artists and genres to recommend spots that match your taste. Not tourist lists, but places that fit your musical identity.

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://gaspbrue-resonance-app.streamlit.app)

---

## How it works

The app fetches your real Spotify data (top artists, genres, recent tracks) and sends that profile to Claude. The prompt asks Claude to reason about your cultural identity before recommending anything, and each recommendation includes an explicit link between your music and the place. Tourist clichés are explicitly excluded unless they genuinely fit the profile.

---

## Stack

Spotify API for music data (OAuth Authorization Code flow), Anthropic Claude for the recommendations, Streamlit for the interface, deployed on Streamlit Cloud.

---

## Run locally

Clone the repo, create a virtual environment, install dependencies with `pip install -r requirements.txt`, and add a `.streamlit/secrets.toml` file with your Spotify credentials, Anthropic API key, and redirect URI. Then run `streamlit run app.py`.

---

*Built in 2026.*