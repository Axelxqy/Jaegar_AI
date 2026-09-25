from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel 

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
    return {"message": f"Received message: {request.message}"}


# if __name__ == "__main__":
#     main()