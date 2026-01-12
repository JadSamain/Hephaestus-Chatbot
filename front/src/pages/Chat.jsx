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
        // On rajoute au début
        let newTableau = [newChat];
        for (let i = 0; i < conversations.length; i++) {
            newTableau.push(conversations[i]);
        }
        setConversations(newTableau);
        setCurrentChatId(newChat.id);
        setMessages([]);
        setIsSidebarOpen(false);
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
        // Copie du tableau pour ne pas modifier l'état directement
        let newConversations = [...conversations];

        // On cherche la conversation à modifier
        for (let i = 0; i < newConversations.length; i++) {
            if (newConversations[i].id === chatId) {
                newConversations[i].messages = newMessages;

                // Si c'est le premier message on met le titre
                if (newConversations[i].messages.length > 0 && newConversations[i].title === "Nouvelle conversation") {
                    let firstMsg = newConversations[i].messages[0];
                    if (firstMsg.sender === 'user') {
                        newConversations[i].title = firstMsg.text.substring(0, 20) + "...";
                    }
                }
            }
        }
        setConversations(newConversations);
    };

    const deleteConversation = (e, chatId) => {
        e.stopPropagation(); // Pour ne pas ouvrir la conversation en cliquant sur supprimer

        if (confirm("Supprimer cette conversation ?")) {
            let newConversations = [];
            for (let i = 0; i < conversations.length; i++) {
                if (conversations[i].id !== chatId) {
                    newConversations.push(conversations[i]);
                }
            }
            setConversations(newConversations);

            // Si on supprime la conversation active, on en crée une nouvelle ou on change
            //         if (chatId === currentChatId) {
            //             if (newConversations.length > 0) {
            //                 loadConversation(newConversations[0].id);
            //             } else {
            //                 createNewChat();
            //             }
            //         }
            //     }
            // };

            const handleSendMessage = async (e) => {
                e.preventDefault();

                if (inputValue === "") {
                    // Pas de message vide
                    return;
                }

                // On crée la date à la main
                let now = new Date();
                let hours = now.getHours();
                let minutes = now.getMinutes();
                if (minutes < 10) minutes = "0" + minutes;
                let timeString = hours + ":" + minutes;

                // Message de l'utilisateur
                const userMessage = {
                    id: Date.now(),
                    text: inputValue,
                    sender: "user",
                    timestamp: timeString
                };

                const updatedMessages = [...messages, userMessage];
                setMessages(updatedMessages);
                updateConversation(currentChatId, updatedMessages);

                const currentInput = inputValue;
                setInputValue("");
                setIsLoading(true);

                try {
                    // On prépare les données pour le back
                    const donnee = { prompt: currentInput };

                    console.log("Envoi au serveur...");

                    const response = await fetch('http://localhost:8000/chat/', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(donnee)
                    });

                    if (response.status !== 200) {
                        alert("Erreur serveur !");
                        setIsLoading(false);
                        return;
                    }

                    const data = await response.json();

                    // Réponse de l'IA
                    const botMessage = {
                        id: Date.now() + 1,
                        text: data.response,
                        sender: "bot",
                        timestamp: timeString
                    };

                    // On ajoute la réponse
                    const finalMessages = [...updatedMessages, botMessage];
                    setMessages(finalMessages);
                    updateConversation(currentChatId, finalMessages);

                } catch (error) {
                    console.log(error);
                    alert("Impossible de contacter le serveur");
                }

                setIsLoading(false);
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
                                    <span className="history-item-title">{chat.title}</span>
                                    <button
                                        className="delete-conv-btn"
                                        onClick={(e) => deleteConversation(e, chat.id)}
                                    >
                                        🗑️
                                    </button>
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
