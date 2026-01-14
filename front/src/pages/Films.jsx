import { useState, useRef, useEffect } from "react";
import { Link, NavLink } from "react-router-dom";
import "../film.css";
import "./Films.css";

// --- Mock Data Generator ---
// Helper to create a large dataset from a few base movies
const baseMovies = [
    {
        id: 1, title: "Inception", rating: 8.8,
        poster: "https://image.tmdb.org/t/p/w500/9gk7adHYeDvHkCSEqAvQNLV5Uge.jpg",
        platforms: ["Netflix", "Max"], director: "Christopher Nolan", releaseDate: "2010", duration: "2h 28m",
        summary: "Dom Cobb est un voleur expérimenté, le meilleur dans l'art dangereux de l'extraction.",
        tags: ["Tendances", "Action"]
    },
    {
        id: 2, title: "Interstellar", rating: 8.6,
        poster: "https://image.tmdb.org/t/p/w500/gEU2QniE6E77NI6lCU6MxlNBvIx.jpg",
        platforms: ["Prime Video"], director: "Christopher Nolan", releaseDate: "2014", duration: "2h 49m",
        summary: "Une équipe d'explorateurs voyage à travers un trou de ver dans l'espace.",
        tags: ["Tendances", "Sci-Fi"]
    },
    {
        id: 3, title: "The Dark Knight", rating: 9.0,
        poster: "https://image.tmdb.org/t/p/w500/qJ2tW6WMUDux911r6m7haRef0WH.jpg",
        platforms: ["Max"], director: "Christopher Nolan", releaseDate: "2008", duration: "2h 32m",
        summary: "Batman entreprend de démanteler les dernières organisations criminelles de Gotham.",
        tags: ["Tendances", "Action"]
    },
    {
        id: 4, title: "Avatar", rating: 7.8,
        poster: "https://image.tmdb.org/t/p/w500/kyeqWdyUXW608qlYkRqosgbbJyK.jpg",
        platforms: ["Disney+"], director: "James Cameron", releaseDate: "2009", duration: "2h 42m",
        summary: "Un marine paraplégique envoyé sur la lune Pandora pour une mission unique.",
        tags: ["Populaires", "Sci-Fi"]
    },
    {
        id: 5, title: "Dune: Part Two", rating: 8.7,
        poster: "https://image.tmdb.org/t/p/w500/1pdfLvkbY9ohJlCjQH2CZjjYVvJ.jpg",
        platforms: ["Max"], director: "Denis Villeneuve", releaseDate: "2024", duration: "2h 46m",
        summary: "Paul Atreides s'unit à Chani et aux Fremen tout en préparant sa revanche.",
        tags: ["Nouveautés", "Tendances"]
    },
    {
        id: 6, title: "Oppenheimer", rating: 8.2,
        poster: "https://image.tmdb.org/t/p/w500/8Gxv8gSFCU0XGDykEGv7zR1n2ua.jpg",
        platforms: ["Peacock"], director: "Christopher Nolan", releaseDate: "2023", duration: "3h 00m",
        summary: "L'histoire de J. Robert Oppenheimer et la bombe atomique.",
        tags: ["Populaires", "Drame"]
    },
    {
        id: 7, title: "Spider-Man: Across the Spider-Verse", rating: 8.7,
        poster: "https://image.tmdb.org/t/p/w500/8Vt6mWEReuy4Of61Lnj5Xj704m8.jpg",
        platforms: ["Netflix"], director: "Joaquim Dos Santos", releaseDate: "2023", duration: "2h 20m",
        summary: "Miles Morales est catapulté à travers le Multivers.",
        tags: ["Nouveautés", "Animation"]
    },
    {
        id: 8, title: "The Batman", rating: 7.7,
        poster: "https://image.tmdb.org/t/p/w500/74xTEgt7R36Fpooo50r9T25onhq.jpg",
        platforms: ["Max"], director: "Matt Reeves", releaseDate: "2022", duration: "2h 56m",
        summary: "Batman s'aventure dans la pègre de Gotham City.",
        tags: ["Populaires", "Action"]
    }
];

