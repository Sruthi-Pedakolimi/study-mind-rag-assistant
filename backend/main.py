import os
from openai import OpenAI 
from fastapi import FastAPI, UploadFile
from dotenv import load_dotenv
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter


load_dotenv(override=True)
app = FastAPI()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY") , base_url=os.getenv("OPENAI_BASE_URL"))
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=2000,
    chunk_overlap=200,
)

@app.post("/upload")
async def get_file(file: UploadFile):
    
    file_content_type = file.content_type
    if file_content_type != "application/pdf":
        return {"error": "Only PDF files are supported"}
 
    text = ""
    reader = PdfReader(file.file)
    for page in reader.pages:
        extracted_page = page.extract_text()
        # avoid none extraction
        if  extracted_page:
            text += extracted_page
    
    chunks = text_splitter.split_text(text)
            
    return {"filename": file.filename, "chunks": chunks}

