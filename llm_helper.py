import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

GROQ_API_KEY=os.getenv("GROQ_API_KEY")
MODEL=os.getenv("MODEL")

llm = ChatGroq(
    groq_api_key=GROQ_API_KEY, 
    model_name=MODEL
)

if __name__ == "__main__":
    response = llm.invoke("Hello, Groq! what is the capital of Iran?")
    print(response.content)