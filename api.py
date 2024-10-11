
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import sys
import os


sys.path.append(os.path.join(os.path.dirname(__file__), "/Users/adamkabak/Development/GraphRAG-3/venv/lib/python3.11/site-packages"))
from chatbot import generate_chat_response  # Import the chatbot logic


app = FastAPI()

# Allow requests from your React frontend
origins = ["http://localhost:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    # allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define the request body model
class ChatRequest(BaseModel):
    prompt: str
    use_groq: bool = False  # Optional flag to switch between OpenAI and Groq

@app.post("/chat")
async def chat(chat_request: ChatRequest):
    user_prompt = chat_request.prompt
    use_groq = chat_request.use_groq

    # Call your function to get chatbot response
    response = generate_chat_response(user_prompt, use_groq=use_groq)
    return {"response": response}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
