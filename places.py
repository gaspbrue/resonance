import streamlit as st
import anthropic
import requests
import json

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


def get_search_queries(profile, city, grande_ville):
    client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])

    if grande_ville:
        niche_instruction = f"""
NIVEAU DE NOTORIÉTÉ VISÉ pour {city} :
- Pas le top 20 TripAdvisor ni les monuments que tout touriste connaît
- Vise les lieux que les habitants connaissent et fréquentent — connus des locaux, ignorés des touristes
- Des adresses qu'un habitant dirait à un ami : "vas-y, c'est bien, c'est pas touristique"
- Inclus le nom d'un quartier précis dans chaque requête"""
    else:
        niche_instruction = """
- Varie les types : parcs, cinémas, librairies, marchés, cafés, bars, musées, espaces insolites
- Cherche des adresses authentiques qui correspondent à la sensibilité de l'utilisateur"""

    prompt = f"""Tu es un critique culturel et un fin connaisseur des villes.

Voici le profil musical d'un utilisateur :
- Artistes favoris : {', '.join(profile['artists'])}
- Genres : {', '.join(profile['genres'])}
- Titres récents : {', '.join(profile['tracks'][:5])}

ÉTAPE 1 — Analyse esthétique profonde.
Ne pense pas à la musique comme genre. Pense à ce qu'elle dit de la sensibilité de cette personne.
Extrait 3 à 5 valeurs esthétiques précises.

ÉTAPE 2 — Génère 8 requêtes de recherche Google Places pour {city}.
{niche_instruction}
Sois radical dans la diversité : parcs, cimetières, cinémas, librairies, marchés, musées, cafés, espaces insolites, jardins, passages, quais, brocantes, bars.

Réponds UNIQUEMENT en JSON valide :
{{
  "valeurs_esthetiques": ["valeur 1", "valeur 2", "valeur 3"],
  "analyse": "2-3 phrases sur la sensibilité de cette personne",
  "requetes": [
    {{
      "query": "requête Google Places précise",
      "type_lieu": "parc/cinéma/librairie/bar/café/musée/etc",
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


def get_shared_queries(profile_a, profile_b, city, grande_ville):
    """Analyse deux profils et génère des requêtes basées sur leur sensibilité commune."""
    client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])

    if grande_ville:
        niche_instruction = f"""
NIVEAU DE NOTORIÉTÉ VISÉ pour {city} :
- Pas le top 20 TripAdvisor ni les monuments que tout touriste connaît
- Vise les lieux que les habitants connaissent et fréquentent
- Inclus le nom d'un quartier précis dans chaque requête"""
    else:
        niche_instruction = """
- Varie les types : parcs, cinémas, librairies, marchés, cafés, bars, musées, espaces insolites"""

    prompt = f"""Tu es un critique culturel et un fin connaisseur des villes.

Deux personnes veulent explorer une ville ensemble. Voici leurs profils musicaux :

PROFIL A :
- Artistes : {', '.join(profile_a['artists'])}
- Genres : {', '.join(profile_a['genres'])}
- Titres : {', '.join(profile_a['tracks'][:3])}

PROFIL B :
- Artistes : {', '.join(profile_b['artists'])}
- Genres : {', '.join(profile_b['genres'])}
- Titres : {', '.join(profile_b['tracks'][:3])}

ÉTAPE 1 — Analyse de la sensibilité commune.
Ne pense pas aux genres musicaux. Pense à ce que ces deux profils partagent en profondeur — leurs points de rencontre esthétiques, émotionnels, culturels.
Extrait 3 à 5 valeurs esthétiques communes, même si les musiques semblent différentes en surface.
Explique en 2-3 phrases ce territoire partagé.

ÉTAPE 2 — Génère 8 requêtes Google Places pour {city} qui correspondent à cette sensibilité commune.
{niche_instruction}
Sois radical dans la diversité : parcs, cimetières, cinémas, librairies, marchés, musées, cafés, espaces insolites, jardins, passages, quais, brocantes, bars.

Réponds UNIQUEMENT en JSON valide :
{{
  "valeurs_communes": ["valeur 1", "valeur 2", "valeur 3"],
  "analyse_commune": "2-3 phrases sur ce que ces deux profils partagent en profondeur",
  "requetes": [
    {{
      "query": "requête Google Places précise",
      "type_lieu": "parc/cinéma/librairie/bar/café/musée/etc",
      "vibe": "quelle valeur commune ce lieu incarne"
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
            body = {"textQuery": f"{item['query']} {city}", "languageCode": "fr"}

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
        except Exception:
            continue

    return all_places


def select_and_explain(profile, city, places, analyse, valeurs, grande_ville):
    client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
    places_text = json.dumps(places, ensure_ascii=False, indent=2)

    if grande_ville:
        niche_filter = f"""
