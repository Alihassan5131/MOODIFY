import os
import requests
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import streamlit as st
import time

# ==============================
# Load API keys
# ==============================
groq_api_key = os.getenv("groqapi")
spotify_client_id = os.getenv("spotify_client_id")
spotify_client_secret = os.getenv("spotify_client_secret")

if not spotify_client_id or not spotify_client_secret or not groq_api_key:
    st.error("⚠️ Missing API keys! Please set them in Hugging Face Space Settings → Variables and secrets.")
    st.stop()

# ==============================
# Spotify authentication
# ==============================
sp = spotipy.Spotify(
    auth_manager=SpotifyClientCredentials(
        client_id=spotify_client_id,
        client_secret=spotify_client_secret
    )
)

# ==============================
# App Page Config & Background
# ==============================
st.set_page_config(page_title="MOODiFY", layout="wide")
st.markdown("""
<style>
body {
    background: linear-gradient(to right, #D6EAF8, #AED6F1);
}
.stButton>button {
    background: linear-gradient(to right, #6DD5FA, #2980B9);
    color: white;
    font-weight: bold;
    border-radius: 8px;
    padding: 8px 16px;
    transition: all 0.3s ease;
}
.stButton>button:hover {
    transform: scale(1.05);
    box-shadow: 0px 4px 12px rgba(0,0,0,0.3);
}
</style>
""", unsafe_allow_html=True)

# ==============================
# App Title: MOODiFY
# ==============================
st.markdown(
    """
    <div style="
        text-align:center;
        padding: 20px;
        border-radius: 15px;
        background: linear-gradient(90deg, #FFDEE9, #B5FFFC);
        font-family: 'Arial Black', Gadget, sans-serif;
        box-shadow: 3px 3px 15px rgba(0,0,0,0.2);
        margin-bottom: 20px;
    ">
        <h1 style='font-size:64px; font-weight:bold; background: linear-gradient(to right, #FF6B6B, #FFD93D);
        -webkit-background-clip: text; color: transparent;'>MOODiFY</h1>
        <p style='font-size:20px; color:#1B2631; margin-top:0;'>
            Your vibes, your playlist 🎵 <br>
            <span style="font-size:14px; color:#34495E;">Developed by Ali Hassan</span>
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

# ==============================
# Sidebar: Mood & Language + Previous Selections
# ==============================
st.sidebar.header("🎛 Customize Your Mood")
mood_options = {
    "Happy 😄": "Happy",
    "Sad 😢": "Sad",
    "Energetic ⚡": "Energetic",
    "Relaxed 🌿": "Relaxed",
    "Romantic 💖": "Romantic",
    "Angry 😡": "Angry"
}
mood = st.sidebar.selectbox("Mood", list(mood_options.keys()))
mood_text = mood_options[mood]

language_options = ["Punjabi", "Urdu", "Hindi", "English", "Arabic"]
language = st.sidebar.selectbox("Language", language_options)

shuffle = st.sidebar.checkbox("🔀 Shuffle AI suggestions")

# ---------- Sidebar Previous Selections ----------
if "history" in st.session_state and st.session_state.history:
    st.sidebar.markdown("### 🕒 Previous Selections")
    for h in reversed(st.session_state.history[-5:]):
        st.sidebar.write(f"**Mood:** {h['mood']} | **Language:** {h['language']}")

# ==============================
# Initialize history
# ==============================
if "history" not in st.session_state:
    st.session_state.history = []

# ==============================
# Generate Playlist Button
# ==============================
if st.button("🎶 Get Playlist"):
    with st.spinner("Generating AI playlist suggestion..."):
        try:
            # ---------- AI Playlist Suggestion ----------
            groq_url = "https://api.groq.com/openai/v1/chat/completions"
            system_prompt = "You are a music assistant. Suggest playlist descriptions in 1-2 sentences."
            user_prompt = (
                f"Suggest a short, human-readable playlist description in {language} "
                f"for a {mood_text.lower()} mood. Make it clear and natural."
            )

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]

            payload = {
                "model": "openai/gpt-oss-20b",
                "messages": messages
            }

            headers = {
                "Authorization": f"Bearer {groq_api_key}",
                "Content-Type": "application/json"
            }

            response = requests.post(groq_url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            ai_suggestion = data.get("choices", [{}])[0].get("message", {}).get("content", "No suggestion available.")

            if shuffle:
                ai_suggestion = ai_suggestion[::-1]

            # ---------- Styled AI Suggestion ----------
            st.markdown(
                f"""
                <div style="
                    background-color:#EAF2F8; 
                    color:#1B2631; 
                    padding:20px; 
                    border-radius:15px; 
                    font-size:18px;
                    box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
                    margin-bottom:20px;
                    animation: fadeIn 0.5s;
                ">
                    <strong>🎤 AI Suggestion:</strong> {ai_suggestion}
                </div>
                <style>
                @keyframes fadeIn {{
                    from {{opacity: 0;}}
                    to {{opacity: 1;}}
                }}
                </style>
                """,
                unsafe_allow_html=True
            )

            # ---------- Spotify Playlist Search ----------
            results = sp.search(q=f"{mood_text} {language} music", type="playlist", limit=10)
            playlists = results.get("playlists", {}).get("items", [])
            valid_playlists = [p for p in playlists if p and p.get("id")]

            if not valid_playlists:
                st.warning("No valid playlists found. Try another mood or language!")
            else:
                # Display playlists in two columns for better layout
                cols = st.columns(2)
                for idx, playlist in enumerate(valid_playlists):
                    col = cols[idx % 2]
                    if playlist and isinstance(playlist, dict):
                        playlist_name = playlist.get("name", "No Name")
                        owner_info = playlist.get("owner") or {}
                        owner_name = owner_info.get("display_name", "Unknown")
                        spotify_url = playlist.get("external_urls", {}).get("spotify", "#")
                        images = playlist.get("images") or []
                        image_url = images[0].get("url") if images and images[0].get("url") else None

                        with col.expander(f"🎵 {playlist_name} - by {owner_name}"):
                            if image_url:
                                st.image(image_url, width=300)
                            st.markdown(f"[🎧 Open in Spotify]({spotify_url})")

                            playlist_id = playlist.get("id")
                            if playlist_id:
                                tracks_data = sp.playlist_tracks(playlist_id).get("items", []) or []
                                if tracks_data:
                                    for t in tracks_data[:5]:  # first 5 tracks
                                        if t and isinstance(t, dict):
                                            track = t.get("track")
                                            if track and isinstance(track, dict):
                                                track_name = track.get("name", "Unknown")
                                                artists = track.get("artists") or []
                                                artist_name = artists[0].get("name", "Unknown") if artists and artists[0] else "Unknown"
                                                st.write(f"🎶 {track_name} - {artist_name}")
                                                preview_url = track.get("preview_url")
                                                if preview_url:
                                                    st.audio(preview_url, format="audio/mp3")
                                                else:
                                                    st.write("🔇 No preview available for this track")
                                            else:
                                                st.write("Track information missing")
                                else:
                                    st.write("No tracks available for this playlist")
                            else:
                                st.write("Invalid playlist ID")

            # ---------- Save History ----------
            st.session_state.history.append({
                "mood": mood_text,
                "language": language
            })

        except Exception as e:
            st.error(f"Error: {e}")
