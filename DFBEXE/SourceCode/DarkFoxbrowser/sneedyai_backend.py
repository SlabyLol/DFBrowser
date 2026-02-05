import os
from PySide6.QtCore import QObject, Slot
from openai import OpenAI

# OpenAI API Key aus Environment Variable
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY not set in environment variables!")

client = OpenAI(api_key=api_key)

class SneedyAI(QObject):
    @Slot(str, result=str)
    def ask(self, message):
        if not message.strip():
            return ""
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are SneedyAI, a helpful assistant inside DarkFoxBrowser."},
                    {"role": "user", "content": message}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error: {str(e)}"
