import React, { useState, useEffect, useRef } from "react";
import "./App.css";

function App() {
  const [inputValue, setInputValue] = useState("");
  const [messages, setMessages] = useState([]);
  const chatEndRef = useRef(null);

  const handleSend = async () => {
    if (inputValue.trim() === "") return;

    const userMessage = { role: "user", content: inputValue };
    setMessages((prevMessages) => [...prevMessages, userMessage]);

    // Clear input field
    setInputValue("");

    // Send user message to backend
    const response = await fetch("http://localhost:8000/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt: inputValue, use_groq: false }),
    });

    const data = await response.json();
    const botMessage = { role: "bot", content: data.response };
    setMessages((prevMessages) => [...prevMessages, botMessage]);

    // Scroll to the latest message
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter") {
      handleSend();
    }
  };

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="chat-container">
      <div className="chat-box">
        {messages.map((msg, index) => (
          <div key={index} className={`message ${msg.role}`}>
            {msg.content}
          </div>
        ))}
        <div ref={chatEndRef} />
      </div>

      <input
        type="text"
        placeholder="Type your message..."
        value={inputValue}
        onChange={(e) => setInputValue(e.target.value)}
        onKeyPress={handleKeyPress}
        className="input-field"
      />
      <button onClick={handleSend} className="send-btn">
        Send
      </button>
    </div>
  );
}

export default App;
