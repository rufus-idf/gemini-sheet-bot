import streamlit as st
import pandas as pd
import google.generativeai as genai
from streamlit_gsheets import GSheetsConnection

# 1. Page Config
st.set_page_config(page_title="Inventory Assistant", layout="centered")
st.title("📦 Stock & Project Assistant")

# 2. Setup Gemini
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-pro')
else:
    st.error("Missing Gemini API Key in Secrets")

# 3. Connect to Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data():
    """
    Reads specific tabs: 'Wood Stock', 'Component Stock', 'Products', 'Project Overview'
    """
    try:
        # We use a list to store text from all sheets
        all_data = []

        # --- TAB 1: Wood Stock ---
        # We try to read it. If the name is slightly wrong (like "Wood Stock "), we catch the error.
        try:
            df_wood = conn.read(worksheet="Wood Stock", ttl=60)
            all_data.append(f"WOOD STOCK DATA:\n{df_wood.to_string(index=False)}")
        except:
            all_data.append("Could not find tab 'Wood Stock' - check spelling.")

        # --- TAB 2: Component Stock ---
        try:
            df_comp = conn.read(worksheet="Component Stock", ttl=60)
            all_data.append(f"COMPONENT STOCK DATA:\n{df_comp.to_string(index=False)}")
        except:
            all_data.append("Could not find tab 'Component Stock'.")

        # --- TAB 3: Products ---
        try:
            df_prod = conn.read(worksheet="Products", ttl=60)
            all_data.append(f"PRODUCT DATA:\n{df_prod.to_string(index=False)}")
        except:
            all_data.append("Could not find tab 'Products'.")

        # --- TAB 4: Project Overview ---
        try:
            df_proj = conn.read(worksheet="Project Overview", ttl=60)
            all_data.append(f"PROJECT OVERVIEW:\n{df_proj.to_string(index=False)}")
        except:
            all_data.append("Could not find tab 'Project Overview'.")
        
        return "\n\n".join(all_data)

    except Exception as e:
        st.error(f"Major Error reading sheet: {e}")
        return ""

# 4. Chat Interface
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 5. User Input
if prompt := st.chat_input("Ask about wood, components, or projects..."):
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.spinner("Checking all tabs..."):
        data_context = get_data()
        
        # If we got data, ask Gemini
        if data_context:
            full_prompt = f"""
            You are an expert inventory manager. 
            Answer the user's question based ONLY on the data below.
            
            DATA FROM SHEETS:
            {data_context}
            
            USER QUESTION:
            {prompt}
            """
            
            try:
                response = model.generate_content(full_prompt)
                ai_reply = response.text
            except Exception as e:
                # ERROR FIX: This line MUST have 4 spaces of indentation
                ai_reply = f"Gemini Error: {e}"
        else:
            ai_reply = "I couldn't read any data from the sheets."

        st.chat_message("assistant").markdown(ai_reply)
        st.session_state.messages.append({"role": "assistant", "content": ai_reply})