// --- Platform Data ---
const PLATFORMS = [
    { id: "netflix", name: "Netflix", logoSrc: "/src/img/platforms/netflix.svg", color: "#E50914" },
    { id: "prime", name: "Prime Video", logoSrc: "/src/img/platforms/prime.svg", color: "#00A8E1" },
    { id: "disney", name: "Disney+", logoSrc: "/src/img/platforms/disney.svg", color: "#113CCF" },
    { id: "max", name: "Max", logoSrc: "/src/img/platforms/max.svg", color: "#002BE7" },
    { id: "apple", name: "Apple TV+", logoSrc: "/src/img/platforms/apple.svg", color: "#FFFFFF" },
    { id: "paramount", name: "Paramount+", logoSrc: "/src/img/platforms/paramount.svg", color: "#0064FF" },
    { id: "mubi", name: "MUBI", logoSrc: "/src/img/platforms/mubi.svg", color: "#000000" },
    { id: "crunchyroll", name: "Crunchyroll", logoSrc: "/src/img/platforms/crunchyroll.svg", color: "#F47521" },
    { id: "canal", name: "Canal+", logoSrc: "/src/img/platforms/canal.svg", color: "#000000" },
    { id: "peacock", name: "Peacock", logoSrc: "/src/img/platforms/peacock.svg", color: "#000000" }
];

// --- Platform Filter Component ---
const PlatformFilter = ({ selected, onChange }) => {
    const [isOpen, setIsOpen] = useState(false);
    const dropdownRef = useRef(null);

    // Close on click outside
    useEffect(() => {
        const handleClickOutside = (event) => {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
                setIsOpen(false);
            }
        };
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, []);

    const togglePlatform = (id) => {
        if (selected.includes(id)) {
            onChange(selected.filter(pid => pid !== id));
        } else {
            onChange([...selected, id]);
        }
    };

    const clearSelection = () => onChange([]);

    return (
        <div className="platform-filter-container" ref={dropdownRef}>
            <button
                className={`platform-filter-btn ${isOpen ? 'open' : ''} ${selected.length > 0 ? 'active' : ''}`}
                onClick={() => setIsOpen(!isOpen)}
            >
                <span className="filter-icon">📺</span>
                <span className="filter-label">
                    Plateformes {selected.length > 0 && `(${selected.length})`}
                </span>
                <span className="filter-chevron">▼</span>
            </button>

            {isOpen && (
                <div className="platform-dropdown">
                    <div className="dropdown-header">
                        <span>Filtrer par</span>
                        {selected.length > 0 && (
                            <button className="clear-btn" onClick={clearSelection}>
                                Effacer
                            </button>
                        )}
                    </div>
                    <div className="platform-list">
                        {PLATFORMS.map(p => {
                            const isSelected = selected.includes(p.id);
                            return (
                                <div
                                    key={p.id}
                                    className={`platform-item ${isSelected ? 'selected' : ''}`}
                                    onClick={() => togglePlatform(p.id)}
                                >
                                    <div className="platform-checkbox">
                                        {isSelected && "✓"}
                                    </div>
                                    <div className="platform-logo-placeholder" style={{ backgroundColor: p.color }}>
                                        {/* Fallback if image fails or doesn't exist yet */}
                                        <img
                                            src={p.logoSrc}
                                            alt={p.name}
                                            onError={(e) => { e.target.style.display = 'none'; }}
                                            onLoad={(e) => { e.target.style.display = 'block'; }}
                                        />
                                        <span className="logo-text-fallback">{p.name[0]}</span>
                                    </div>
                                    <span className="platform-name">{p.name}</span>
                                </div>
                            );
                        })}
                    </div>
                </div>
            )}
        </div>
    );
};

// --- Mock Data Generator ---
const generateMovies = () => {
    let movies = [];
    for (let i = 0; i < 5; i++) {
        baseMovies.forEach((m) => {
            movies.push({
                ...m,
                id: `${m.id}-${i}`, // Unique ID
                rating: (Math.random() * (9.5 - 7.0) + 7.0).toFixed(1) // Randomize slightly
            });
        });
    }
    return movies;
};

const allMovies = generateMovies();

const categories = [
    { title: "Tendances", filter: m => m.tags.includes("Tendances") || m.rating > 8.5 },
    { title: "Populaires", filter: m => m.tags.includes("Populaires") },
    { title: "Nouveautés", filter: m => m.tags.includes("Nouveautés") || parseInt(m.releaseDate) >= 2023 },
    { title: "Recommandés pour vous", filter: m => m.rating > 8.0 } // Generic good movies
];

// --- Components ---

const MovieCard = ({ movie, onClick }) => (
    <div className="movie-card" onClick={() => onClick(movie)}>
        <div className="movie-poster-wrapper">
            <img src={movie.poster} alt={movie.title} className="movie-poster" loading="lazy" />
            <div className="movie-rating">{movie.rating}</div>
        </div>
        <div className="movie-info">
            <h4>{movie.title}</h4>
        </div>
    </div>
);

