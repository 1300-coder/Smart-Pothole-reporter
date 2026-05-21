"""
PROJECT: Smart Pothole Reporter (Competition Edition)
AUTHOR: High School AI Developer
DESCRIPTION:
    AI-powered pothole reporting system with:
    - Live GPS
    - Camera capture
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
# PAGE CONFIG
# ==========================================

st.set_page_config(
    page_title="Smart Pothole Reporter",
    page_icon="🛡️",
    layout="centered",
    initial_sidebar_state="collapsed"
)


# ==========================================
# SECRETS
# ==========================================

try:

    GEMINI_API_KEY = st.secrets[
        "GEMINI_API_KEY"
    ]

    GMAIL_USER = st.secrets[
        "GMAIL_USER"
    ]

    GMAIL_PASSWORD = st.secrets[
        "GMAIL_APP_PASSWORD"
    ]

    RECIPIENT_EMAIL = st.secrets[
        "RECIPIENT_EMAIL"
    ]

except KeyError:

    st.error(
        "🚨 Missing Streamlit secrets."
    )

    st.stop()


# ==========================================
# GEMINI CONFIG
# ==========================================

genai.configure(
    api_key=GEMINI_API_KEY
)

model = genai.GenerativeModel(
    "gemini-1.5-flash"
)


# ==========================================
# GLOBAL STYLES
# ==========================================

def inject_styles():

    st.markdown("""
    <style>

    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');

    :root {
        --accent: #E8FF47;
        --surface: #0D0D0D;
        --surface-card: #1C1C1C;
        --border: rgba(255,255,255,0.08);
        --text-primary: #F5F5F5;
        --text-secondary: #9A9A9A;
        --success: #4EFFA8;
        --danger: #FF5A5A;
        --radius: 14px;
        --radius-lg: 22px;
    }

    .stApp,
    .main,
    section.main {
        background: var(--surface) !important;
    }

    .block-container {
        max-width: 760px !important;
        padding: 2rem 1.5rem !important;
    }

    footer,
    header {
        display: none !important;
    }

    html,
    body,
    p,
    span,
    div {
        font-family: 'DM Sans', sans-serif;
        color: var(--text-primary);
    }

    h1,
    h2,
    h3 {
        font-family: 'Syne', sans-serif;
    }

    .hero-title {
        font-size: clamp(2.6rem, 7vw, 4rem);
        font-weight: 800;
        line-height: 1;
        text-align: center;
        margin-bottom: 1rem;
    }

    .accent {
        color: var(--accent);
    }

    .hero-sub {
        text-align: center;
        color: var(--text-secondary);
        line-height: 1.7;
        margin-bottom: 2.5rem;
    }

    .hero-badge {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
        background: rgba(232,255,71,0.08);
        border: 1px solid rgba(232,255,71,0.25);
        color: var(--accent);
        padding: 6px 14px;
        border-radius: 999px;
        font-size: 12px;
        margin-bottom: 1.5rem;
    }

    .section-heading {
        font-size: 1.15rem;
        font-weight: 700;
        margin-bottom: 0.25rem;
    }

    .section-sub {
        color: var(--text-secondary);
        margin-bottom: 1rem;
        font-size: 0.95rem;
    }

    .gps-box {
        background: rgba(78,255,168,0.08);
        border: 1px solid rgba(78,255,168,0.25);
        border-radius: var(--radius);
        padding: 1rem;
        margin-bottom: 1.5rem;
    }

    .result-card {
        border-radius: var(--radius-lg);
        padding: 1.4rem;
        margin-top: 1.25rem;
    }

    .positive {
        background: rgba(255,90,90,0.08);
        border: 1px solid rgba(255,90,90,0.25);
    }

    .negative {
        background: rgba(78,255,168,0.06);
        border: 1px solid rgba(78,255,168,0.2);
    }

    .result-label {
        font-weight: 700;
        margin-bottom: 0.5rem;
    }

    .result-text {
        line-height: 1.7;
    }

    .stButton button {
        background: var(--accent) !important;
        color: black !important;
        border: none !important;
        border-radius: 12px !important;
        font-weight: 700 !important;
        padding: 0.7rem 1.5rem !important;
    }

    </style>
    """, unsafe_allow_html=True)


inject_styles()


# ==========================================
# EXIF HELPERS
# ==========================================

def change_to_rational(number):

    deg = int(number)

    min_float = (
        (number - deg) * 60
    )

    minute = int(min_float)

    sec = round(
        (min_float - minute) * 60,
        4
    )

    return [
        float(deg),
        float(minute),
        float(sec)
    ]


def add_geotag_to_image(
    image_buffer,
    lat,
    lon
):

    img = Image.open(image_buffer)

    gps_info = {}

    lat_ref = (
        "N"
        if lat >= 0
        else "S"
    )

    lon_ref = (
        "E"
        if lon >= 0
        else "W"
    )

    gps_info[1] = lat_ref

    gps_info[2] = change_to_rational(
        abs(lat)
    )

    gps_info[3] = lon_ref

    gps_info[4] = change_to_rational(
        abs(lon)
    )

    exif = img.getexif()

    exif[0x8825] = gps_info

    output_buffer = io.BytesIO()

    img.save(
        output_buffer,
        format="JPEG",
        exif=exif
    )

    output_buffer.seek(0)

    return output_buffer


# ==========================================
# EMAIL FUNCTION
# ==========================================

def send_notification_email(
    lat,
    lon,
    analysis
):

    recipients = [
        email.strip()
        for email
        in RECIPIENT_EMAIL.split(",")
    ]

    msg = EmailMessage()

    maps_link = (
        f"https://www.google.com/maps?q={lat},{lon}"
    )

    body = f"""
