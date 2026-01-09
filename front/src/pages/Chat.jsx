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
        const currentInput = inputValue;
        setInputValue("");
        setIsLoading(true);

        try {
            // Appel à l'API backend
            const response = await fetch('http://localhost:8000/chat/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ prompt: currentInput })
            });

            if (!response.ok) {
                throw new Error(`Erreur HTTP: ${response.status}`);
            }

            const data = await response.json();

            const botMessage = {
                id: Date.now() + 1,
                text: data.response || "Désolé, je n'ai pas pu générer une réponse.",
                sender: "bot",
                timestamp: new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })
            };

            setMessages(prev => [...prev, botMessage]);
        } catch (error) {
            console.error('Erreur lors de l\'appel à l\'API:', error);

            const errorMessage = {
                id: Date.now() + 1,
                text: "Désolé, une erreur s'est produite. Assurez-vous que le serveur backend est en cours d'exécution sur http://localhost:8000",
                sender: "bot",
                timestamp: new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })
            };

            setMessages(prev => [...prev, errorMessage]);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="page">
            <div className="chat-container">
                <div className="chat-header">
                    <h2>
                        <span className="status-indicator"></span>
                        CineBot Chat
                    </h2>
                    <Link to="/" className="back-btn">
                        ← Retour
                    </Link>
                </div>

                <div className="chat-messages">
                    {messages.length === 0 ? (
                        <div className="empty-state">
                            <div className="empty-state-icon">🎬</div>
                            <h3>Commencez une conversation</h3>
                            <p>Recherchez un film ou une série et découvrez où le regarder !</p>
                        </div>
                    ) : (
                        messages.map((message) => (
                            <div key={message.id} className={`message ${message.sender}`}>
                                <div className="message-avatar">
                                    {message.sender === "user" ? "👤" : "🎬"}
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
                            <div className="message-avatar">🎬</div>
                            <div className="message-content">
                                <p>Recherche en cours...</p>
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
                            placeholder="Ex: Où puis-je regarder Inception ?"
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
