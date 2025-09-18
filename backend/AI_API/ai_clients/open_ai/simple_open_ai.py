import openai
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPEN_AI_KEY")

client = openai.OpenAI(api_key=API_KEY)

# Specify the model to use
model = "gpt-4o-mini"

# Prompt the user for input
user_prompt = "What is GenAI?"

# Generate a response using the OpenAI API
response = client.chat.completions.create(
    model=model,
    messages=[
        {"role": "developer", "content": "You are a helpful assistant."},
        {"role": "user", "content": user_prompt},
        {"role": "assistant", "content": "GenAI is a vegetable!"},
        {"role": "user", "content": "Are you sure? What made you think of that?"}
    ],
    temperature=0.7,
    max_tokens=150
)

# Display the generated text
print("Generated text:\n", response.choices[0].message.content)