"""
PROJECT: Smart Pothole Reporter (Competition Edition)
AUTHOR: High School AI Developer
DESCRIPTION:
    A production-grade Streamlit web application featuring a polished landing page,
    live GPS telemetry, Gemini AI analysis, and automated email dispatch.
"""

# ==========================================
# 1. IMPORTING REQUIRED LIBRARIES
# ==========================================
import streamlit as st
import google.generativeai as genai
from PIL import Image
import smtplib
from email.message import EmailMessage
from streamlit_geolocation import streamlit_geolocation
import io

# ==========================================
# 2. CONFIGURATION & SECRETS MANAGEMENT
# ==========================================
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    GMAIL_USER = st.secrets["GMAIL_USER"]
    GMAIL_PASSWORD = st.secrets["GMAIL_APP_PASSWORD"]
    RECIPIENT_EMAIL = st.secrets["RECIPIENT_EMAIL"]
except KeyError:
    st.error("🚨 Configuration Error: Missing required keys in Streamlit Secrets!")
    st.info("Please ensure GEMINI_API_KEY, GMAIL_USER, GMAIL_APP_PASSWORD, and RECIPIENT_EMAIL are set up in your secrets.")
    st.stop()

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

# ==========================================
# 3. GLOBAL STYLES — injected once at top
# ==========================================
def inject_styles():
    st.markdown("""
    <style>
    /* ── Google Fonts ── */
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');

    /* ── Root tokens ── */
    :root {
        --accent: #E8FF47;          /* electric lime — alert / CTA */
        --accent-dark: #B8CC1A;
        --surface: #0D0D0D;
        --surface-raised: #141414;
        --surface-card: #1C1C1C;
        --border: rgba(255,255,255,0.08);
        --border-hover: rgba(232,255,71,0.35);
        --text-primary: #F5F5F5;
        --text-secondary: #9A9A9A;
        --text-muted: #555;
        --success: #4EFFA8;
        --danger: #FF5A5A;
        --warning: #FFB74D;
        --radius: 12px;
        --radius-lg: 20px;
    }

    /* ── Reset Streamlit chrome ── */
    .stApp, .main, section.main { background: var(--surface) !important; }
    .block-container { max-width: 760px !important; padding: 2rem 1.5rem !important; }
    footer, header { display: none !important; }
    [data-testid="stToolbar"] { display: none !important; }

    /* ── Typography base ── */
    html, body, .stMarkdown, .stText, label, p, span, div {
        font-family: 'DM Sans', sans-serif !important;
        color: var(--text-primary);
    }
    h1, h2, h3, .display-heading {
        font-family: 'Syne', sans-serif !important;
        color: var(--text-primary) !important;
    }

    /* ── Landing hero ── */
    .hero-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(232,255,71,0.1);
        border: 1px solid rgba(232,255,71,0.3);
        border-radius: 999px;
        padding: 5px 14px;
        font-family: 'DM Sans', sans-serif;
        font-size: 12px;
        font-weight: 500;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: var(--accent);
        margin-bottom: 1.5rem;
    }

    .hero-title {
        font-family: 'Syne', sans-serif !important;
        font-size: clamp(2.4rem, 6vw, 3.8rem) !important;
        font-weight: 800 !important;
        line-height: 1.1 !important;
        letter-spacing: -0.02em !important;
        color: var(--text-primary) !important;
        margin: 0 0 1rem !important;
    }
    .hero-title .accent { color: var(--accent); }

    .hero-sub {
        font-size: 1.05rem;
        line-height: 1.7;
        color: var(--text-secondary);
        max-width: 520px;
        margin: 0 auto 2.5rem;
    }

    /* ── Stat row on landing ── */
    .stat-row {
        display: flex;
        justify-content: center;
        gap: 2.5rem;
        margin: 2rem 0 2.5rem;
        flex-wrap: wrap;
    }
    .stat-item { text-align: center; }
    .stat-num {
        font-family: 'Syne', sans-serif;
        font-size: 1.8rem;
        font-weight: 700;
        color: var(--accent);
        line-height: 1;
    }
    .stat-label {
        font-size: 12px;
        color: var(--text-muted);
        letter-spacing: 0.06em;
        text-transform: uppercase;
        margin-top: 4px;
    }

    /* ── Feature pill row ── */
    .feature-pills {
        display: flex;
        flex-wrap: wrap;
        justify-content: center;
        gap: 10px;
        margin-bottom: 2.5rem;
    }
    .pill {
        background: var(--surface-card);
        border: 1px solid var(--border);
        border-radius: 999px;
        padding: 6px 16px;
        font-size: 13px;
        color: var(--text-secondary);
        font-family: 'DM Sans', sans-serif;
    }
    .pill span { margin-right: 6px; }

    /* ── Divider ── */
    .rule {
        border: none;
        border-top: 1px solid var(--border);
        margin: 2rem 0;
    }

    /* ── Step cards ── */
    .step-card {
        background: var(--surface-card);
        border: 1px solid var(--border);
        border-radius: var(--radius-lg);
        padding: 1.5rem;
        margin-bottom: 1.25rem;
        position: relative;
    }
    .step-card:hover { border-color: var(--border-hover); transition: border-color 0.2s; }
    .step-badge {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 28px; height: 28px;
        background: var(--accent);
        color: #000;
        border-radius: 50%;
        font-family: 'Syne', sans-serif;
        font-size: 13px;
        font-weight: 700;
        margin-bottom: 0.75rem;
    }
    .step-title {
        font-family: 'Syne', sans-serif !important;
        font-size: 1rem !important;
        font-weight: 600 !important;
        color: var(--text-primary) !important;
        margin: 0 0 0.3rem !important;
    }
    .step-desc {
        font-size: 14px;
        color: var(--text-secondary);
        line-height: 1.5;
        margin: 0;
    }

    /* ── GPS status banner ── */
    .gps-locked {
        display: flex;
        align-items: center;
        gap: 12px;
        background: rgba(78,255,168,0.07);
        border: 1px solid rgba(78,255,168,0.25);
        border-radius: var(--radius);
        padding: 0.9rem 1.2rem;
        margin: 0.75rem 0 1.5rem;
    }
    .gps-dot {
        width: 10px; height: 10px;
        background: var(--success);
        border-radius: 50%;
        box-shadow: 0 0 8px var(--success);
        flex-shrink: 0;
    }
    .gps-text { font-size: 14px; color: var(--success); font-weight: 500; }
    .gps-coords { font-size: 12px; color: var(--text-muted); margin-top: 2px; }

    /* ── AI result card ── */
    .result-card {
        border-radius: var(--radius-lg);
        padding: 1.4rem 1.5rem;
        margin: 1.25rem 0;
    }
    .result-card.positive {
        background: rgba(255,90,90,0.08);
        border: 1px solid rgba(255,90,90,0.3);
    }
    .result-card.negative {
        background: rgba(78,255,168,0.06);
        border: 1px solid rgba(78,255,168,0.2);
    }
    .result-label {
        font-family: 'Syne', sans-serif;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        margin-bottom: 0.5rem;
    }
    .result-text { font-size: 15px; line-height: 1.6; }

    /* ── Primary CTA button override ── */
    .stButton > button[kind="primary"],
    .stButton > button {
        background: var(--accent) !important;
        color: #000 !important;
        border: none !important;
        border-radius: var(--radius) !important;
        font-family: 'Syne', sans-serif !important;
        font-weight: 700 !important;
        font-size: 15px !important;
        letter-spacing: 0.03em !important;
        padding: 0.65rem 1.5rem !important;
        transition: opacity 0.15s !important;
    }
    .stButton > button:hover { opacity: 0.85 !important; }

    /* Secondary ghost button */
    .stButton > button[data-ghost="true"] {
        background: transparent !important;
        color: var(--text-secondary) !important;
        border: 1px solid var(--border) !important;
    }

    /* ── Alerts ── */
    .stAlert { border-radius: var(--radius) !important; }

    /* ── Section heading ── */
    .section-heading {
        font-family: 'Syne', sans-serif;
        font-size: 1.2rem;
        font-weight: 700;
        color: var(--text-primary);
        margin: 0 0 0.25rem;
    }
    .section-sub {
        font-size: 13.5px;
        color: var(--text-muted);
        margin: 0 0 1.2rem;
    }

    /* ── Mini logo bar ── */
    .top-bar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding-bottom: 1.25rem;
        border-bottom: 1px solid var(--border);
        margin-bottom: 1.75rem;
    }
    .top-bar-title {
        font-family: 'Syne', sans-serif;
        font-size: 1rem;
        font-weight: 700;
        color: var(--text-primary);
    }
    .top-bar-badge {
        background: rgba(232,255,71,0.1);
        border: 1px solid rgba(232,255,71,0.25);
        border-radius: 999px;
        padding: 3px 10px;
        font-size: 11px;
        color: var(--accent);
        font-weight: 500;
        letter-spacing: 0.05em;
    }

    /* ── Spinner & camera ── */
    .stSpinner { color: var(--accent) !important; }
    [data-testid="stCameraInput"] { border-radius: var(--radius) !important; overflow: hidden; }
    </style>
    """, unsafe_allow_html=True)


