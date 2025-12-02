import streamlit as st
import google.generativeai as genai

st.title("🔑 API Key Diagnostic")

# 1. Setup Gemini
if "GEMINI_API_KEY" in st.secrets:
    my_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=my_key)
    st.write(f"Key found! (Ends in: ...{my_key[-5:]})")
else:
    st.error("No API Key found in secrets!")

# 2. Ask Google what models are available
try:
    st.write("Contacting Google to list models...")
    available_models = []
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            available_models.append(m.name)
            
    st.success("Success! Here are the models your key can see:")
    st.code(available_models)

except Exception as e:
    st.error(f"DIAGNOSTIC FAILED: {e}")
    st.write("If you see a 'User location is not supported' error, we know the issue is the UK region.")
