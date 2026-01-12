import { useState, useRef, useEffect } from "react";
import { Link } from "react-router-dom";
import "../App.css";

import logo from "../img/logo.png";

export default function Chat() {
    const [conversations, setConversations] = useState([]);
    const [currentChatId, setCurrentChatId] = useState(null);
    const [messages, setMessages] = useState([]);
    const [inputValue, setInputValue] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [isSidebarOpen, setIsSidebarOpen] = useState(false);
    const messagesEndRef = useRef(null);

    // Charger l'historique au démarrage
    useEffect(() => {
        const savedConversations = JSON.parse(localStorage.getItem("popcorn_history") || "[]");
        setConversations(savedConversations);

        if (savedConversations.length > 0) {
            // Charger la dernière conversation ou créer une nouvelle
            loadConversation(savedConversations[0].id);
        } else {
            createNewChat();
        }
    }, []);

    // Sauvegarder les conversations à chaque changement
    useEffect(() => {
        if (conversations.length > 0) {
            localStorage.setItem("popcorn_history", JSON.stringify(conversations));
        }
    }, [conversations]);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const createNewChat = () => {
        const newChat = {
            id: Date.now(),
            title: "Nouvelle conversation",
            messages: [],
            date: new Date().toISOString()
        };
        setConversations(prev => [newChat, ...prev]);
        setCurrentChatId(newChat.id);
        setMessages([]);
        setIsSidebarOpen(false); // Fermer sidebar sur mobile après sélection
    };

    const loadConversation = (chatId) => {
        const chat = conversations.find(c => c.id === chatId);
        if (chat) {
            setCurrentChatId(chatId);
            setMessages(chat.messages);
            setIsSidebarOpen(false);
        }
    };

    const updateConversation = (chatId, newMessages) => {
        setConversations(prev => prev.map(chat => {
            if (chat.id === chatId) {
                // Générer un titre si c'est le premier message utilisateur
                let title = chat.title;
                if (chat.messages.length === 0 && newMessages.length > 0) {
                    const firstUserMsg = newMessages.find(m => m.sender === 'user');
                    if (firstUserMsg) {
                        title = firstUserMsg.text.slice(0, 30) + (firstUserMsg.text.length > 30 ? "..." : "");
                    }
                }
                return { ...chat, messages: newMessages, title };
            }
            return chat;
        }));
    };

    const handleSendMessage = async (e) => {
        e.preventDefault();

        if (!inputValue.trim() || isLoading) return;

        const userMessage = {
            id: Date.now(),
            text: inputValue,
            sender: "user",
            timestamp: new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })
        };

        const updatedMessages = [...messages, userMessage];
        setMessages(updatedMessages);
        updateConversation(currentChatId, updatedMessages);

        const currentInput = inputValue;
        setInputValue("");
        setIsLoading(true);

        try {
            // Appel à l'API backend
            const requestPayload = { prompt: currentInput };

            console.log('📤 Envoi au backend:', requestPayload);
            console.log('📤 JSON envoyé:', JSON.stringify(requestPayload));

            const response = await fetch('http://localhost:8000/chat/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestPayload)
            });

            console.log('📥 Statut de la réponse:', response.status);

            if (!response.ok) {
                throw new Error(`Erreur HTTP: ${response.status}`);
            }

            const data = await response.json();

            console.log('📥 Réponse du backend:', data);
            console.log('📥 Texte de la réponse:', data.response);

            const botMessage = {
                id: Date.now() + 1,
                text: data.response || "Désolé, je n'ai pas pu générer une réponse.",
                sender: "bot",
                timestamp: new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })
            };

            const finalMessages = [...updatedMessages, botMessage];
            setMessages(finalMessages);
            updateConversation(currentChatId, finalMessages);
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
        <div className="app-container">
            {/* Sidebar */}
            <div className={`sidebar ${isSidebarOpen ? 'open' : ''}`}>
                <div className="sidebar-header">
                    <img src={logo} alt="Popcorn Chat Logo" className="sidebar-logo" />
                </div>
                <button onClick={createNewChat} className="new-chat-btn">
                    <span>+</span> Nouvelle conversation
                </button>

                <div className="history-list">
                    {conversations.map(chat => (
                        <div
                            key={chat.id}
                            className={`history-item ${chat.id === currentChatId ? 'active' : ''}`}
                            onClick={() => loadConversation(chat.id)}
                        >
                            <span className="history-item-icon">💬</span>
                            {chat.title}
                        </div>
                    ))}
                </div>

                <Link to="/" className="back-btn" style={{ marginTop: 'auto' }}>
                    ← Menu Principal
                </Link>
            </div>

            {/* Main Chat Area */}
            <div className="chat-container">
                <button
                    className="mobile-menu-btn"
                    onClick={() => setIsSidebarOpen(!isSidebarOpen)}
                >
                    ☰
                </button>

                <div className="chat-header">
                    <h2>
                        <span className="status-indicator"></span>
                        POPCORN Chat
                    </h2>
                </div>

                <div className="chat-messages">
                    {messages.length === 0 ? (
                        <div className="empty-state">
                            <div className="empty-state-icon">🎬</div>
                            <h3>Bienvenue sur POPCORN</h3>
                            <p>Je suis prêt à parler cinéma !</p>
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
