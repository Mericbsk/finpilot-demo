import os

import google.generativeai as genai
import streamlit as st

# Try to get key from secrets or env
api_key = os.environ.get("GOOGLE_API_KEY")
if not api_key:
    try:
        import toml

        secrets = toml.load(".streamlit/secrets.toml")
        api_key = secrets.get("GOOGLE_API_KEY")
    except:
        pass

if not api_key:
    print("No API key found.")
else:
    genai.configure(api_key=api_key)
    try:
        print("Available models:")
        for m in genai.list_models():
            if "generateContent" in m.supported_generation_methods:
                print(m.name)
    except Exception as e:
        print(f"Error listing models: {e}")
