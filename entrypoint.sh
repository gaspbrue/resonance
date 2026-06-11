#!/bin/bash
mkdir -p /app/.streamlit
cat > /app/.streamlit/secrets.toml << EOF
SPOTIFY_CLIENT_ID = "${SPOTIFY_CLIENT_ID}"
SPOTIFY_CLIENT_SECRET = "${SPOTIFY_CLIENT_SECRET}"
ANTHROPIC_API_KEY = "${ANTHROPIC_API_KEY}"
REDIRECT_URI = "${REDIRECT_URI}"
GOOGLE_PLACES_API_KEY = "${GOOGLE_PLACES_API_KEY}"
EOF
streamlit run app.py --server.port=8501 --server.address=0.0.0.0