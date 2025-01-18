import openai
import os
from dotenv import load_dotenv

# Explicitly load .env from the correct directory
load_dotenv(dotenv_path=os.path.join("instance", ".env"))

# Check if the API key is loaded
print("Loaded API Key:", os.getenv("OPENAI_API_KEY"))

# Set the OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Test the OpenAI API with gpt-4 or gpt-3.5-turbo
try:
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",  # Replace with "gpt-4" if you want GPT-4
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say hello"},
        ],
        max_tokens=10
    )
    print(response["choices"][0]["message"]["content"].strip())
except Exception as e:
    print("Error:", e)