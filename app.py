import streamlit as st
import anthropic
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import json
import googlemaps

# Config
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

def get_search_queries(profile, city):
    """Étape 1 : Claude analyse le profil et génère des requêtes de recherche"""
    client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
    
    prompt = f"""Tu es un expert en culture urbaine et en recommandations de lieux.

Voici le profil musical d'un utilisateur :
- Artistes favoris : {', '.join(profile['artists'])}
- Genres : {', '.join(profile['genres'])}
- Titres récents : {', '.join(profile['tracks'][:5])}

Analyse ce profil musical en profondeur et génère 8 requêtes de recherche Google Places pour trouver des lieux à {city} qui correspondent à l'identité culturelle de cet utilisateur.

Les requêtes doivent être variées (bars, cafés, clubs, restaurants, salles de concert...) et refléter précisément le vibe musical.

Réponds UNIQUEMENT en JSON valide :
{{
  "analyse": "2-3 phrases sur l'identité culturelle derrière ce profil musical",
  "requetes": [
    {{
      "query": "requête de recherche en français ou anglais",
      "type_lieu": "bar/café/club/restaurant/concert",
      "vibe": "description courte du vibe recherché"
    }}
  ]
}}"""

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )
    
    response_text = message.content[0].text
    if "```json" in response_text:
        response_text = response_text.split("```json")[1].split("```")[0]
    elif "```" in response_text:
        response_text = response_text.split("```")[1].split("```")[0]
    
    return json.loads(response_text.strip())

def search_real_places(queries, city):
    """Étape 2 : Google Places trouve les vrais lieux"""
    gmaps = googlemaps.Client(key=st.secrets["GOOGLE_PLACES_API_KEY"])
    
    all_places = []
    seen_ids = set()
    
    for item in queries['requetes']:
        try:
            results = gmaps.places(
                query=f"{item['query']} {city}",
                language="fr"
            )
            
            for place in results.get('results', [])[:2]:
                place_id = place['place_id']
                if place_id not in seen_ids:
                    seen_ids.add(place_id)
                    all_places.append({
                        "nom": place['name'],
                        "adresse": place.get('formatted_address', ''),
                        "note": place.get('rating', 'N/A'),
                        "nb_avis": place.get('user_ratings_total', 0),
                        "types": place.get('types', []),
                        "vibe_recherche": item['vibe'],
                        "type_lieu": item['type_lieu']
                    })
        except Exception:
            continue
    
    return all_places

def select_and_explain(profile, city, places, analyse):
    """Étape 3 : Claude choisit parmi les vrais lieux et explique"""
    client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
    
    places_text = json.dumps(places, ensure_ascii=False, indent=2)
    
    prompt = f"""Tu es un expert en culture urbaine.

Profil musical de l'utilisateur :
- Artistes : {', '.join(profile['artists'])}
- Genres : {', '.join(profile['genres'])}
- Analyse : {analyse}

Voici une liste de vrais lieux trouvés à {city} :
{places_text}

Sélectionne les 5 meilleurs lieux de cette liste qui correspondent le mieux au profil musical.
Pour chaque lieu choisi, explique le lien précis entre ce lieu et l'identité musicale de l'utilisateur.

Réponds UNIQUEMENT en JSON valide :
{{
  "lieux": [
    {{
      "nom": "nom exact du lieu tel qu'il apparaît dans la liste",
      "adresse": "adresse exacte telle qu'elle apparaît dans la liste",
      "note": "note telle qu'elle apparaît dans la liste",
      "type_lieu": "type du lieu",
      "ambiance": "description courte et précise de l'ambiance",
      "pourquoi": "lien spécifique et personnel avec le profil musical en 1-2 phrases"
    }}
  ]
}}"""

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}]
    )
    
    response_text = message.content[0].text
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
            
            with st.spinner("Claude analyse ton profil musical..."):
                search_data = get_search_queries(profile, city)
            
            with st.expander("Analyse de ton identité musicale"):
                st.write(search_data['analyse'])
            
            with st.spinner(f"Recherche de vrais lieux à {city}..."):
                real_places = search_real_places(search_data, city)
            
            if not real_places:
                st.error("Aucun lieu trouvé. Essaie une autre ville.")
            else:
                with st.spinner("Claude sélectionne les meilleurs lieux pour toi..."):
                    result = select_and_explain(profile, city, real_places, search_data['analyse'])
                
                st.markdown(f"## 📍 5 lieux à {city} pour toi")
                
                for lieu in result['lieux']:
                    with st.container():
                        st.markdown(f"### {lieu['nom']}")
                        col1, col2 = st.columns([1, 3])
                        with col1:
                            st.markdown(f"**{lieu['type_lieu'].upper()}**")
                            if lieu['note'] != 'N/A':
                                st.markdown(f"⭐ {lieu['note']}")
                        with col2:
                            st.markdown(f"📍 {lieu['adresse']}")
                        st.markdown(f"*{lieu['ambiance']}*")
                        st.markdown(f"🎵 {lieu['pourquoi']}")
                        st.divider()
                        
        except Exception as e:
            st.error(f"Erreur : {e}")