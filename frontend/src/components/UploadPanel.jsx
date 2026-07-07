import { useState } from 'react'
import './UploadPanel.css'

function UploadPanel({setDocumentId, setFileName, documentId, fileName}) {
  const [file, setFile] = useState("")
  const [message, setMessage] = useState("")
  const [isError, setError] = useState(false)
   const [isUploading, setUploading] = useState(false)

  const handleFile = (event) => {
        setError(false)
        setMessage("")
        setFile(event.target.files[0])
  };

  const onClickUploadButton = async() => {
     
        if (!file) {
            setError(true)
            setMessage("Please upload file");
            return;
        }

        const formData = new FormData();
        formData.append('file', file)
        const url = "http://localhost:8000/upload"
        setUploading(true)
        setError(false)
        setMessage("Uploading......")
        
        const response = await fetch(url, {
            method: "POST",
            body: formData,
        })
        if (!response.ok){
            setUploading(false)
            const errorData = await response.json()
            setMessage(errorData.detail)
            setError(true)

           
            return;
        }
        const data = await response.json()
        setUploading(false)
        setDocumentId(data.document_id)
        setFileName(data.file_name)
        localStorage.setItem('document_id', data.document_id);
        localStorage.setItem('file_name', data.file_name);
        setError(false)
        setMessage("Document uploaded successfully!!!")
       
  }

  return (
    <div className="upload-file-main-container">
        <h3 className="upload-file-heading">Upload the doc</h3>
        <input type="file" onChange={handleFile}/>
      
        <button className="upload-btn" onClick={onClickUploadButton} disabled={isUploading}>Upload</button>
        {fileName && <p className="current-file">Currently loaded: {fileName}</p>}
        <p className={isError ? "message-error" : "message-success"}>{message}</p>

        
        
    </div>
  )
}

export default UploadPanel
