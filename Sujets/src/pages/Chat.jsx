import { useState, useRef, useEffect } from "react";
import { Link } from "react-router-dom";
import "../App.css";

export default function Chat() {
    const [messages, setMessages] = useState([]);
    const [inputValue, setInputValue] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const messagesEndRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleSendMessage = async (e) => {
        e.preventDefault();

        if (!inputValue.trim() || isLoading) return;

        const userMessage = {
            id: Date.now(),
            text: inputValue,
            sender: "user",
            timestamp: new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })
        };

        setMessages(prev => [...prev, userMessage]);
        setInputValue("");
        setIsLoading(true);

        // Simuler une réponse du bot (à remplacer par votre API)
        setTimeout(() => {
            const botMessage = {
                id: Date.now() + 1,
                text: "En cours",
                sender: "bot",
                timestamp: new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })
            };
            setMessages(prev => [...prev, botMessage]);
            setIsLoading(false);
        }, 1000);
    };

    return (
        <div className="page">
            <div className="chat-container">
                <div className="chat-header">
                    <h2>
                        <span className="status-indicator"></span>
                        MeteoBot Chat
                    </h2>
                    <Link to="/" className="back-btn">
                        ← Retour
                    </Link>
                </div>

                <div className="chat-messages">
                    {messages.length === 0 ? (
                        <div className="empty-state">
                            <div className="empty-state-icon">💬</div>
                            <h3>Commencez une conversation</h3>
                            <p>Posez-moi des questions sur la météo !</p>
                        </div>
                    ) : (
                        messages.map((message) => (
                            <div key={message.id} className={`message ${message.sender}`}>
                                <div className="message-avatar">
                                    {message.sender === "user" ? "👤" : "🤖"}
                                </div>
                                <div className="message-content">
                                    <p>{message.text}</p>
                                    <small style={{ opacity: 0.7, fontSize: '0.85rem' }}>
                                        {message.timestamp}
                                    </small>
                                </div>
                            </div>
                        ))
                    )}
                    {isLoading && (
                        <div className="message bot">
                            <div className="message-avatar">🤖</div>
                            <div className="message-content">
                                <p>En train d'écrire...</p>
                            </div>
                        </div>
                    )}
                    <div ref={messagesEndRef} />
                </div>

                <div className="chat-input-container">
                    <form onSubmit={handleSendMessage} className="chat-input-wrapper">
                        <input
                            type="text"
                            className="chat-input"
                            placeholder="Demandez-moi la météo..."
                            value={inputValue}
                            onChange={(e) => setInputValue(e.target.value)}
                            disabled={isLoading}
                        />
                        <button
                            type="submit"
                            className="send-btn"
                            disabled={isLoading || !inputValue.trim()}
                        >
                            Envoyer
                        </button>
                    </form>
                </div>
            </div>
        </div>
    );
}