const CategoryRow = ({ title, movies, onMovieClick }) => {
    const rowRef = useRef(null);

    const scrollLeft = () => {
        if (rowRef.current) {
            rowRef.current.scrollBy({ left: -window.innerWidth * 0.7, behavior: "smooth" });
        }
    };

    const scrollRight = () => {
        if (rowRef.current) {
            rowRef.current.scrollBy({ left: window.innerWidth * 0.7, behavior: "smooth" });
        }
    };

    // Handle horizontal scrolling on mouse wheel
    const handleWheel = (e) => {
        if (rowRef.current && Math.abs(e.deltaX) === 0) { // Only convert vertical if no horizontal intent
            e.preventDefault();
            rowRef.current.scrollLeft += e.deltaY;
        }
    };

    return (
        <div className="category-section">
            <h3 className="category-title">{title}</h3>
            <div className="carousel-wrapper">
                <button className="carousel-nav left" onClick={scrollLeft}>‹</button>
                <div
                    className="movie-row"
                    ref={rowRef}
                    onWheel={handleWheel} // Optional: Enable to force wheel to scroll horizontal
                >
                    {movies.map((movie) => (
                        <MovieCard key={movie.id} movie={movie} onClick={onMovieClick} />
                    ))}
                </div>
                <button className="carousel-nav right" onClick={scrollRight}>›</button>
            </div>
        </div>
    );
};

const MovieSidebar = ({ movie, onClose }) => {
    if (!movie) return null;

    return (
        <div className="movie-sidebar">
            <button className="close-btn" onClick={onClose}>×</button>
            <div className="sidebar-content">
                <div className="sidebar-poster-wrapper">
                    <img src={movie.poster} alt={movie.title} className="sidebar-poster" />
                </div>
                <h2>{movie.title}</h2>
                <div className="sidebar-meta">
                    <span className="rating-badge">★ {movie.rating}</span>
                    <span className="duration">{movie.duration}</span>
                    <span className="year">{movie.releaseDate}</span>
                </div>
                <div className="sidebar-section">
                    <h3>Résumé</h3>
                    <p className="summary">{movie.summary}</p>
                </div>
                <div className="sidebar-section">
                    <h3>Réalisateur</h3>
                    <p>{movie.director}</p>
                </div>
                <div className="sidebar-section">
                    <h3>Plateformes</h3>
                    <div className="platform-tags">
                        {movie.platforms.map(p => (
                            <span key={p} className="platform-tag">{p}</span>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default function Films() {
    console.log("Films Page Loaded - Version with Platform Filter");
    const [selectedMovie, setSelectedMovie] = useState(null);
    const [selectedPlatforms, setSelectedPlatforms] = useState([]); // Array of platform IDs

    return (
        <div className="page films-page">
            <header className="films-header">
                <div className="header-left">
                    <div className="logo-container">
                        <span className="logo-icon">🍿</span>
                        <h1 className="logo-text">POPCORN</h1>
                    </div>
                    <div className="nav-links">
                        <NavLink to="/" className={({ isActive }) => `nav-btn ${isActive ? "active" : ""}`}>
                            Accueil
                        </NavLink>
                        <NavLink to="/films" className={({ isActive }) => `nav-btn ${isActive ? "active" : ""}`}>
                            Films
                        </NavLink>
                        <NavLink to="/chat" className={({ isActive }) => `nav-btn ${isActive ? "active" : ""}`}>
                            Chat
                        </NavLink>
                        <NavLink to="/about" className={({ isActive }) => `nav-btn ${isActive ? "active" : ""}`}>
                            À propos
                        </NavLink>
                    </div>
                </div>
                <div className="header-right">
                    <PlatformFilter
                        selected={selectedPlatforms}
                        onChange={setSelectedPlatforms}
                    />
                </div>
            </header>

            <div className={`films-container ${selectedMovie ? 'sidebar-open' : ''}`}>
                {categories.map((cat, index) => (
                    <CategoryRow
                        key={index}
                        title={cat.title}
                        movies={allMovies.filter(cat.filter)}
                        onMovieClick={setSelectedMovie}
                    />
                ))}
            </div>

            {selectedMovie && (
                <MovieSidebar
                    movie={selectedMovie}
                    onClose={() => setSelectedMovie(null)}
                />
            )}
            {selectedMovie && <div className="sidebar-overlay" onClick={() => setSelectedMovie(null)}></div>}
        </div>
    );
}
