import streamlit as st
import anthropic
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import json

# Config
SPOTIFY_SCOPE = "user-top-read user-library-read"

def get_spotify_client():
    return spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id=st.secrets["SPOTIFY_CLIENT_ID"],
        client_secret=st.secrets["SPOTIFY_CLIENT_SECRET"],
        redirect_uri="http://127.0.0.1:8501",
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

def ask_claude(profile, city):
    client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
    
    prompt = f"""Tu es un expert en recommandations de lieux urbains.
    
Voici le profil musical d'un utilisateur :
- Artistes favoris : {', '.join(profile['artists'])}
- Genres : {', '.join(profile['genres'])}
- Titres récents : {', '.join(profile['tracks'][:5])}

Recommande 5 lieux à {city} qui correspondent parfaitement à ce profil musical.
Pour chaque lieu, réponds UNIQUEMENT en JSON valide avec ce format exact :

{{
  "lieux": [
    {{
      "nom": "Nom du lieu",
      "type": "bar/café/club/restaurant/etc",
      "ambiance": "description courte de l'ambiance",
      "pourquoi": "lien avec le profil musical en une phrase",
      "adresse": "adresse approximative"
    }}
  ]
}}"""

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )
    
    response_text = message.content[0].text
    # Nettoyer le JSON si besoin
    if "```json" in response_text:
        response_text = response_text.split("```json")[1].split("```")[0]
    elif "```" in response_text:
        response_text = response_text.split("```")[1].split("```")[0]
    
    return json.loads(response_text.strip())

# Interface Streamlit
st.set_page_config(page_title="Resonance", page_icon="🎵", layout="centered")

st.title("🎵 Resonance")
st.subheader("Découvre des lieux qui résonnent avec ta musique")

city = st.text_input("Dans quelle ville tu veux explorer ?", placeholder="Paris, Lyon, Berlin...")

if st.button("Connecte Spotify et explore", type="primary"):
    if not city:
        st.warning("Entre une ville d'abord !")
    else:
        try:
            with st.spinner("Connexion à Spotify..."):
                sp = get_spotify_client()
                profile = get_user_music_profile(sp)
            
            st.success("Profil musical récupéré !")
            
            with st.expander("Ton profil musical"):
                st.write("**Artistes :**", ", ".join(profile['artists']))
                st.write("**Genres :**", ", ".join(profile['genres']))
            
            with st.spinner("Claude analyse ton profil et cherche des lieux..."):
                result = ask_claude(profile, city)
            
            st.markdown(f"## 📍 5 lieux à {city} pour toi")
            
            for lieu in result['lieux']:
                with st.container():
                    st.markdown(f"### {lieu['nom']}")
                    col1, col2 = st.columns([1, 3])
                    with col1:
                        st.markdown(f"**{lieu['type'].upper()}**")
                    with col2:
                        st.markdown(f"📍 {lieu['adresse']}")
                    st.markdown(f"*{lieu['ambiance']}*")
                    st.markdown(f"🎵 {lieu['pourquoi']}")
                    st.divider()
                    
        except Exception as e:
            st.error(f"Erreur : {e}")