import os
import openai
from openai import OpenAI 
from fastapi import FastAPI, UploadFile, HTTPException
from dotenv import load_dotenv
from pypdf import PdfReader
from pypdf.errors import PdfReadError, PdfStreamError, EmptyFileError
from langchain_text_splitters import RecursiveCharacterTextSplitter
import chromadb
import uuid
from pydantic import BaseModel 
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv(override=True)
app = FastAPI()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY") , base_url=os.getenv("OPENAI_BASE_URL"))
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=2000,
    chunk_overlap=200,
)
chroma_client = chromadb.PersistentClient(path="./chroma_data")
collection = chroma_client.get_or_create_collection(name="study_materials")


class AskRequest(BaseModel):
    question: str 
    document_id: str

def build_rag_prompt(context: str, question: str) -> str:
    prompt = f"""Answer the question based only on the following context. if the answer isn't there in the context, say you dont know.
            Context: {context}
            question: {question}
            """
    return prompt

# calls the openai function
def call_openai_safely(func, *args, **kwargs):
    try:
        return func(*args, **kwargs)
    except openai.RateLimitError as e:
        logger.error(f"You exceeded your limit: {e}")
        raise HTTPException(status_code=429, detail="Service temporarily unavailable, please try again shortly")
    except openai.AuthenticationError as e:
        logger.error(f"Auth error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    except openai.BadRequestError as e:
        logger.error(f"Bad request error: {e}")
        raise HTTPException(status_code=400, detail="Your request was malformed or missing some required parameters")
    except openai.APIConnectionError as e:
        logger.error(f"Connection error: {e}")
        raise HTTPException(status_code=503, detail="Service temporarily unavailable, please try again shortly")

# extracts the text from the uploaded file
def extract_text_from_pdf(file: UploadFile) -> str:
    try:
        reader = PdfReader(file.file)
        text = ""
        for page in reader.pages:
            extracted_page = page.extract_text()
            # avoid none extraction
            if  extracted_page:
                text += extracted_page
        return text
    except (PdfReadError, PdfStreamError, EmptyFileError) as e:
        raise HTTPException(status_code=400, detail="Could not read PDF file. It may be corrupted")

   
def store_chunks_in_chromadb(document_id: uuid.UUID, chunks: list[str], response) -> None:

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


@app.post("/upload")
async def get_file(file: UploadFile):
   
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    text = extract_text_from_pdf(file)
    if not text.strip():
        raise HTTPException(status_code=400, detail="No extractable text found in the pdf")  # files like image text etc will be filtered here
    

    chunks = text_splitter.split_text(text)
    response = call_openai_safely(client.embeddings.create,input=chunks, model="text-embedding-3-small")
    document_id = uuid.uuid4()
    store_chunks_in_chromadb(document_id, chunks, response)

    return {"document_id": str(document_id)}


@app.post("/ask")
async def ask_query(request: AskRequest):

    if not request.question:
        raise HTTPException(status_code=400, detail="Empty question")
    if not request.document_id:
        raise HTTPException(status_code=400, detail="Document ID is not provided")
    
    question_response = call_openai_safely(client.embeddings.create,input=request.question, model="text-embedding-3-small")
    results = collection.query(
            query_embeddings=[question_response.data[0].embedding], 
            n_results=3, 
            where={"document_id":request.document_id}
        )
    
    if not results["documents"][0]:
        raise HTTPException(status_code=404, detail="No document found with this ID")
    
    context = "\n\n".join(results["documents"][0])
    prompt = build_rag_prompt(context, request.question)
    
    response = call_openai_safely(client.responses.create ,model="gpt-4.1", input=[{"role": "user", "content":prompt}])
    try:
        output = response.output[0].content[0].text
    except (IndexError, AttributeError) as e:
        logger.error(f"Unexpected response shape: {e}")
        raise HTTPException(status_code=500, detail="Failed to process the AI response")

  
    return {"answer": output}
