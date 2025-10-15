from dotenv import load_dotenv
import os

# Load .env
load_dotenv(dotenv_path=r"C:/Users/MSI/Desktop/Book Sphere/.env")

# Correct: use the ENV VAR NAME, not the key itself
groq_key = os.getenv("GROQ_API_KEY")

print("Groq Key:", groq_key)
