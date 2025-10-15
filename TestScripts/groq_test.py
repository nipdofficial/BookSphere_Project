import os
import requests
from dotenv import load_dotenv

# Load .env
load_dotenv(dotenv_path=r"C:/Users/MSI/Desktop/Book Sphere/.env")

# Correct: use the ENV VAR NAME
api_key = os.getenv("GROQ_API_KEY")

url = "https://api.groq.com/openai/v1/chat/completions"
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {api_key}"
}
data = {
    "model": "meta-llama/llama-4-scout-17b-16e-instruct",
    "messages": [
        {"role": "user", "content": "Explain the importance of fast language models"}
    ]
}

response = requests.post(url, headers=headers, json=data)
print(response.json())
