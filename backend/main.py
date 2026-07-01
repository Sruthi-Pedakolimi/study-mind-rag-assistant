import os
from openai import OpenAI 
from fastapi import FastAPI, UploadFile
from dotenv import load_dotenv


load_dotenv(override=True)
app = FastAPI()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY") , base_url=os.getenv("OPENAI_BASE_URL"))

@app.post("/upload")
async def get_file(file: UploadFile):
    uploaded_filename = file.filename
    return {"filename": uploaded_filename, "status": "received"}

