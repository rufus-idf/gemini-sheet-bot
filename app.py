import streamlit as st
import pandas as pd
import google.generativeai as genai
from streamlit_gsheets import GSheetsConnection

# 1. Page Config
st.set_page_config(page_title="Inventory Assistant", layout="centered")

# --- CSS HACK: HIDE UI ELEMENTS & MAKE TRANSPARENT ---
hide_streamlit_style = """
<style>
    /* 1. Hide the top header bar (the colored line & hamburger menu) */
    header {visibility: hidden;}
    
    /* 2. Hide the footer "Made with Streamlit" */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* 3. Attempt to make the main background transparent */
    /* Note: If Google Sites forces a white background, this might show white */
    .stApp {
        background-color: transparent;
    }
    
    /* 4. Remove top padding so the chat starts at the top of the box */
    .block-container {
        padding-top: 0rem;
        padding-bottom: 0rem;
    }
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# 2. Setup Gemini
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('models/gemini-2.0-flash-lite-preview-02-05')
else:
    st.error("Missing Gemini API Key in Secrets")

# 3. Connect to Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data():
    """
    Reads 5 tabs. We reduced rows to 40 per tab to ensure Wood Stock doesn't get cut off.
    """
    try:
        all_data = []

        # --- TAB 1: Wood Stock ---
        try:
            df_wood = conn.read(worksheet="Wood Stock", ttl=60)
            df_wood = df_wood.head(40)
            # We add a specific description so the AI knows this is raw material
            all_data.append(f"--- SECTION 1: WOOD STOCK (Raw Materials like Oak, Pine, Sheets) ---\n{df_wood.to_string(index=False)}")
        except:
            all_data.append("Could not find tab 'Wood Stock'.")

        # --- TAB 2: Component Stock ---
        try:
            df_comp = conn.read(worksheet="Component Stock", ttl=60)
            df_comp = df_comp.head(40)
            all_data.append(f"--- SECTION 2: COMPONENT STOCK (Hardware, Screws, etc) ---\n{df_comp.to_string(index=False)}")
        except:
            all_data.append("Could not find tab 'Component Stock'.")

        # --- TAB 3: Products ---
        try:
            df_prod = conn.read(worksheet="Products", ttl=60)
            df_prod = df_prod.head(40)
            all_data.append(f"--- SECTION 3: FINISHED PRODUCTS ---\n{df_prod.to_string(index=False)}")
        except:
            all_data.append("Could not find tab 'Products'.")

        # --- TAB 4: Project Overview ---
        try:
            df_proj = conn.read(worksheet="Project Overview", ttl=60)
            df_proj = df_proj.head(40)
            all_data.append(f"--- SECTION 4: PROJECT OVERVIEW ---\n{df_proj.to_string(index=False)}")
        except:
            all_data.append("Could not find tab 'Project Overview'.")

        # --- TAB 5: Prices ---
        try:
            df_price = conn.read(worksheet="Prices", ttl=60)
            df_price = df_price.head(40)
            all_data.append(f"--- SECTION 5: BUYING LINKS & PRICES ---\n{df_price.to_string(index=False)}")
        except:
            all_data.append("Could not find tab 'Prices'.")

        try:
            df_proj = conn.read(worksheet="Wood Usage", ttl=60)
            df_proj = df_proj.head(40)
            all_data.append(f"--- SECTION 4: Wood Usage ---\n{df_proj.to_string(index=False)}")
        except:
            all_data.append("Could not find tab 'Wood Usage'.")
        
        return "\n\n".join(all_data)

    except Exception as e:
        st.error(f"Major Error reading sheet: {e}")
        return ""

# 4. Debug Feature (Use this to check if Wood data is loading)
with st.expander("🕵️‍♂️ Debug: See what the AI sees"):
    if st.button("Load Raw Data"):
        with st.spinner("Fetching data..."):
            raw_text = get_data()
            st.text_area("Raw Data sent to AI:", raw_text, height=300)

# 5. Chat Interface
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask about wood, stock, or prices..."):
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.spinner("Checking..."):
        data_context = get_data()
        
        if data_context:
            full_prompt = f"""
            You are an intelligent inventory manager. You have access to 5 sections of data:
            1. Wood Stock (Raw materials)
            2. Component Stock (Hardware)
            3. Finished Products
            4. Projects
            5. Prices & Links
            
            YOUR JOB:
            Answer the user's question by looking at ALL sections above.
            - If they ask for "Stock", check Wood, Components, and Products.
            - If they ask for "Prices" or "Links", check the Prices section.
            
            DATA:
            {data_context}
            
            USER QUESTION:
            {prompt}
            """
            
            try:
                response = model.generate_content(full_prompt)
                ai_reply = response.text
            except Exception as e:
                ai_reply = f"Gemini Error: {e}"
        else:
            ai_reply = "I couldn't read any data from the sheets."

        st.chat_message("assistant").markdown(ai_reply)
        st.session_state.messages.append({"role": "assistant", "content": ai_reply})
