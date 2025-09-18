import anthropic
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("CLAUDE_API_KEY")

# Initialize the Anthropic client
client = anthropic.Anthropic(api_key=API_KEY)

# Specify the model to use
model = "claude-3-5-sonnet-latest"

# Prompt the user for input
user_prompt = "What is GenAI?"

# Define the system message to set the behavior of the assistant
system_message = "You are a helpful assistant. Provide concise and relevant responses."

# Create the message payload
messages = [
    {"role": "user", "content": user_prompt}
]

# Generate a response using the Claude API
response = client.messages.create(
    model=model,
    system=system_message,
    messages=messages,
    max_tokens=150,
    temperature=0.7
)

# Display the generated text
print("Generated text:\n", response.content[0].text)