NIVEAU DE NOTORIÉTÉ :
- Écarte les lieux du top 20 touristique de {city}
- Garde des lieux que les habitants connaissent et apprécient
- Test : un habitant dirait "ah oui je connais, c'est bien"
- Si choix entre deux lieux similaires, préfère le moins touristique"""
    else:
        niche_filter = ""

    prompt = f"""Tu es un critique culturel qui écrit sur les villes.

Sensibilité de l'utilisateur :
- Artistes : {', '.join(profile['artists'])}
- Valeurs esthétiques : {', '.join(valeurs)}
- Analyse : {analyse}

Voici une liste de vrais lieux trouvés à {city} :
{places_text}

{niche_filter}

Sélectionne exactement 5 lieux. Varie les types — un lieu de jour, un lieu de nuit, un silencieux, un vivant.
Parle comme un critique culturel, pas un guide touristique.
Le lien avec la musique doit être indirect et poétique.

Réponds UNIQUEMENT en JSON valide :
{{
  "lieux": [
    {{
      "nom": "nom exact",
      "adresse": "adresse exacte",
      "note": "note",
      "type_lieu": "type",
      "moment": "matin/après-midi/soir/nuit",
      "ambiance": "une phrase sèche et précise",
      "pourquoi": "lien poétique et indirect, 2-3 phrases"
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


def select_and_explain_duo(profile_a, profile_b, city, places, analyse_commune, valeurs_communes, grande_ville):
    """Sélectionne les lieux pour deux profils en expliquant le lien avec les deux."""
    client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
    places_text = json.dumps(places, ensure_ascii=False, indent=2)

    if grande_ville:
        niche_filter = f"""
NIVEAU DE NOTORIÉTÉ :
- Écarte les lieux du top 20 touristique de {city}
- Garde des lieux que les habitants connaissent et apprécient"""
    else:
        niche_filter = ""

    prompt = f"""Tu es un critique culturel qui écrit sur les villes.

Deux personnes explorent {city} ensemble. Voici leurs profils :

PROFIL A : {', '.join(profile_a['artists'])}
PROFIL B : {', '.join(profile_b['artists'])}

Sensibilité commune :
- Valeurs : {', '.join(valeurs_communes)}
- Analyse : {analyse_commune}

Voici une liste de vrais lieux trouvés à {city} :
{places_text}

{niche_filter}

Sélectionne exactement 5 lieux. Varie les types — un lieu de jour, un lieu de nuit, un silencieux, un vivant.
Pour chaque lieu, explique pourquoi il parle aux DEUX profils — trouve le point de rencontre.
Parle comme un critique culturel, pas un guide touristique.

Réponds UNIQUEMENT en JSON valide :
{{
  "lieux": [
    {{
      "nom": "nom exact",
      "adresse": "adresse exacte",
      "note": "note",
      "type_lieu": "type",
      "moment": "matin/après-midi/soir/nuit",
      "ambiance": "une phrase sèche et précise",
      "pourquoi": "pourquoi ce lieu parle aux deux profils, 2-3 phrases"
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
