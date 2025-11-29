import os
from google import genai
from dotenv import load_dotenv

class UserLLMClient:
    def __init__(self):
        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")
        self.client = genai.Client(api_key=api_key)
        self.chat_history = [] # List of {"role": "user"|"model", "content": str}

    def generate_next_message(self, goal: str, last_system_response: str = None) -> str:
        """
        Generates the next user message based on the goal and conversation history.
        """
        if last_system_response:
            # Append system response to history (as 'model' because it's the interlocutor)
            # Wait, for the User LLM, the interlocutor is the system.
            # Let's keep it simple: 'System' and 'User' labels in the prompt.
            self.chat_history.append({"role": "System", "content": last_system_response})
        
        system_instruction = f"""
        You are a user testing an apartment management system.
        Your current goal is: {goal}
        
        You are interacting with a chatbot that manages the system.
        Generate a natural language request to achieve your goal.
        
        Rules:
        1. If the last system response indicates that the goal has been successfully achieved (e.g., "Person created", "Data updated", or showing the requested data), output exactly "DONE".
        2. If the system asks for required information (like name, email, etc.), provide it.
        3. Keep your responses concise and natural.
        4. Do not output "DONE" if the system is asking for confirmation or more details.
        """
        
        prompt = f"{system_instruction}\n\nConversation History:\n"
        for msg in self.chat_history:
            prompt += f"{msg['role']}: {msg['content']}\n"
            
        prompt += "\nUser (You):"
        
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            text = response.text.strip()
        except Exception as e:
            print(f"Error generating content: {e}")
            print(f"Error generating content: {e}")
            return "WAIT"
        
        # Remove "User (You):" prefix if generated
        if text.startswith("User (You):"):
            text = text[len("User (You):"):].strip()
            
        if text != "DONE":
            self.chat_history.append({"role": "User", "content": text})
            
        return text

    def reset_history(self):
        self.chat_history = []
