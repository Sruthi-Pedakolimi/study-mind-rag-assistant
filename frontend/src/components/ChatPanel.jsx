import { useState } from 'react'
import './ChatPanel.css'
import ReactMarkdown from 'react-markdown'

function ChatPanel({documentId}) {
    const [isAnswerLoading, setAnswerLoading] = useState(false)
    const [message, setMessage] = useState("")
    const [question, setQuestion] = useState("")
    const [chatHistory, setChatHistory] = useState([])
    const [submitStatus, setSubmitStatus] = useState(false)

    const handleSubmit = async(event) => {
        if (question == ""){
            setMessage("Please enter the question")
            return
        }
        setSubmitStatus(true)
        const url = "http://localhost:8000/ask"
        const payload = {
                question: question,
                document_id: documentId,
            }
        setAnswerLoading(true)
        setMessage("Generating....")
        const response = await fetch(url, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(payload)
        })
        console.log(response)
        if (!response.ok){
            setAnswerLoading(false)
            const errorData = await response.json()
            setMessage(errorData.detail)
            return
        }
        const data = await response.json()
        setChatHistory([...chatHistory, {question: question, answer: data.answer}])
        setAnswerLoading(false)
        setMessage("")
        setQuestion("")
    }
    const handleQuestionInput = (event) => {
        setSubmitStatus(false)
        setMessage("")
        setQuestion(event.target.value)
    }
    return (
        <div className="chat-panel-main-container">
            <div className="chat-response-container">
                {chatHistory.map((chat, index) => {
                    return(
                    <div key={index}>
                        <p className="question">{chat.question}</p>
                        <div className="answer"><ReactMarkdown>{chat.answer}</ReactMarkdown></div>
                    </div>)
                })}
               
            </div>
            <p className="message">{message}</p>
            <input type="text" onChange={handleQuestionInput} value={question} placeholder='Please enter the question' className="question-input"/>
            <button onClick={handleSubmit} className="enter-btn">Enter</button>
        </div>
    )

}

export default ChatPanel