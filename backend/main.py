import os
from openai import OpenAI 
from fastapi import FastAPI, UploadFile
from dotenv import load_dotenv
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import chromadb
import uuid


load_dotenv(override=True)
app = FastAPI()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY") , base_url=os.getenv("OPENAI_BASE_URL"))
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=2000,
    chunk_overlap=200,
)
chroma_client = chromadb.PersistentClient(path="./chroma_data")
collection = chroma_client.get_or_create_collection(name="study_materials")

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
    response = client.embeddings.create(input=chunks, model="text-embedding-3-small")
    document_id = uuid.uuid4()
    chunkids = []
    embeddings = []
    documents = []
    metadata = []
    for i, chunk in enumerate(chunks):
        chunkids.append(f"{document_id}_chunk_{i}")
        embeddings.append(response.data[i].embedding)
        documents.append(chunk) 
        metadata.append({"document_id": str(document_id)})

    collection.add(ids=chunkids, documents=documents, embeddings=embeddings, metadatas=metadata)
    return {"filename": file.filename, "chunks_len": len(chunks), "response_len": len(response.data)}

result = collection.get(limit=2)
print(result)