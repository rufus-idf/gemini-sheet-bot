import streamlit as st
import pandas as pd
import google.generativeai as genai
from streamlit_gsheets import GSheetsConnection

# 1. Page Config
st.set_page_config(page_title="Inventory Assistant", layout="centered")
st.title("📦 Stock, Projects & Prices")

# 2. Setup Gemini
# Using the Lite model to avoid speed limits
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('models/gemini-2.0-flash-lite-preview-02-05')
else:
    st.error("Missing Gemini API Key in Secrets")

# 3. Connect to Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data():
    """
    Reads 5 tabs: Wood, Components, Products, Projects, and PRICES.
    Limits to 50 rows each to prevent crashing.
    """
    try:
        all_data = []

        # --- TAB 1: Wood Stock ---
        try:
            df_wood = conn.read(worksheet="Wood Stock", ttl=60)
            df_wood = df_wood.head(50)
            all_data.append(f"--- WOOD STOCK (Top 50) ---\n{df_wood.to_string(index=False)}")
        except:
            all_data.append("Could not find tab 'Wood Stock'.")

        # --- TAB 2: Component Stock ---
        try:
            df_comp = conn.read(worksheet="Component Stock", ttl=60)
            df_comp = df_comp.head(50)
            all_data.append(f"--- COMPONENT STOCK (Top 50) ---\n{df_comp.to_string(index=False)}")
        except:
            all_data.append("Could not find tab 'Component Stock'.")

        # --- TAB 3: Products ---
        try:
            df_prod = conn.read(worksheet="Products", ttl=60)
            df_prod = df_prod.head(50)
            all_data.append(f"--- PRODUCTS (Top 50) ---\n{df_prod.to_string(index=False)}")
        except:
            all_data.append("Could not find tab 'Products'.")

        # --- TAB 4: Project Overview ---
        try:
            df_proj = conn.read(worksheet="Project Overview", ttl=60)
            df_proj = df_proj.head(50)
            all_data.append(f"--- PROJECT OVERVIEW (Top 50) ---\n{df_proj.to_string(index=False)}")
        except:
            all_data.append("Could not find tab 'Project Overview'.")

        # --- TAB 5: Prices (NEW) ---
        try:
            df_price = conn.read(worksheet="Prices", ttl=60)
            df_price = df_price.head(50)
            # We explicitly label this so the AI knows these are buy links
            all_data.append(f"--- PRICES & BUYING LINKS (Top 50) ---\n{df_price.to_string(index=False)}")
        except:
            all_data.append("Could not find tab 'Prices'.")
        
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
if prompt := st.chat_input("Ask about stock, prices, or links..."):
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.spinner("Checking stock and prices..."):
        data_context = get_data()
        
        if data_context:
            full_prompt = f"""
            You are an inventory and purchasing assistant. 
            Answer the question based ONLY on the data below.
            
            IMPORTANT:
            - If the user asks about cost or where to buy, provide the price and the exact URL link from the 'Prices' section.
            - If the URL is in the data, do not make one up. Use the one provided.
            
            DATA (Truncated to first 50 rows):
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
