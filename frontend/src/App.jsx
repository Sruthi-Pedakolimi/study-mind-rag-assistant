import { useState } from 'react'
import UploadPanel from './components/UploadPanel'
import './App.css'
import ChatPanel from './components/ChatPanel'

function App() {
  const [documentId, setDocumentId] = useState(localStorage.getItem("document_id"))
  const [fileName, setFileName] = useState(localStorage.getItem("file_name"))
  const [chatHistory, setChatHistory] = useState([])
  

  return (
    <>
    <h1 className="app-title">StudyMind</h1>
    <div className="app-layout">
        <UploadPanel setDocumentId={setDocumentId} setFileName={setFileName} documentId={documentId} fileName={fileName}/>
        <ChatPanel documentId={documentId}/>
    </div>
    </>
  )
}

export default App
