from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel 

from backend.agentCore.core import JaegarAgent
from backend.agentInteraction.interactionCore import InteractionCore

agent = JaegarAgent()
interaction = InteractionCore(agent)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class MessageRequest(BaseModel):
    message: str

@app.get("/")
def root():
    return {"message": "Jaegar Python backend is running."}

@app.post("/message")
def message_received(request: MessageRequest):
    try:
        response = interaction.process_message(request.message)

        return {"message": response}

    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

# if __name__ == "__main__":
#     main()