🚨 POTHOLE ALERT

Latitude: {lat}
Longitude: {lon}

Google Maps:
{maps_link}

AI ANALYSIS:
{analysis}
"""

    msg.set_content(body)

    msg["Subject"] = (
        "🚨 Smart Pothole Alert"
    )

    msg["From"] = GMAIL_USER

    msg["To"] = ", ".join(recipients)

    with smtplib.SMTP_SSL(
        "smtp.gmail.com",
        465
    ) as smtp:

        smtp.login(
            GMAIL_USER,
            GMAIL_PASSWORD
        )

        smtp.send_message(
            msg,
            to_addrs=recipients
        )


# ==========================================
# SESSION STATE
# ==========================================

if "app_started" not in st.session_state:

    st.session_state.app_started = False

if "location_data" not in st.session_state:

    st.session_state.location_data = None


# ==========================================
# LANDING PAGE
# ==========================================

if not st.session_state.app_started:

    st.markdown("<br>", unsafe_allow_html=True)

    try:

        logo = Image.open(
            "logo_smart.png"
        )

        st.image(
            logo,
            use_container_width=True
        )

    except:
        pass

    st.markdown("""
    <div style="text-align:center">
        <div class="hero-badge">
            ◉ Edge AI · Live GPS · Gemini Vision
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <h1 class="hero-title">
        Smart<br>
        <span class="accent">
            Pothole
        </span><br>
        Reporter
    </h1>
    """, unsafe_allow_html=True)

    st.markdown("""
    <p class="hero-sub">
        Capture road damage, verify it using Gemini AI,
        attach live GPS coordinates, and automatically
        notify city authorities in seconds.
    </p>
    """, unsafe_allow_html=True)

    if st.button(
        "Launch Application →",
        use_container_width=True
    ):

        st.session_state.app_started = True

        st.rerun()


# ==========================================
# MAIN APPLICATION
# ==========================================

else:

    # ======================================
    # TOP BAR
    # ======================================

    col1, col2 = st.columns([4, 1])

    with col1:

        st.markdown("""
        <h2 style="
            font-family:Syne,sans-serif;
            margin-top:0;
        ">
            🛡️ Smart Pothole Reporter
        </h2>
        """, unsafe_allow_html=True)

    with col2:

        if st.button("← Back"):

            st.session_state.app_started = False

            st.session_state.location_data = None

            st.rerun()

    # ======================================
    # STEP 1 — GPS
    # ======================================

    st.markdown("""
    <div class="section-heading">
        Step 1 — Acquire GPS Coordinates
    </div>

    <div class="section-sub">
        Grant browser location permission.
    </div>
    """, unsafe_allow_html=True)

    # FIXED GEOLOCATION FLOW
    if st.session_state.location_data is None:

        location_data = streamlit_geolocation()

        if (
            location_data
            and location_data.get("latitude")
            is not None
        ):

            st.session_state.location_data = (
                location_data
            )

            st.rerun()

    location_data = (
        st.session_state.location_data
    )

    # ======================================
    # GPS SUCCESS
    # ======================================

    if (
        location_data
        and location_data.get("latitude")
        is not None
    ):

        lat = location_data["latitude"]

        lon = location_data["longitude"]

        st.markdown(
            f"""
            <div class="gps-box">

                <div style="
                    color:#4EFFA8;
                    font-weight:700;
                    margin-bottom:0.3rem;
                ">
                    GPS Locked
                </div>

                <div>
                    {lat:.6f}, {lon:.6f}
                </div>

            </div>
            """,
            unsafe_allow_html=True
        )

        # ==================================
        # STEP 2 — CAMERA
        # ==================================

        st.markdown("""
        <div class="section-heading">
            Step 2 — Capture Road Damage
        </div>

        <div class="section-sub">
            Photograph the pothole clearly.
        </div>
        """, unsafe_allow_html=True)

        camera_photo = st.camera_input(
            "",
            label_visibility="collapsed"
        )

        # ==================================
        # IMAGE CAPTURED
        # ==================================

        if camera_photo is not None:

            with st.spinner(
                "Embedding GPS metadata..."
            ):

                geotagged_image_file = (
                    add_geotag_to_image(
                        camera_photo,
                        lat,
                        lon
                    )
                )

            st.success(
                "✅ GPS metadata embedded."
            )

            st.markdown("---")

            # ==============================
            # STEP 3 — ANALYSIS
            # ==============================

            st.markdown("""
            <div class="section-heading">
                Step 3 — Analyse & Dispatch
            </div>

            <div class="section-sub">
                Run Gemini AI analysis and
                automatically notify authorities.
            </div>
            """, unsafe_allow_html=True)

            if st.button(
                "🚀 Analyse & Send Report",
                use_container_width=True
            ):

                with st.spinner(
                    "Analyzing image..."
                ):

                    try:

                        geotagged_image_file.seek(0)

                        prompt = (
                            "You are a strict city "
                            "infrastructure monitoring system. "
                            "Determine whether this image "
                            "contains a real pothole or "
                            "severe road damage. "
                            "Reply ONLY using: "
                            "'YES: explanation' "
                            "or "
                            "'NO: explanation'."
                        )

                        response = (
                            model.generate_content(
                                [
                                    prompt,
                                    {
                                        "mime_type":
                                        "image/jpeg",

                                        "data":
                                        geotagged_image_file.getvalue()
                                    }
                                ]
                            )
                        )

                        verdict = (
                            response.text.strip()
                        )

                    except Exception as e:

                        st.error(
                            f"Gemini Analysis Error: {e}"
                        )

                        st.stop()

                # ==========================
                # RESULT CARD
                # ==========================

                is_pothole = (
                    verdict.upper().startswith(
                        "YES"
                    )
                )

                card_class = (
                    "positive"
                    if is_pothole
                    else "negative"
                )

                label_text = (
                    "⚠ Pothole Detected"
                    if is_pothole
                    else "✓ No Damage Found"
                )

                label_color = (
                    "#FF5A5A"
                    if is_pothole
                    else "#4EFFA8"
                )

                st.markdown(
                    f"""
                    <div class="
                        result-card
                        {card_class}
                    ">

                        <div
                            class="result-label"
                            style="
                                color:{label_color}
                            "
                        >
                            {label_text}
                        </div>

                        <div class="result-text">
                            {verdict}
                        </div>

                    </div>
                    """,
                    unsafe_allow_html=True
                )

                # ==========================
                # EMAIL ALERT
                # ==========================

                if is_pothole:

                    with st.spinner(
                        "Sending report..."
                    ):

                        try:

                            send_notification_email(
                                lat,
                                lon,
                                verdict
                            )

                            st.balloons()

                            st.success(
                                "📩 Authorities "
                                "have been notified."
                            )

                        except Exception as e:

                            st.error(
                                f"SMTP Error: {e}"
                            )

                else:

                    st.success(
                        "🌿 No pothole detected."
                    )

    # ======================================
    # WAITING FOR GPS
    # ======================================

    else:

        st.markdown("""
        <div style="
            background:#1C1C1C;
            border:1px solid rgba(255,255,255,0.08);
            border-radius:20px;
            padding:1.5rem;
            text-align:center;
            margin-top:1rem;
        ">

            <div style="
                font-size:2rem;
                margin-bottom:0.75rem;
            ">
                📍
            </div>

            <p style="
                font-weight:700;
                margin-bottom:0.4rem;
                color:white;
            ">
                Waiting for GPS Access
            </p>

            <p style="
                color:#9A9A9A;
                margin:0;
            ">
                Allow browser location permission
                to continue.
            </p>

        </div>
        """, unsafe_allow_html=True)
