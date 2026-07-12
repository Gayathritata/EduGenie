import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
try:
    client = genai.Client(api_key=os.environ.get('GEMINI_API_KEY'))
    for m in client.models.list():
        if 'flash' in m.name.lower():
            print(m.name)
except Exception as e:
    print("Error:", e)
