import { useState, useRef, useEffect } from "react";
import { Link } from "react-router-dom";
import "../App.css";

export default function Chat() {
    // Variables d'état
    const [history, setHistory] = useState([]);
    const [currentId, setCurrentId] = useState(null);
    const [msgs, setMsgs] = useState([]);
    const [input, setInput] = useState("");
    const [loading, setLoading] = useState(false);
    const [menuOpen, setMenuOpen] = useState(false);
    const bottomRef = useRef(null);

    // Au chargement de la page
    useEffect(() => {
        let saved = localStorage.getItem("popcorn_history");
        if (saved) {
            saved = JSON.parse(saved);
        } else {
            saved = [];
        }
        setHistory(saved);

        if (saved.length > 0) {
            // Charger le premier chat
            let first = saved[0];
            setCurrentId(first.id);
            setMsgs(first.messages);
            setMenuOpen(false);
        } else {
            // Créer un nouveau chat
            let newChat = {
                id: Date.now(),
                title: "Nouvelle conversation",
                messages: [],
                date: new Date().toISOString()
            };
            setHistory([newChat]);
            setCurrentId(newChat.id);
            setMsgs([]);
            setMenuOpen(false);
        }
    }, []);

    // Sauvegarde auto
    useEffect(() => {
        if (history.length > 0) {
            localStorage.setItem("popcorn_history", JSON.stringify(history));
        }
    }, [history]);

    // Scroll en bas automatique
    useEffect(() => {
        if (bottomRef.current) {
            bottomRef.current.scrollIntoView({ behavior: "smooth" });
        }
    }, [msgs]);

    // Nouvelle conversation
    const newChat = () => {
        let chat = {
            id: Date.now(),
            title: "Nouvelle conversation",
            messages: [],
            date: new Date().toISOString()
        };
        let newHistory = [chat, ...history];
        setHistory(newHistory);
        setCurrentId(chat.id);
        setMsgs([]);
        setMenuOpen(false);
    }

    // Changer de conversation
    const switchChat = (id) => {
        let chat = history.find(c => c.id === id);
        if (chat) {
            setCurrentId(id);
            setMsgs(chat.messages);
            setMenuOpen(false);
        }
    }

    // Envoyer un message
    const send = async (e) => {
        e.preventDefault();

        if (input === "" || loading) return;

        // Message utilisateur
        let userMsg = {
            id: Date.now(),
            text: input,
            sender: "user",
            timestamp: new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })
        };

        let newMsgs = [...msgs, userMsg];
        setMsgs(newMsgs);

        // Mettre à jour l'historique direct
        let newHistory = history.map(chat => {
            if (chat.id === currentId) {
                let title = chat.title;
                // Si c'est le tout premier message, on change le titre
                if (chat.messages.length === 0) {
                    title = input.substring(0, 30);
                    if (input.length > 30) title += "...";
                }
                return { ...chat, messages: newMsgs, title: title };
            }
            return chat;
        });
        setHistory(newHistory);

        let prompt = input;
        setInput("");
        setLoading(true);

        // Appel API
        try {
            const res = await fetch('http://localhost:8000/chat/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ prompt: prompt })
            });

            if (!res.ok) throw new Error("Erreur serveur");

            const data = await res.json();

            // Message Bot
            let botMsg = {
                id: Date.now() + 1,
                text: data.response || "Pas de réponse.",
                sender: "bot",
                timestamp: new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })
            };

            let finalMsgs = [...newMsgs, botMsg];
            setMsgs(finalMsgs);

            // Mettre à jour l'historique encore
            newHistory = history.map(chat => {
                if (chat.id === currentId) {
                    // On garde le titre qu'on a peut-être changé juste avant
                    let currentTitle = chat.title;
                    if (chat.messages.length === 0) {
                        currentTitle = prompt.substring(0, 30);
                        if (prompt.length > 30) currentTitle += "...";
                    }
                    return { ...chat, messages: finalMsgs, title: currentTitle };
                }
                return chat;
            });
            setHistory(newHistory);

        } catch (err) {
            console.log(err);
            let errorMsg = {
                id: Date.now() + 1,
                text: "Erreur connexion serveur (http://localhost:8000)",
                sender: "bot",
                timestamp: new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })
            };
            setMsgs([...newMsgs, errorMsg]);
        }

        setLoading(false);
    };

    return (
        <div className="app-container">
            {/* Sidebar */}
            <div className={`sidebar ${menuOpen ? 'open' : ''}`}>
                <button onClick={newChat} className="new-chat-btn">
                    <span>+</span> Nouvelle conversation
                </button>

                <div className="history-list">
                    {history.map(c => (
                        <div
                            key={c.id}
                            className={`history-item ${c.id === currentId ? 'active' : ''}`}
                            onClick={() => switchChat(c.id)}
                        >
                            <span className="history-item-icon">💬</span>
                            {c.title}
                        </div>
                    ))}
                </div>

                <Link to="/" className="back-btn" style={{ marginTop: 'auto' }}>
                    ← Menu Principal
                </Link>
            </div>

            {/* Zone de Chat */}
            <div className="chat-container">
                <button
                    className="mobile-menu-btn"
                    onClick={() => setMenuOpen(!menuOpen)}
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
                    {msgs.length === 0 ? (
                        <div className="empty-state">
                            <div className="empty-state-icon">🎬</div>
                            <h3>Bienvenue sur POPCORN</h3>
                            <p>Je suis prêt à parler cinéma !</p>
                        </div>
                    ) : (
                        msgs.map((m) => (
                            <div key={m.id} className={`message ${m.sender}`}>
                                <div className="message-avatar">
                                    {m.sender === "user" ? "👤" : "🎬"}
                                </div>
                                <div className="message-content">
                                    <p>{m.text}</p>
                                    <small style={{ opacity: 0.7, fontSize: '0.85rem' }}>
                                        {m.timestamp}
                                    </small>
                                </div>
                            </div>
                        ))
                    )}
                    {loading && (
                        <div className="message bot">
                            <div className="message-avatar">🎬</div>
                            <div className="message-content">
                                <p>Recherche en cours...</p>
                            </div>
                        </div>
                    )}
                    <div ref={bottomRef} />
                </div>

                <div className="chat-input-container">
                    <form onSubmit={send} className="chat-input-wrapper">
                        <input
                            type="text"
                            className="chat-input"
                            placeholder="Ex: Où puis-je regarder Inception ?"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            disabled={loading}
                        />
                        <button
                            type="submit"
                            className="send-btn"
                            disabled={loading || !input.trim()}
                        >
                            Envoyer
                        </button>
                    </form>
                </div>
            </div>
        </div>
    );
}