# ==========================================
# 4. EXIF METADATA INJECTION
# ==========================================
def change_to_rational(number):
    deg = int(number)
    min_float = (number - deg) * 60
    minute = int(min_float)
    sec = round((min_float - minute) * 60, 4)
    return [float(deg), float(minute), float(sec)]

def add_geotag_to_image(image_buffer, lat, lon):
    img = Image.open(image_buffer)
    gps_info = {}
    lat_ref = 'N' if lat >= 0 else 'S'
    lon_ref = 'E' if lon >= 0 else 'W'
    gps_info[1] = lat_ref
    gps_info[2] = change_to_rational(abs(lat))
    gps_info[3] = lon_ref
    gps_info[4] = change_to_rational(abs(lon))
    exif = img.getexif()
    exif[0x8825] = gps_info
    output_buffer = io.BytesIO()
    img.save(output_buffer, format="JPEG", exif=exif)
    output_buffer.seek(0)
    return output_buffer

# ==========================================
# 5. EMAIL DISPATCHER
# ==========================================
def send_notification_email(lat, lon, analysis):
    msg = EmailMessage()
    maps_link = f"https://www.google.com/maps?q={lat},{lon}"
    email_body = (
        f"🚨 AUTOMATED ALERT: Pothole Hazard Detected.\n\n"
        f"--- GEOGRAPHIC LOCATION ---\n"
        f"Latitude: {lat}\n"
        f"Longitude: {lon}\n"
        f"Google Maps Link: {maps_link}\n\n"
        f"--- GEMINI AI DAMAGE ANALYSIS ---\n"
        f"{analysis}\n\n"
        f"Sent automatically by the Smart Pothole Reporter Application."
    )
    msg.set_content(email_body)
    msg['Subject'] = "🚨 CRITICAL: Pothole Hazard Location Report"
    msg['From'] = GMAIL_USER
    msg['To'] = RECIPIENT_EMAIL
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(GMAIL_USER, GMAIL_PASSWORD)
        smtp.send_message(msg)


