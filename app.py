import streamlit as st
import anthropic
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import json
import requests

# Config
SPOTIFY_SCOPE = "user-top-read user-library-read"

GRANDES_VILLES = {
    "paris", "london", "londres", "berlin", "new york", "new york city", "nyc",
    "barcelona", "barcelone", "madrid", "rome", "roma", "amsterdam", "vienna",
    "vienne", "prague", "budapest", "lisbon", "lisbonne", "tokyo", "osaka",
    "seoul", "séoul", "beijing", "shanghai", "sydney", "melbourne", "toronto",
    "montreal", "montréal", "chicago", "los angeles", "la", "miami", "milan",
    "florence", "firenze", "venice", "venise", "dublin", "brussels",
    "bruxelles", "zurich", "zürich", "copenhagen", "copenhague", "stockholm",
    "oslo", "helsinki", "warsaw", "varsovie", "bucharest", "bucarest",
    "lyon", "marseille", "bordeaux", "lille", "toulouse", "nantes", "strasbourg"
}

def is_grande_ville(city):
    return city.lower().strip() in GRANDES_VILLES

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

Génère un profil musical structuré pour ces artistes.
Réponds UNIQUEMENT en JSON valide :
{{
  "artists": ["artiste 1", "artiste 2"],
  "genres": ["genre 1", "genre 2"],
  "tracks": ["titre emblématique - artiste"]
}}

Pour les genres, déduis-les des artistes. Pour les tracks, cite 5 titres emblématiques de ces artistes."""

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

def get_search_queries(profile, city, grande_ville):
    client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])

    if grande_ville:
        niche_instruction = f"""
NIVEAU DE NOTORIÉTÉ VISÉ pour {city} — le sweet spot :
- Pas le top 20 TripAdvisor ni les monuments que tout touriste connaît
- Pas non plus les spots ultra-confidentiels que seul un critique de magazine connaît
- Vise les lieux que les habitants de {city} connaissent et fréquentent — connus des locaux, ignorés des touristes
- Des adresses qu'un Parisien dirait à un ami qui visite : "vas-y, c'est bien, c'est pas touristique"
- Inclus le nom d'un quartier précis dans chaque requête pour éviter les résultats génériques"""
    else:
        niche_instruction = """
- Varie les types de lieux : parcs, cinémas, librairies, marchés, cafés, bars, musées, espaces insolites
- Cherche des adresses authentiques qui correspondent à la sensibilité de l'utilisateur"""

    prompt = f"""Tu es un critique culturel et un fin connaisseur des villes.

Voici le profil musical d'un utilisateur :
- Artistes favoris : {', '.join(profile['artists'])}
- Genres : {', '.join(profile['genres'])}
- Titres récents : {', '.join(profile['tracks'][:5])}

ÉTAPE 1 — Analyse esthétique profonde.
Ne pense pas à la musique comme genre. Pense à ce qu'elle dit de la sensibilité de cette personne.
Extrait 3 à 5 valeurs esthétiques précises. Exemples : mélancolie douce, beauté abîmée, décalage poétique, énergie brute et collective, douceur introspective, nostalgie urbaine, tension entre légèreté et profondeur.

ÉTAPE 2 — Génère 8 requêtes de recherche Google Places pour {city}.
{niche_instruction}

Sois radical dans la diversité des types :
- Inclus : parcs, cimetières, cinémas de quartier, librairies, marchés, musées confidentiels, architectures particulières, cafés, espaces insolites, jardins, passages couverts, quais, brocantes, bars
- Chaque lieu doit pouvoir exister un mardi après-midi autant qu'un vendredi soir

Réponds UNIQUEMENT en JSON valide :
{{
  "valeurs_esthetiques": ["valeur 1", "valeur 2", "valeur 3"],
  "analyse": "2-3 phrases qui décrivent la sensibilité de cette personne au-delà de ses genres musicaux",
  "requetes": [
    {{
      "query": "requête Google Places précise",
      "type_lieu": "parc/cinéma/librairie/bar/café/musée/marché/etc",
      "vibe": "quelle valeur esthétique ce lieu incarne"
    }}
  ]
}}"""

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1200,
        messages=[{"role": "user", "content": prompt}]
    )
    
    response_text = message.content[0].text
    if "```json" in response_text:
        response_text = response_text.split("```json")[1].split("```")[0]
    elif "```" in response_text:
        response_text = response_text.split("```")[1].split("```")[0]
    
    return json.loads(response_text.strip())

def search_real_places(queries, city):
    api_key = st.secrets["GOOGLE_PLACES_API_KEY"]
    
    all_places = []
    seen_ids = set()
    
    for item in queries['requetes']:
        try:
            url = "https://places.googleapis.com/v1/places:searchText"
            headers = {
                "Content-Type": "application/json",
                "X-Goog-Api-Key": api_key,
                "X-Goog-FieldMask": "places.id,places.displayName,places.formattedAddress,places.rating,places.userRatingCount,places.types"
            }
            body = {
                "textQuery": f"{item['query']} {city}",
                "languageCode": "fr"
            }
            
            response = requests.post(url, headers=headers, json=body)
            results = response.json()
            
            for place in results.get('places', [])[:2]:
                place_id = place['id']
                if place_id not in seen_ids:
                    seen_ids.add(place_id)
                    all_places.append({
                        "nom": place.get('displayName', {}).get('text', ''),
                        "adresse": place.get('formattedAddress', ''),
                        "note": place.get('rating', 'N/A'),
                        "nb_avis": place.get('userRatingCount', 0),
                        "types": place.get('types', []),
                        "vibe_recherche": item['vibe'],
                        "type_lieu": item['type_lieu']
                    })
        except Exception as e:
            st.write(f"Erreur requête '{item['query']}': {e}")
            continue
    
    return all_places

