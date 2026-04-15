import os
from dotenv import load_dotenv
import streamlit as st

# -----------------------------
# Page setup
# -----------------------------
st.set_page_config(
    page_title="PLL Fantasy Assistant",
    page_icon="🥍",
    layout="wide"
)

st.title("🥍 PLL Fantasy Assistant")
st.caption("Ask start/sit, rankings, and player comparison questions using 2025 PLL data.")

# -----------------------------
# Safe import of backend code
# -----------------------------
try:
    from pll_assistant import FantasyAssistant, LeagueSettings
except Exception as e:
    st.error(f"Failed to import pll_assistant.py: {e}")
    st.stop()

# -----------------------------
# Load environment variables
# -----------------------------
load_dotenv()
api_key = st.secrets.get("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY"))

if not api_key:
    st.error("OPENAI_API_KEY not found. Make sure your .env file is in the same folder as app.py.")
    st.stop()

# -----------------------------
# Create assistant once
# -----------------------------
@st.cache_resource
def get_assistant():
    return FantasyAssistant(api_key=api_key, model="gpt-5.4")

assistant = get_assistant()

# -----------------------------
# Sidebar: League settings
# -----------------------------
st.sidebar.header("League Settings")

league_format = st.sidebar.selectbox(
    "League Format",
    ["points_leader", "head_to_head"],
    index=0
)

league_size = st.sidebar.selectbox(
    "League Size",
    [4, 6, 8, 10, 12],
    index=2
)

salary_cap_input = st.sidebar.text_input(
    "Salary Cap (optional)",
    value=""
)

weekly_reset = st.sidebar.checkbox(
    "Weekly lineup reset",
    value=True
)

st.sidebar.divider()
st.sidebar.subheader("Default PLL Lineup")
st.sidebar.caption("2 Attack • 2 Midfield • 1 Faceoff • 1 Defense • 1 Goalie")

# -----------------------------
# Sidebar: Data options
# -----------------------------
st.sidebar.divider()
st.sidebar.subheader("Data")

st.sidebar.info("Using built-in 2025 PLL datasets:\n- Regular Season\n- Postseason\n- Champ Series")

uploaded_file = st.sidebar.file_uploader(
    "Upload a replacement CSV (optional)",
    type=["csv"]
)

if uploaded_file is not None:
    st.sidebar.warning(
        "Your current backend load_data() uses the built-in 3 PLL CSV files. "
        "This uploaded file will not be used unless you update the backend to support it."
    )

# -----------------------------
# Example questions
# -----------------------------
sample_questions = [
    "Based on 2025 performance, who are the best PLL fantasy players to start?",
    "Who are the best attackmen in PLL fantasy based on 2025 data?",
    "Compare the top PLL goalies for fantasy.",
    "Which midfielders offer the best mix of floor and upside?",
    "Who are the best faceoff specialists for PLL fantasy?",
    "Give me 10 undervalued PLL fantasy players based on the data.",
]

with st.expander("Example questions"):
    for q in sample_questions:
        st.write(f"- {q}")

# -----------------------------
# Main input
# -----------------------------
question = st.text_area(
    "Ask your PLL fantasy question",
    value="Based on 2025 performance, who are the best PLL fantasy players to start?",
    height=140
)

ask_button = st.button("Get Advice", type="primary")

# -----------------------------
# Helper: load data
# -----------------------------
def load_player_data():
    """
    Load the built-in PLL datasets through the backend.
    """
    return assistant.load_data()

# -----------------------------
# Run query
# -----------------------------
if ask_button:
    try:
        load_player_data()

        salary_cap = None
        if salary_cap_input.strip():
            salary_cap = int(salary_cap_input.strip())

        league = LeagueSettings(
            league_format=league_format,
            league_size=league_size,
            salary_cap=salary_cap,
            weekly_reset=weekly_reset,
        )

        with st.spinner("Analyzing 2025 PLL player data..."):
            answer = assistant.ask_question(question, league)

        st.subheader("Recommendation")
        st.write(answer)

    except ValueError as e:
        st.error(f"Invalid input: {e}")

    except FileNotFoundError as e:
        st.error(str(e))

    except Exception as e:
        st.error(f"Something went wrong: {e}")