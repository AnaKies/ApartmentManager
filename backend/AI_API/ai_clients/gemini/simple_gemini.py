import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
# Configure the client with your API key
genai.configure(api_key=API_KEY)

# Specify the model to use
model = genai.GenerativeModel("gemini-2.0-flash-exp")

# Prompt the user for input
user_prompt = "Gib mir 3 völlig verschiedene Verwendungen für einen Ziegelstein."

# Generate a response using the Gemini API
response = model.generate_content(user_prompt,
         generation_config=genai.types.GenerationConfig(
         temperature=1.0,
         max_output_tokens=10  # Limit auf ca. 100 Tokens
    ))

print("Generated text:\n", response.text)