import streamlit as st
import pandas as pd
import google.generativeai as genai
from streamlit_gsheets import GSheetsConnection

# 1. Page Config (Makes it look nice)
st.set_page_config(page_title="Company Assistant", layout="centered")
st.title("📊 Data Assistant")

# 2. Setup Gemini
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash')

# 3. Connect to Google Sheets
# We use ttl=600 so it checks for new data every 10 minutes (prevents freezing)
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data():
    try:
        # REPLACE 'Stock', 'Product', 'Project' with your actual tab names!
        df_stock = conn.read(worksheet="Stock", ttl=60)
        df_product = conn.read(worksheet="Product", ttl=60)
        df_project = conn.read(worksheet="Project", ttl=60)
        
        # Combine data into a readable string for the AI
        combined_data = f"""
        Here is the current Stock Data:
        {df_stock.to_string(index=False)}
        
        Here is the Product Details:
        {df_product.to_string(index=False)}
        
        Here is the Project Info:
        {df_project.to_string(index=False)}
        """
        return combined_data
    except Exception as e:
        st.error(f"Error reading sheet: {e}")
        return ""

# 4. Chat Interface
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 5. The Logic
if prompt := st.chat_input("Ask about stock, products, or projects..."):
    # User message
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # AI Process
    with st.spinner("Analyzing spreadsheet..."):
        data_context = get_data()
        
        if data_context:
            full_prompt = f"""
            You are a helpful business assistant. 
            Answer the user's question based ONLY on the data provided below.
            If the answer is not in the data, say "I don't see that in the sheets."
            
            DATA:
            {data_context}
            
            USER QUESTION:
            {prompt}
            """
            
            response = model.generate_content(full_prompt)
            ai_reply = response.text
            
            # AI Reply
            with st.chat_message("assistant"):
                st.markdown(ai_reply)
            st.session_state.messages.append({"role": "assistant", "content": ai_reply})