# ==========================================
# 6. APP ENTRY POINT
# ==========================================
st.set_page_config(
    page_title="Smart Pothole Reporter",
    page_icon="🛡️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

inject_styles()

if "app_started" not in st.session_state:
    st.session_state.app_started = False


# ══════════════════════════════════════════
# STATE A — LANDING PAGE
# ══════════════════════════════════════════
if not st.session_state.app_started:

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Optional logo ──
    col1, col2, col3 = st.columns([1.5, 1, 1.5])
    with col2:
        try:
            logo_img = Image.open("logo_smart.png")
            st.image(logo_img, use_container_width=True)
        except FileNotFoundError:
            # Fallback icon block when logo missing
            st.markdown("""
            <div style="width:72px;height:72px;background:var(--accent);border-radius:16px;
            display:flex;align-items:center;justify-content:center;
            font-size:2rem;margin:0 auto 1rem;">🛡️</div>
            """, unsafe_allow_html=True)

    # ── Badge ──
    st.markdown("""
    <div style="text-align:center">
        <div class="hero-badge">◉ &nbsp; Edge AI · Computer Vision · Live GPS</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Hero heading ──
    st.markdown("""
    <h1 class="hero-title" style="text-align:center">
        Smart<br><span class="accent">Pothole</span><br>Reporter
    </h1>
    """, unsafe_allow_html=True)

    # ── Subtitle ──
    st.markdown("""
    <p class="hero-sub" style="text-align:center">
        Capture road damage, verify it with Gemini AI, and automatically
        alert city authorities — all from your browser in under 30 seconds.
    </p>
    """, unsafe_allow_html=True)

    # ── Stats ──
    st.markdown("""
    <div class="stat-row">
        <div class="stat-item">
            <div class="stat-num">2.5s</div>
            <div class="stat-label">Avg. AI analysis</div>
        </div>
        <div class="stat-item">
            <div class="stat-num">GPS</div>
            <div class="stat-label">Live coordinates</div>
        </div>
        <div class="stat-item">
            <div class="stat-num">EXIF</div>
            <div class="stat-label">Geotagged proof</div>
        </div>
        <div class="stat-item">
            <div class="stat-num">Auto</div>
            <div class="stat-label">Email dispatch</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Feature pills ──
    st.markdown("""
    <div class="feature-pills">
        <div class="pill"><span>📍</span>Browser GPS</div>
        <div class="pill"><span>🤖</span>Gemini 2.5 Flash</div>
        <div class="pill"><span>📸</span>EXIF Geotag</div>
        <div class="pill"><span>📧</span>SMTP Alert</div>
        <div class="pill"><span>🔒</span>Secure Secrets</div>
    </div>
    """, unsafe_allow_html=True)

    # ── CTA button ──
    col_a, col_b, col_c = st.columns([1, 2, 1])
    with col_b:
        if st.button("Launch Application →", use_container_width=True):
            st.session_state.app_started = True
            st.rerun()

    st.markdown("<hr class='rule'>", unsafe_allow_html=True)

    # ── How it works ──
    st.markdown("<p style='text-align:center;font-size:12px;letter-spacing:0.1em;text-transform:uppercase;color:var(--text-muted);margin-bottom:1.25rem;font-family:DM Sans,sans-serif'>How it works</p>", unsafe_allow_html=True)

    steps = [
        ("Grant GPS access", "Your browser requests live coordinates. No data is stored."),
        ("Photograph the damage", "Point your device camera at the road defect and capture."),
        ("AI verification", "Gemini 2.5 Flash confirms whether a real pothole is visible."),
        ("Automatic alert", "A geotagged report is emailed to the responsible authority."),
    ]

    for i, (title, desc) in enumerate(steps, 1):
        st.markdown(f"""
        <div class="step-card">
            <div class="step-badge">{i}</div>
            <p class="step-title">{title}</p>
            <p class="step-desc">{desc}</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)


# ══════════════════════════════════════════
# STATE B — CORE REPORTING ENGINE
# ══════════════════════════════════════════
else:
    # ── Top bar ──
    col_title, col_back = st.columns([3, 1])
    with col_title:
        st.markdown("""
        <div class="top-bar">
            <div>
                <span class="top-bar-title">🛡️ Smart Pothole Reporter</span>
            </div>
            <div class="top-bar-badge">LIVE</div>
        </div>
        """, unsafe_allow_html=True)
    with col_back:
        if st.button("← Back", help="Return to landing page"):
            st.session_state.app_started = False
            st.rerun()

    # ── STEP 1: GPS ──
    st.markdown("""
    <div class="section-heading">Step 1 — Acquire GPS Coordinates</div>
    <p class="section-sub">Click the button below to fetch your live device location via the browser.</p>
    """, unsafe_allow_html=True)

    location_data = streamlit_geolocation()

    if location_data and location_data.get('latitude') is not None:
        lat = location_data['latitude']
        lon = location_data['longitude']

        st.markdown(f"""
        <div class="gps-locked">
            <div class="gps-dot"></div>
            <div>
                <div class="gps-text">GPS signal locked</div>
                <div class="gps-coords">{lat:.6f}, {lon:.6f}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── STEP 2: Camera ──
        st.markdown("""
        <div class="section-heading">Step 2 — Capture the Road Damage</div>
        <p class="section-sub">Position the camera directly over the road surface defect.</p>
        """, unsafe_allow_html=True)

        camera_photo = st.camera_input("", label_visibility="hidden")

        if camera_photo:
            with st.spinner("Embedding GPS coordinates into image EXIF headers…"):
                geotagged_image_file = add_geotag_to_image(camera_photo, lat, lon)
                st.toast("✅ EXIF geotag injected successfully.", icon="📍")

            st.markdown("<hr class='rule'>", unsafe_allow_html=True)

            # ── STEP 3: Analyse ──
            # ── STEP 3: Analyse ──
st.markdown("""
<div class="section-heading">Step 3 — Analyse & Dispatch</div>
<p class="section-sub">
Run the image through Gemini AI. If a pothole is confirmed,
a report is emailed automatically.
</p>
""", unsafe_allow_html=True)

if st.button("🚀 Analyse & Send Report", use_container_width=True):

    with st.spinner("Sending frame to Gemini AI…"):

        try:
            # Reset image buffer
            geotagged_image_file.seek(0)

            prompt = (
                "You are a strict city infrastructure monitoring system. "
                "Analyze this image carefully. "
                "Determine whether there is a real pothole, cracked asphalt, "
                "or severe road surface damage visible. "
                "Reply ONLY in this format: "
                "'YES: explanation' or 'NO: explanation'."
            )

            response = model.generate_content(
                [
                    prompt,
                    {
                        "mime_type": "image/jpeg",
                        "data": geotagged_image_file.getvalue()
                    }
                ]
            )

            verdict = response.text.strip()

        except Exception as e:
            st.error(f"Gemini Analysis Error: {e}")
            st.stop()

    # ── Result Processing ──
    is_pothole = verdict.upper().startswith("YES")

    card_class = "positive" if is_pothole else "negative"

    label_text = (
        "⚠ Pothole Detected"
        if is_pothole
        else "✓ No Damage Found"
    )

    label_color = (
        "var(--danger)"
        if is_pothole
        else "var(--success)"
    )

    st.markdown(
        f"""
        <div class="result-card {card_class}">
            <div class="result-label" style="color:{label_color}">
                {label_text}
            </div>

            <div class="result-text">
                {verdict}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # ── Email Dispatch ──
    if is_pothole:

        with st.spinner(
            "Dispatching secure alert to authority inbox…"
        ):

            try:
                send_notification_email(lat, lon, verdict)

                st.balloons()

                st.success(
                    "📩 Alert dispatched successfully. "
                    "Authorities have been notified."
                )

            except Exception as e:
                st.error(
                    f"SMTP error — could not send email: {e}"
                )

    else:
        st.success(
            "🌿 No structural failure confirmed. "
            "No alert triggered.")
    else:
        st.markdown("""
        <div style="background:var(--surface-card);border:1px solid var(--border);
        border-radius:var(--radius-lg);padding:1.5rem;text-align:center;margin-top:0.5rem">
            <div style="font-size:2rem;margin-bottom:0.75rem">📍</div>
            <p style="font-weight:500;margin:0 0 0.4rem;font-family:'Syne',sans-serif">
                Waiting for GPS access
            </p>
            <p style="font-size:13.5px;color:var(--text-muted);margin:0">
                Grant location permission in your browser to unlock the camera step.
            </p>
        </div>
        """, unsafe_allow_html=True)
