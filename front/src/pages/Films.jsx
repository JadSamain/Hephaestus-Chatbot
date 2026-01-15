import { useState, useRef, useEffect } from "react";
import { Link } from "react-router-dom";
import logo from "../img/logo.png";
import MovieDetailsSidebar from "../components/MovieDetailsSidebar.jsx";
import CategoryRow from "../components/CategoryRow.jsx";
import "../Films.css";

export default function Films() {
    const [selectedPlatform, setSelectedPlatform] = useState("All");
    const [searchQuery, setSearchQuery] = useState(""); // Search State
    const [selectedMovie, setSelectedMovie] = useState(null);
    const [isSidebarOpen, setIsSidebarOpen] = useState(false);
    const [categories, setCategories] = useState([]);
    const [platformsList, setPlatformsList] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const filmsRef = useRef(null);
    const aboutRef = useRef(null);

    useEffect(() => {
        const fetchData = async () => {
            try {
                setLoading(true);
                setError(null);

                // Fetch platforms
                const platformsResponse = await fetch("http://localhost:8000/films/platforms");
                if (!platformsResponse.ok) {
                    throw new Error("Erreur lors du chargement des plateformes");
                }
                const platformsData = await platformsResponse.json();
                setPlatformsList(platformsData.platforms || []);

                // Fetch films grouped by category
                const filmsResponse = await fetch("http://localhost:8000/films/");
                if (!filmsResponse.ok) {
                    throw new Error("Erreur lors du chargement des films");
                }
                const filmsData = await filmsResponse.json();
                setCategories(filmsData.categories || []);
            } catch (err) {
                setError(err.message);
                console.error("Error fetching data:", err);
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, []);


    const scrollToSection = (ref) => {
        ref.current?.scrollIntoView({ behavior: "smooth" });
    };

    const filteredCategories = categories.map(category => ({
        ...category,
        movies: category.movies.filter(movie => {
            const matchesPlatform = selectedPlatform === "All" || movie.platforms.includes(selectedPlatform);
            const matchesSearch = movie.title.toLowerCase().includes(searchQuery.toLowerCase());
            return matchesPlatform && matchesSearch;
        })
    })).filter(category => category.movies.length > 0);

    return (
        <div className="page films-page">
            <nav className="top-navbar">
                <div className="nav-left">
                    <img src={logo} alt="Logo" className="nav-logo" />
                    <span className="brand-name">POPCORN</span>
                </div>
                <div className="nav-links">
                    <span
                        className="nav-link"
                        onClick={() => scrollToSection(filmsRef)}
                    >
                        Films
                    </span>
                    <Link to="/chat" className="nav-btn-framed">ChatBot</Link>
                    <span
                        className="nav-link"
                        onClick={() => scrollToSection(aboutRef)}
                    >
                        À propos
                    </span>
                </div>
            </nav>

            <div ref={filmsRef}>
                <header className="films-header">
                    <div className="header-left">
                        <h2>Films Populaires</h2>
                        <Link to="/" className="back-btn">← Retour</Link>
                    </div>
                    <div className="header-right">
                        <input
                            type="text"
                            className="search-input"
                            placeholder="Rechercher un film..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                        />
                        <select
                            className="platform-filter"
                            value={selectedPlatform}
                            onChange={(e) => setSelectedPlatform(e.target.value)}
                        >
                            <option value="All">Toutes les plateformes</option>
                            {platformsList.map(platform => (
                                <option key={platform} value={platform}>{platform}</option>
                            ))}
                        </select>
                    </div>
                </header>

                <div className="films-container">
                    {loading ? (
                        <div className="loading-state">
                            <div className="loading-spinner"></div>
                            <h3>Chargement des films...</h3>
                            <p>Veuillez patienter</p>
                        </div>
                    ) : error ? (
                        <div className="error-state">
                            <div className="error-icon">⚠️</div>
                            <h3>Erreur de chargement</h3>
                            <p>{error}</p>
                            <button
                                className="retry-btn"
                                onClick={() => window.location.reload()}
                            >
                                Réessayer
                            </button>
                        </div>
                    ) : filteredCategories.length > 0 ? (
                        filteredCategories.map((category, index) => (
                            <CategoryRow
                                key={index}
                                title={category.title}
                                movies={category.movies}
                                onMovieClick={(movie) => {
                                    setSelectedMovie(movie);
                                    setIsSidebarOpen(true);
                                }}
                            />
                        ))
                    ) : (
                        <div className="empty-state">
                            <div className="empty-state-icon">🎬</div>
                            <h3>Aucun film trouvé</h3>
                            <p>Essayez de choisir une autre plateforme.</p>
                        </div>
                    )}
                </div>
            </div>

            <div ref={aboutRef} className="about-section">
                <div className="about-content">
                    <h2 className="about-main-title">
                        <span className="info-icon">ⓘ</span> À propos de POPCORN
                    </h2>

                    <div className="about-card">
                        <h3>Projet HEPHAESTUS</h3>
                        <p>
                            POPCORN est un assistant cinéma intelligent propulsé par l'IA. Il combine une base de connaissances locale avec des
                            outils de scraping et des API externes pour vous fournir des informations complètes sur les films.
                        </p>
                    </div>

                    <div className="about-card">
                        <h3>Fonctionnalités</h3>
                        <ul className="features-list">
                            <li>Recherche de films et séries</li>
                            <li>Informations détaillées (notes, réalisateur, année, durée)</li>
                            <li>Disponibilité sur les plateformes de streaming</li>
                            <li>Recommandations personnalisées</li>
                            <li>Chat intelligent pour vos questions cinéma</li>
                        </ul>
                    </div>

                    <div className="about-card">
                        <h3>Sources de données</h3>
                        <div className="data-sources-list">
                            <div className="source-item">
                                <span className="source-badge">Base de données locale</span>
                                <span className="source-desc">Catalogue de films et métadonnées</span>
                            </div>
                            <div className="source-item">
                                <span className="source-badge">Scraping IMDb</span>
                                <span className="source-desc">Notes et critiques</span>
                            </div>
                            <div className="source-item">
                                <span className="source-badge">API JustWatch</span>
                                <span className="source-desc">Disponibilité streaming</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <MovieDetailsSidebar
                movie={selectedMovie}
                isOpen={isSidebarOpen}
                onClose={() => setIsSidebarOpen(false)}
            />
        </div>
    );
}
