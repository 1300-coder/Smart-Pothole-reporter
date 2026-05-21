"""
PROJECT: Smart Pothole Reporter (Competition Edition)
AUTHOR: High School AI Developer
DESCRIPTION:
    AI-powered pothole reporting system with:
    - Live GPS via streamlit-geolocation
    - Camera capture via st.camera_input
    - Gemini AI analysis
    - EXIF geotagging
    - Automatic authority alerts
"""

# ==========================================
# IMPORTS
# ==========================================

import io
import smtplib
from email.message import EmailMessage

import google.generativeai as genai
import streamlit as st
from PIL import Image
from streamlit_geolocation import streamlit_geolocation


# ==========================================
# PAGE CONFIG  (must be first Streamlit call)
# ==========================================

st.set_page_config(
    page_title="Smart Pothole Reporter",
    page_icon="🛡️",
    layout="centered",
    initial_sidebar_state="collapsed",
)


# ==========================================
# SECRETS
# ==========================================

try:
    GEMINI_API_KEY   = st.secrets["GEMINI_API_KEY"]
    GMAIL_USER       = st.secrets["GMAIL_USER"]
    GMAIL_PASSWORD   = st.secrets["GMAIL_APP_PASSWORD"]
    RECIPIENT_EMAIL  = st.secrets["RECIPIENT_EMAIL"]
except KeyError as missing:
    st.error(f"🚨 Missing secret: {missing}. Add it in ⚙ Settings → Secrets.")
    st.stop()


# ==========================================
# GEMINI CONFIG
# ==========================================

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")


# ==========================================
# GLOBAL STYLES
# ==========================================

