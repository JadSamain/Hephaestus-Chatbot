import { useState, useRef, useEffect } from "react";
import { Link } from "react-router-dom";
import MovieCard from "../components/MovieCard.jsx";
import ConfirmationModal from "../components/ConfirmationModal.jsx";
import "../App.css";

import logo from "../img/logo.png";

export default function Chat() {
    const [conversations, setConversations] = useState([]);
    const [currentChatId, setCurrentChatId] = useState(null);
    const [messages, setMessages] = useState([]);
    const [inputValue, setInputValue] = useState("");
    const [loadingMessage, setLoadingMessage] = useState(""); // État pour le message de chargement
    const [loadingChatId, setLoadingChatId] = useState(null); // ID de la conv qui charge
    const [isSidebarOpen, setIsSidebarOpen] = useState(false);
    const [searchTerm, setSearchTerm] = useState(""); // Recherche
    const [isSearchVisible, setIsSearchVisible] = useState(false); // Afficher/Masquer barre recherche

    // State pour la modale de suppression
    const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
    const [chatToDeleteId, setChatToDeleteId] = useState(null);
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
        setConversations(prevConversations => {
            return prevConversations.map(chat => {
                if (chat.id === chatId) {
                    // Création d'une copie de l'objet chat pour éviter la mutation
                    let updatedChat = { ...chat, messages: newMessages };

                    // Mise à jour du titre si nécessaire
                    if (newMessages.length > 0 && chat.title === "Nouvelle conversation") {
                        const firstMsg = newMessages[0];
                        if (firstMsg.sender === 'user') {
                            updatedChat.title = firstMsg.text.substring(0, 20) + "...";
                        }
                    }
                    return updatedChat;
                }
                return chat;
            });
        });
    };

    const deleteConversation = (e, chatId) => {
        e.stopPropagation();
        setChatToDeleteId(chatId);
        setIsDeleteModalOpen(true);
    };

    const confirmDeleteConversation = () => {
        if (chatToDeleteId) {
            let newConversations = [];
            for (let i = 0; i < conversations.length; i++) {
                if (conversations[i].id !== chatToDeleteId) {
                    newConversations.push(conversations[i]);
                }
            }
            setConversations(newConversations);

            // Si on supprime la conversation courante, on charge la première disponible ou on en crée une nouvelle
            if (chatToDeleteId === currentChatId) {
                if (newConversations.length > 0) {
                    loadConversation(newConversations[0].id);
                } else {
                    createNewChat();
                }
            }
        }
        setIsDeleteModalOpen(false);
        setChatToDeleteId(null);
    };

    const cancelDeleteConversation = () => {
        setIsDeleteModalOpen(false);
        setChatToDeleteId(null);
    };

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

        // Séquence de chargement
        const steps = ["Réflexion...", "Recherche sur IMDb...", "Analyse des plateformes...", "Génération de la réponse..."];
        setLoadingMessage(steps[0]);
        setLoadingChatId(currentChatId); // On memorise quelle conv charge
        let stepIndex = 0;

        // On change le message toutes les 2.5 secondes pour montrer que ça travaille
        const intervalId = setInterval(() => {
            stepIndex++;
            if (stepIndex < steps.length) {
                setLoadingMessage(steps[stepIndex]);
            }
        }, 2500);

        try {
            // On prépare les données pour le back
            const donnee = { prompt: currentInput };

            const response = await fetch('http://localhost:8000/chat/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(donnee)
            });

            if (response.status !== 200) {
                alert("Erreur serveur !");
                return;
            }

            const data = await response.json();

            // On essaie de voir si c'est du JSON (film) ou du texte normal
            let botText = data.response;
            let msgType = 'text';
            let movieData = null;

            try {
                // On tente de parser la réponse si c'est un JSON valide
                if (data.response.trim().startsWith('{')) {
                    const parsed = JSON.parse(data.response);
                    if (parsed.type === 'movie_recommendation') {
                        msgType = 'movie';
                        movieData = parsed;
                        botText = "Voici une recommandation pour vous :"; // Texte de fallback ou titre
                    }
                }
            } catch (e) {
                // Si ça échoue, c'est juste du texte normal
            }

            // Réponse de l'IA
            const botMessage = {
                id: Date.now() + 1,
                text: botText,
                sender: "bot",
                timestamp: timeString,
                type: msgType,
                content: movieData
            };

            // On ajoute la réponse
            const finalMessages = [...updatedMessages, botMessage];
            setMessages(finalMessages);
            updateConversation(currentChatId, finalMessages);

        } catch (error) {
            alert("Impossible de contacter le serveur");
        } finally {
            // On nettoie tout
            clearInterval(intervalId);
            setLoadingMessage("");
            setLoadingChatId(null);
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

                <button onClick={() => setIsSearchVisible(!isSearchVisible)} className="search-toggle-btn">
                    <span>🔍</span> Rechercher des chats
                </button>

                {isSearchVisible && (
                    <input
                        type="text"
                        className="sidebar-search-input"
                        placeholder="Mots-clés..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                    />
                )}

                <div className="history-list">
                    {(() => {
                        let filteredConversations = [];
                        if (searchTerm === "") {
                            filteredConversations = conversations;
                        } else {
                            // Style étudiant : boucle for simple et recherche profonde
                            for (let i = 0; i < conversations.length; i++) {
                                let found = false;
                                const chat = conversations[i];
                                const searchLower = searchTerm.toLowerCase();

                                // 1. Vérifier le titre
                                if (chat.title.toLowerCase().includes(searchLower)) {
                                    found = true;
                                }

                                // 2. Vérifier les messages si pas trouvé dans le titre
                                if (!found && chat.messages) {
                                    for (let j = 0; j < chat.messages.length; j++) {
                                        if (chat.messages[j].text && chat.messages[j].text.toLowerCase().includes(searchLower)) {
                                            found = true;
                                            break;
                                        }
                                    }
                                }

                                if (found) {
                                    filteredConversations.push(chat);
                                }
                            }
                        }

                        return filteredConversations.map(chat => (
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
                        ));
                    })()}
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
                                    {message.type === 'movie' && message.content ? (
                                        <MovieCard
                                            title={message.content.title}
                                            year={message.content.year}
                                            poster={message.content.poster}
                                            rating={message.content.rating}
                                            platforms={message.content.platforms}
                                        />
                                    ) : (
                                        <p>{message.text}</p>
                                    )}
                                    <small style={{ opacity: 0.7, fontSize: '0.85rem' }}>
                                        {message.timestamp}
                                    </small>
                                </div>
                            </div>
                        ))
                    )}
                    {loadingMessage && loadingChatId === currentChatId && (
                        <div className="message bot">
                            <div className="message-avatar">🎬</div>
                            <div className="message-content">
                                <p className="loading-text">{loadingMessage}</p>
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
                            disabled={!!loadingMessage}
                        />
                        <button
                            type="submit"
                            className="send-btn"
                            disabled={!!loadingMessage || !inputValue.trim()}
                        >
                            Envoyer
                        </button>
                    </form>
                </div>
            </div >

            <ConfirmationModal
                isOpen={isDeleteModalOpen}
                onClose={cancelDeleteConversation}
                onConfirm={confirmDeleteConversation}
                message="Êtes-vous sûr de vouloir supprimer cette conversation ? Cette action est irréversible."
            />
        </div >
    );
}
