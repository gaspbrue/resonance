import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import anthropic
import json

SPOTIFY_SCOPE = "user-top-read user-library-read"


def get_spotify_client():
    return spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id=st.secrets["SPOTIFY_CLIENT_ID"],
        client_secret=st.secrets["SPOTIFY_CLIENT_SECRET"],
        redirect_uri=st.secrets["REDIRECT_URI"],
        scope=SPOTIFY_SCOPE
    ))


def get_user_music_profile(sp):
    top_tracks = sp.current_user_top_tracks(limit=10, time_range="medium_term")
    top_artists = sp.current_user_top_artists(limit=5, time_range="medium_term")

    tracks = [f"{t['name']} - {t['artists'][0]['name']}" for t in top_tracks['items']]
    artists = [a['name'] for a in top_artists['items']]

    genres = []
    for artist in top_artists['items']:
        if artist.get('genres'):
            genres.extend(artist['genres'][:2])
    genres = list(set(genres))[:8] if genres else ["variété", "pop"]

    return {"tracks": tracks, "artists": artists, "genres": genres}


def build_manual_profile(artists_input):
    client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])

    prompt = f"""Tu es un expert en musique.
L'utilisateur a listé ces artistes qu'il aime : {artists_input}

Génère un profil musical structuré. Réponds UNIQUEMENT en JSON valide :
{{
  "artists": ["artiste 1", "artiste 2"],
  "genres": ["genre 1", "genre 2"],
  "tracks": ["titre - artiste"]
}}
Pour les genres, déduis-les des artistes. Pour les tracks, cite 5 titres emblématiques."""

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}]
    )

    response_text = message.content[0].text
    if "```json" in response_text:
        response_text = response_text.split("```json")[1].split("```")[0]
    elif "```" in response_text:
        response_text = response_text.split("```")[1].split("```")[0]

    return json.loads(response_text.strip())