def inject_styles():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:ital,wght@0,300;0,400;0,500;1,400&display=swap');

        :root {
            --accent:       #E8FF47;
            --surface:      #0D0D0D;
            --card:         #1A1A1A;
            --border:       rgba(255,255,255,0.08);
            --text:         #F5F5F5;
            --muted:        #9A9A9A;
            --success:      #4EFFA8;
            --danger:       #FF5A5A;
            --r:            14px;
            --r-lg:         22px;
        }

        /* ---- base ---- */
        .stApp, .main, section.main   { background: var(--surface) !important; }
        footer, header, #MainMenu       { display: none !important; }
        .block-container               { max-width: 760px !important; padding: 2rem 1.5rem !important; }

        html, body, p, span, div       { font-family: 'DM Sans', sans-serif; color: var(--text); }
        h1, h2, h3                      { font-family: 'Syne', sans-serif; }

        /* ---- hero ---- */
        .hero-title {
            font-size: clamp(2.6rem, 7vw, 4rem);
            font-weight: 800;
            line-height: 1.05;
            text-align: center;
            margin-bottom: 1rem;
        }
        .accent     { color: var(--accent); }
        .hero-sub   { text-align: center; color: var(--muted); line-height: 1.7; margin-bottom: 2.5rem; }
        .hero-badge {
            display: inline-flex; align-items: center; justify-content: center;
            gap: 8px;
            background: rgba(232,255,71,0.08);
            border: 1px solid rgba(232,255,71,0.25);
            color: var(--accent);
            padding: 6px 14px; border-radius: 999px; font-size: 12px;
            margin-bottom: 1.5rem;
        }

        /* ---- section labels ---- */
        .section-heading { font-size: 1.15rem; font-weight: 700; margin-bottom: 0.2rem; }
        .section-sub     { color: var(--muted); margin-bottom: 0.8rem; font-size: 0.93rem; }

        /* ---- gps box ---- */
        .gps-box {
            background: rgba(78,255,168,0.08);
            border: 1px solid rgba(78,255,168,0.28);
            border-radius: var(--r);
            padding: 1rem 1.2rem;
            margin-bottom: 1.5rem;
        }
        .gps-label { color: var(--success); font-weight: 700; margin-bottom: 0.3rem; font-size: 0.9rem; }
        .gps-coords{ font-size: 1.05rem; letter-spacing: 0.02em; }

        /* ---- waiting box ---- */
        .wait-box {
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: var(--r-lg);
            padding: 2rem 1.5rem;
            text-align: center;
            margin-top: 1rem;
        }
        .wait-icon  { font-size: 2rem; margin-bottom: 0.75rem; }
        .wait-title { font-weight: 700; margin-bottom: 0.4rem; color: var(--text); }
        .wait-sub   { color: var(--muted); margin: 0; font-size: 0.92rem; }

        /* ---- result card ---- */
        .result-card { border-radius: var(--r-lg); padding: 1.4rem; margin-top: 1.25rem; }
        .positive    { background: rgba(255,90,90,0.08); border: 1px solid rgba(255,90,90,0.28); }
        .negative    { background: rgba(78,255,168,0.06); border: 1px solid rgba(78,255,168,0.22); }
        .result-label{ font-weight: 700; margin-bottom: 0.5rem; font-family: 'Syne', sans-serif; }
        .result-text { line-height: 1.75; color: var(--muted); }

        /* ---- divider ---- */
        hr { border-color: var(--border) !important; margin: 1.75rem 0 !important; }

        /* ---- buttons ---- */
        .stButton > button {
            background: var(--accent) !important;
            color: #000 !important;
            border: none !important;
            border-radius: 12px !important;
            font-weight: 700 !important;
            font-family: 'Syne', sans-serif !important;
            padding: 0.7rem 1.5rem !important;
            transition: opacity .2s !important;
        }
        .stButton > button:hover { opacity: 0.88 !important; }

        /* ---- camera widget — remove white card chrome ---- */
        [data-testid="stCameraInput"] > div:first-child { display: none; }
        [data-testid="stCameraInputButton"] {
            background: var(--card) !important;
            border: 1px dashed rgba(255,255,255,0.18) !important;
            border-radius: var(--r-lg) !important;
            color: var(--muted) !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


inject_styles()


# ==========================================
# EXIF HELPERS
# ==========================================

def _to_rational(number: float) -> list[float]:
    """Convert decimal degrees to [deg, min, sec] floats."""
    deg = int(number)
    min_float = (number - deg) * 60
    minute = int(min_float)
    sec = round((min_float - minute) * 60, 4)
    return [float(deg), float(minute), float(sec)]


def add_geotag(image_buffer, lat: float, lon: float) -> io.BytesIO:
    """Embed GPS EXIF data into a JPEG image buffer."""
    img = Image.open(image_buffer)

    gps_info = {
        1: "N" if lat >= 0 else "S",
        2: _to_rational(abs(lat)),
        3: "E" if lon >= 0 else "W",
        4: _to_rational(abs(lon)),
    }

    exif = img.getexif()
    exif[0x8825] = gps_info          # GPSInfo IFD tag

    buf = io.BytesIO()
    img.save(buf, format="JPEG", exif=exif)
    buf.seek(0)
    return buf


# ==========================================
# EMAIL HELPER
# ==========================================

def send_alert(lat: float, lon: float, analysis: str) -> None:
    recipients = [e.strip() for e in RECIPIENT_EMAIL.split(",")]

    maps_url = f"https://www.google.com/maps?q={lat},{lon}"
    body = (
        f"🚨 POTHOLE ALERT\n\n"
        f"Latitude  : {lat}\n"
        f"Longitude : {lon}\n"
        f"Google Maps: {maps_url}\n\n"
        f"AI ANALYSIS:\n{analysis}"
    )

    msg = EmailMessage()
    msg.set_content(body)
    msg["Subject"] = "🚨 Smart Pothole Alert"
    msg["From"]    = GMAIL_USER
    msg["To"]      = ", ".join(recipients)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(GMAIL_USER, GMAIL_PASSWORD)
        smtp.send_message(msg, to_addrs=recipients)


# ==========================================
# SESSION STATE INIT
# ==========================================

for key, default in {
    "app_started":   False,
    "location_data": None,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default


# ==========================================
# ① LANDING PAGE
# ==========================================

if not st.session_state.app_started:

    st.markdown("<br>", unsafe_allow_html=True)

    try:
        st.image(Image.open("logo_smart.png"), use_container_width=True)
    except Exception:
        pass

    st.markdown(
        '<div style="text-align:center">'
        '<div class="hero-badge">◉ Edge AI · Live GPS · Gemini Vision</div>'
        "</div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        '<h1 class="hero-title">'
        "Smart<br>"
        '<span class="accent">Pothole</span><br>'
        "Reporter"
        "</h1>",
        unsafe_allow_html=True,
    )

    st.markdown(
        '<p class="hero-sub">'
        "Capture road damage, verify it with Gemini AI, "
        "attach live GPS coordinates, and automatically "
        "notify city authorities in seconds."
        "</p>",
        unsafe_allow_html=True,
    )

    if st.button("Launch Application →", use_container_width=True):
        st.session_state.app_started = True
        st.rerun()

    st.stop()


# ==========================================
# ② MAIN APPLICATION
# ==========================================

# -- Top bar --
col_title, col_back = st.columns([5, 1])
with col_title:
    st.markdown(
        '<h2 style="font-family:Syne,sans-serif;margin:0 0 1.25rem">🛡️ Smart Pothole Reporter</h2>',
        unsafe_allow_html=True,
    )
with col_back:
    if st.button("← Back"):
        st.session_state.app_started   = False
        st.session_state.location_data = None
        st.rerun()


# ==========================================
# STEP 1 — GPS
# ==========================================

st.markdown(
    '<div class="section-heading">Step 1 — Acquire GPS Coordinates</div>'
    '<div class="section-sub">Click the button and grant browser location permission.</div>',
    unsafe_allow_html=True,
)

# KEY FIX: always render the component so its JS runs every load;
# only save coordinates the first time we get a real fix.
raw_loc = streamlit_geolocation()

if (
    raw_loc
    and isinstance(raw_loc, dict)
    and raw_loc.get("latitude") is not None
    and st.session_state.location_data is None
):
    st.session_state.location_data = raw_loc
    st.rerun()

location_data = st.session_state.location_data
gps_ready     = bool(location_data and location_data.get("latitude") is not None)

# -- GPS status display --
if gps_ready:
    lat = location_data["latitude"]
    lon = location_data["longitude"]
    st.markdown(
        f'<div class="gps-box">'
        f'<div class="gps-label">📍 GPS Locked</div>'
        f'<div class="gps-coords">{lat:.6f}, {lon:.6f}</div>'
        f"</div>",
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        '<div class="wait-box">'
        '<div class="wait-icon">📍</div>'
        '<p class="wait-title">Waiting for GPS Access</p>'
        '<p class="wait-sub">Click "Get Location" above, then allow browser location permission to continue.</p>'
        "</div>",
        unsafe_allow_html=True,
    )
    st.stop()   # nothing below makes sense without GPS


# ==========================================
# STEP 2 — CAMERA
# ==========================================

st.markdown(
    '<div class="section-heading">Step 2 — Capture Road Damage</div>'
    '<div class="section-sub">Allow camera access when prompted, then tap the shutter.</div>',
    unsafe_allow_html=True,
)

# KEY FIX: use a plain string label (not empty), and do NOT set
# label_visibility here — that argument conflicts with camera_input
# in some Streamlit versions and can silently prevent the widget from
# mounting its webcam bridge.
camera_photo = st.camera_input("Take a photo of the pothole")

if camera_photo is None:
    st.stop()   # wait for photo before continuing


# ==========================================
# GEOTAG IMAGE
# ==========================================

with st.spinner("Embedding GPS metadata into image…"):
    try:
        geotagged_buf = add_geotag(camera_photo, lat, lon)
    except Exception as e:
        st.error(f"EXIF embedding failed: {e}")
        st.stop()

st.success("✅ GPS metadata embedded successfully.")
st.markdown("---")


# ==========================================
# STEP 3 — ANALYSIS & DISPATCH
# ==========================================

st.markdown(
    '<div class="section-heading">Step 3 — Analyse & Dispatch</div>'
    '<div class="section-sub">Run Gemini AI analysis and automatically notify authorities.</div>',
    unsafe_allow_html=True,
)

if not st.button("🚀 Analyse & Send Report", use_container_width=True):
    st.stop()

# -- Gemini analysis --
with st.spinner("Analysing image with Gemini AI…"):
    try:
        geotagged_buf.seek(0)
        prompt = (
            "You are a strict city infrastructure monitoring system. "
            "Determine whether this image contains a real pothole or "
            "severe road damage. "
            "Reply ONLY in the format 'YES: <explanation>' "
            "or 'NO: <explanation>'."
        )
        response = model.generate_content(
            [
                prompt,
                {"mime_type": "image/jpeg", "data": geotagged_buf.getvalue()},
            ]
        )
        verdict = response.text.strip()
    except Exception as e:
        st.error(f"Gemini analysis error: {e}")
        st.stop()

# -- Result card --
is_pothole   = verdict.upper().startswith("YES")
card_class   = "positive" if is_pothole else "negative"
label_text   = "⚠ Pothole Detected" if is_pothole else "✓ No Damage Found"
label_color  = "#FF5A5A"  if is_pothole else "#4EFFA8"

st.markdown(
    f'<div class="result-card {card_class}">'
    f'<div class="result-label" style="color:{label_color}">{label_text}</div>'
    f'<div class="result-text">{verdict}</div>'
    f"</div>",
    unsafe_allow_html=True,
)

# -- Email alert --
if is_pothole:
    with st.spinner("Dispatching alert to authorities…"):
        try:
            send_alert(lat, lon, verdict)
            st.balloons()
            st.success("📩 Authorities have been notified.")
        except Exception as e:
            st.error(f"SMTP error: {e}")
else:
    st.success("🌿 No pothole detected — road looks clear.")