def select_and_explain(profile, city, places, analyse, valeurs, grande_ville):
    client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
    
    places_text = json.dumps(places, ensure_ascii=False, indent=2)

    if grande_ville:
        niche_filter = f"""
NIVEAU DE NOTORIÉTÉ :
- Écarte les lieux qui font partie du top 20 touristique de {city}
- Mais garde des lieux que les habitants connaissent — pas besoin d'être ultra-confidentiel
- Le bon test : un habitant de {city} dirait "ah oui je connais, c'est bien" — pas "je n'en ai jamais entendu parler"
- Privilégie les lieux entre 200 et 5000 avis Google — assez établis pour être fiables, pas assez massifs pour être sur TripAdvisor page 1"""
    else:
        niche_filter = ""

    prompt = f"""Tu es un critique culturel qui écrit sur les villes.

Sensibilité de l'utilisateur :
- Artistes : {', '.join(profile['artists'])}
- Valeurs esthétiques extraites : {', '.join(valeurs)}
- Analyse : {analyse}

Voici une liste de vrais lieux trouvés à {city} :
{places_text}

{niche_filter}

Sélectionne les 5 lieux qui incarnent le mieux la sensibilité de cette personne.
Varie absolument les types : ne sélectionne pas 3 bars. Mélange les registres — un lieu de jour, un lieu de nuit, un lieu silencieux, un lieu vivant.

Parle du lieu comme un critique culturel, pas comme un guide touristique.
Le lien avec la musique doit être indirect et poétique, pas littéral.

Réponds UNIQUEMENT en JSON valide :
{{
  "lieux": [
    {{
      "nom": "nom exact du lieu",
      "adresse": "adresse exacte",
      "note": "note",
      "type_lieu": "type",
      "moment": "matin/après-midi/soir/nuit — quand y aller",
      "ambiance": "une phrase sèche et précise sur ce qu'on ressent là-bas",
      "pourquoi": "lien poétique et indirect entre ce lieu et la sensibilité musicale, 2-3 phrases"
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
st.subheader("Découvre des lieux qui résonnent avec ta sensibilité")

mode = st.radio(
    "Comment tu veux qu'on construise ton profil ?",
    ["🎧 Depuis mon Spotify", "✍️ Je donne mes artistes moi-même"],
    horizontal=True
)

city = st.text_input("Dans quelle ville tu veux explorer ?", placeholder="Paris, Lyon, Berlin...")

profile = None

if mode == "✍️ Je donne mes artistes moi-même":
    artists_input = st.text_input(
        "Tes artistes préférés en ce moment",
        placeholder="Beach House, Kanye West, Jul, Videoclub..."
    )
    
    if st.button("Explorer", type="primary"):
        if not city:
            st.warning("Entre une ville d'abord !")
        elif not artists_input:
            st.warning("Entre au moins un artiste !")
        else:
            try:
                with st.spinner("Construction du profil musical..."):
                    profile = build_manual_profile(artists_input)
                    grande_ville = is_grande_ville(city)
                    st.session_state['profile'] = profile
                    st.session_state['grande_ville'] = grande_ville
                    st.session_state['city'] = city

                with st.expander("Ton profil musical"):
                    st.write("**Artistes :**", ", ".join(profile['artists']))
                    st.write("**Genres déduits :**", ", ".join(profile['genres']))

            except Exception as e:
                st.error(f"Erreur : {e}")

else:
    if st.button("Connecte Spotify et explore", type="primary"):
        if not city:
            st.warning("Entre une ville d'abord !")
        else:
            try:
                with st.spinner("Connexion à Spotify..."):
                    sp = get_spotify_client()
                    profile = get_user_music_profile(sp)
                    grande_ville = is_grande_ville(city)
                    st.session_state['profile'] = profile
                    st.session_state['grande_ville'] = grande_ville
                    st.session_state['city'] = city

                with st.expander("Ton profil musical"):
                    st.write("**Artistes :**", ", ".join(profile['artists']))
                    st.write("**Genres :**", ", ".join(profile['genres']))

            except Exception as e:
                st.error(f"Erreur : {e}")

# Pipeline commun
if 'profile' in st.session_state and 'city' in st.session_state:
    profile = st.session_state['profile']
    grande_ville = st.session_state['grande_ville']
    city = st.session_state['city']
    
    try:
        with st.spinner("Analyse de ta sensibilité..."):
            search_data = get_search_queries(profile, city, grande_ville)
        
        with st.expander("Ta sensibilité esthétique"):
            st.write(search_data['analyse'])
            st.write("**Valeurs :**", " · ".join(search_data['valeurs_esthetiques']))
        
        with st.spinner(f"Recherche de lieux à {city}..."):
            real_places = search_real_places(search_data, city)
        
        if not real_places:
            st.error("Aucun lieu trouvé. Essaie une autre ville.")
        else:
            with st.spinner("Sélection des lieux qui te correspondent..."):
                result = select_and_explain(
                    profile, city, real_places,
                    search_data['analyse'],
                    search_data['valeurs_esthetiques'],
                    grande_ville
                )
            
            st.markdown(f"## 📍 {city}")
            
            for lieu in result['lieux']:
                with st.container():
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"### {lieu['nom']}")
                    with col2:
                        st.markdown(f"*{lieu.get('moment', '')}*")
                    
                    st.markdown(f"📍 {lieu['adresse']}")
                    if lieu['note'] != 'N/A':
                        st.markdown(f"⭐ {lieu['note']}")
                    st.markdown(f"*{lieu['ambiance']}*")
                    st.markdown(f"{lieu['pourquoi']}")
                    st.divider()

        del st.session_state['profile']
        del st.session_state['grande_ville']
        del st.session_state['city']

    except Exception as e:
        st.error(f"Erreur : {e}")