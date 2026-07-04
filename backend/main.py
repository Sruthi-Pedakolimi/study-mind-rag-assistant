import os
from openai import OpenAI 
from fastapi import FastAPI, UploadFile
from dotenv import load_dotenv
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import chromadb
import uuid
from pydantic import BaseModel 


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
    return {"document_id": str(document_id)}


@app.post("/ask")
async def ask_query(request: AskRequest):
    question_response = client.embeddings.create(input=request.question, model="text-embedding-3-small")
    results = collection.query(
            query_embeddings=[question_response.data[0].embedding], 
            n_results=3, 
            where={"document_id":request.document_id}
        )
    
    context = "\n\n".join(results["documents"][0])
    prompt = f"""Answer the question based only on the following context. if the answer isn't there in the context, say you dont know.
            Context: {context}
            question: {request.question}
            """
    response = client.responses.create(model="gpt-4.1", input=[{"role": "user", "content":prompt}])
    output = response.output[0].content[0].text
    return {"answer": output}
