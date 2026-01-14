import { useState, useRef, useEffect } from "react";
import { Link, NavLink } from "react-router-dom";
import "../film.css";
import "./Films.css";

const platformsList = [
    "Netflix", "Prime Video", "Disney+", "Max", "Hulu",
    "Apple TV+", "Paramount+", "Peacock", "Canal+", "Crunchyroll"
];

const categories = [
    {
        title: "Tendances cette semaine",
        movies: [
            {
                id: 1,
                title: "Inception",
                rating: 8.8,
                poster: "https://image.tmdb.org/t/p/w500/9gk7adHYeDvHkCSEqAvQNLV5Uge.jpg",
                platforms: ["Netflix", "Max"],
                director: "Christopher Nolan",
                releaseDate: "2010",
                duration: "2h 28m",
                summary: "Dom Cobb est un voleur expérimenté, le meilleur dans l'art dangereux de l'extraction, volant les secrets les plus précieux pendant que les victimes rêvent. Sa compétence rare a fait de lui un joueur convoité dans ce nouveau monde de l'espionnage industriel."
            },
            {
                id: 2,
                title: "Interstellar",
                rating: 8.6,
                poster: "https://image.tmdb.org/t/p/w500/gEU2QniE6E77NI6lCU6MxlNBvIx.jpg",
                platforms: ["Prime Video", "Paramount+"],
                director: "Christopher Nolan",
                releaseDate: "2014",
                duration: "2h 49m",
                summary: "Une équipe d'explorateurs voyage à travers un trou de ver dans l'espace pour tenter d'assurer la survie de l'humanité."
            },
            {
                id: 3,
                title: "The Dark Knight",
                rating: 9.0,
                poster: "https://image.tmdb.org/t/p/w500/qJ2tW6WMUDux911r6m7haRef0WH.jpg",
                platforms: ["Max", "Canal+"],
                director: "Christopher Nolan",
                releaseDate: "2008",
                duration: "2h 32m",
                summary: "Batman entreprend de démanteler les dernières organisations criminelles de Gotham. Mais il se heurte bientôt à un nouveau génie du crime connu sous le nom de Joker."
            },
            {
                id: 4,
                title: "Avatar",
                rating: 7.8,
                poster: "https://image.tmdb.org/t/p/w500/kyeqWdyUXW608qlYkRqosgbbJyK.jpg",
                platforms: ["Disney+", "Max"],
                director: "James Cameron",
                releaseDate: "2009",
                duration: "2h 42m",
                summary: "Un marine paraplégique envoyé sur la lune Pandora pour une mission unique se retrouve déchiré entre suivre ses ordres et protéger le monde qu'il considère comme le sien."
            },
            {
                id: 13,
                title: "Dune",
                rating: 8.1,
                poster: "https://image.tmdb.org/t/p/w500/d5NXSklXo0qyIYkgV94XAgMIckC.jpg",
                platforms: ["Max", "Canal+"],
                director: "Denis Villeneuve",
                releaseDate: "2021",
                duration: "2h 35m",
                summary: "Paul Atreides, un jeune homme brillant et doué au destin plus grand que lui-même, doit se rendre sur la planète la plus dangereuse de l'univers pour assurer l'avenir de sa famille et de son peuple."
            },
            {
                id: 14,
                title: "Oppenheimer",
                rating: 8.2,
                poster: "https://image.tmdb.org/t/p/w500/8Gxv8gSFCU0XGDykEGv7zR1n2ua.jpg",
                platforms: ["Peacock", "Prime Video"],
                director: "Christopher Nolan",
                releaseDate: "2023",
                duration: "3h 00m",
                summary: "L'histoire de J. Robert Oppenheimer, le physicien théoricien américain qui a joué un rôle clé dans le développement de la bombe atomique."
            },

        ]
    },
    {
        title: "Action & Aventure",
        movies: [
            { id: 5, title: "Avengers: Endgame", rating: 8.4, poster: "https://image.tmdb.org/t/p/w500/or06FN3Dka5tukK1e9sl16pB3iy.jpg", platforms: ["Disney+"] },
            { id: 9, title: "The Matrix", rating: 8.7, poster: "https://image.tmdb.org/t/p/w500/f89U3ADr1oiB1s9GkdPOEpXUk5H.jpg", platforms: ["Max", "Peacock"] },
            { id: 15, title: "Gladiator", rating: 8.5, poster: "https://image.tmdb.org/t/p/w500/ty8TGRuvJLPUmAR1H1nRIsgwvim.jpg", platforms: ["Prime Video", "Paramount+"] },
            { id: 16, title: "Top Gun: Maverick", rating: 8.3, poster: "https://image.tmdb.org/t/p/w500/62HCnUTziyWcpDaBO2i1DX17ljH.jpg", platforms: ["Paramount+", "Canal+"] },
            { id: 17, title: "Mad Max: Fury Road", rating: 8.1, poster: "https://image.tmdb.org/t/p/w500/8tZYtuWezp8JbcsvHYO0O46tFbo.jpg", platforms: ["Max", "Hulu"] },
            { id: 105, title: "Avengers: Endgame", rating: 8.4, poster: "https://image.tmdb.org/t/p/w500/or06FN3Dka5tukK1e9sl16pB3iy.jpg", platforms: ["Disney+"] },
            { id: 109, title: "The Matrix", rating: 8.7, poster: "https://image.tmdb.org/t/p/w500/f89U3ADr1oiB1s9GkdPOEpXUk5H.jpg", platforms: ["Max", "Peacock"] },
            { id: 115, title: "Gladiator", rating: 8.5, poster: "https://image.tmdb.org/t/p/w500/ty8TGRuvJLPUmAR1H1nRIsgwvim.jpg", platforms: ["Prime Video", "Paramount+"] },
        ]
    },
    {
        title: "Classiques Cultes",
        movies: [
            { id: 6, title: "Titanic", rating: 7.9, poster: "https://image.tmdb.org/t/p/w500/9xjZS2rlVxm8SFx8kPC3aIGCOYQ.jpg", platforms: ["Paramount+", "Disney+"] },
            { id: 10, title: "Fight Club", rating: 8.8, poster: "https://image.tmdb.org/t/p/w500/pB8BM7pdSp6B6Ih7Qf4n6a87u0F.jpg", platforms: ["Hulu", "Disney+"] },
            { id: 11, title: "Pulp Fiction", rating: 8.9, poster: "https://image.tmdb.org/t/p/w500/d5iIlFn5s0ImszYzBPb8JPIfbXD.jpg", platforms: ["Max", "Paramount+"] },
            { id: 12, title: "Forrest Gump", rating: 8.8, poster: "https://image.tmdb.org/t/p/w500/arw2vcBveWOVZr6pxd9XTd1TdQa.jpg", platforms: ["Paramount+", "Prime Video"] },
            { id: 18, title: "Goodfellas", rating: 8.7, poster: "https://image.tmdb.org/t/p/w500/aKuFiU82s5ISJpGZp7YkIr3kCUd.jpg", platforms: ["Max"] },
            { id: 106, title: "Titanic", rating: 7.9, poster: "https://image.tmdb.org/t/p/w500/9xjZS2rlVxm8SFx8kPC3aIGCOYQ.jpg", platforms: ["Paramount+", "Disney+"] },
            { id: 110, title: "Fight Club", rating: 8.8, poster: "https://image.tmdb.org/t/p/w500/pB8BM7pdSp6B6Ih7Qf4n6a87u0F.jpg", platforms: ["Hulu", "Disney+"] },
            { id: 111, title: "Pulp Fiction", rating: 8.9, poster: "https://image.tmdb.org/t/p/w500/d5iIlFn5s0ImszYzBPb8JPIfbXD.jpg", platforms: ["Max", "Paramount+"] },
        ]
    },
    {
        title: "Drames & Émotion",
        movies: [
            { id: 7, title: "Joker", rating: 8.2, poster: "https://image.tmdb.org/t/p/w500/udDclJoHjfjb8EkGsdr7UU7q1ZE.jpg", platforms: ["Max", "Netflix"] },
            { id: 8, title: "Parasite", rating: 8.5, poster: "https://image.tmdb.org/t/p/w500/7IiTTgloJzvGI1TAYymCfbfl3vT.jpg", platforms: ["Hulu", "Max"] },
            { id: 19, title: "The Shawshank Redemption", rating: 9.3, poster: "https://image.tmdb.org/t/p/w500/q6y0Go1tsGEsmtFryDOJo3dEmqu.jpg", platforms: ["Max"] },
            { id: 20, title: "Schindler's List", rating: 9.0, poster: "https://image.tmdb.org/t/p/w500/sF1U4EUQS8YHUYjNl3pMGNIQyr0.jpg", platforms: ["Peacock"] },
            { id: 107, title: "Joker", rating: 8.2, poster: "https://image.tmdb.org/t/p/w500/udDclJoHjfjb8EkGsdr7UU7q1ZE.jpg", platforms: ["Max", "Netflix"] },
            { id: 108, title: "Parasite", rating: 8.5, poster: "https://image.tmdb.org/t/p/w500/7IiTTgloJzvGI1TAYymCfbfl3vT.jpg", platforms: ["Hulu", "Max"] },
        ]
    },
    {
        title: "Animation & Anime",
        movies: [
            { id: 21, title: "Spirited Away", rating: 8.5, poster: "https://image.tmdb.org/t/p/w500/39wmItIWsg5sZMyRUKGnSxQbUgZ.jpg", platforms: ["Crunchyroll", "Max"] },
            { id: 22, title: "Spider-Man: Into the Spider-Verse", rating: 8.4, poster: "https://image.tmdb.org/t/p/w500/iiZZdoQBEYBv6id8su7ImL0oCbD.jpg", platforms: ["Netflix", "Disney+"] },
            { id: 23, title: "Demon Slayer: Mugen Train", rating: 8.2, poster: "https://image.tmdb.org/t/p/w500/h8Rb9gBr48ODIwYUttZNYeMWeQI.jpg", platforms: ["Crunchyroll"] },
            { id: 24, title: "Your Name", rating: 8.5, poster: "https://image.tmdb.org/t/p/w500/q719jXXEzOoYaps6babgKnONONX.jpg", platforms: ["Crunchyroll", "Prime Video"] },
            { id: 121, title: "Spirited Away", rating: 8.5, poster: "https://image.tmdb.org/t/p/w500/39wmItIWsg5sZMyRUKGnSxQbUgZ.jpg", platforms: ["Crunchyroll", "Max"] },
            { id: 122, title: "Spider-Man: Into the Spider-Verse", rating: 8.4, poster: "https://image.tmdb.org/t/p/w500/iiZZdoQBEYBv6id8su7ImL0oCbD.jpg", platforms: ["Netflix", "Disney+"] },
        ]
    }
];

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
                    <span className="duration">{movie.duration || "2h 15m"}</span>
                    <span className="year">{movie.releaseDate || "2023"}</span>
                </div>

                <div className="sidebar-section">
                    <h3>Résumé</h3>
                    <p className="summary">{movie.summary || "Aucun résumé disponible pour ce film."}</p>
                </div>

                <div className="sidebar-section">
                    <h3>Réalisateur</h3>
                    <p>{movie.director || "Information non disponible"}</p>
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

const MovieRow = ({ movies, onMovieClick }) => {
    const rowRef = useRef(null);
    const [isDragging, setIsDragging] = useState(false);
    const [startX, setStartX] = useState(0);
    const [scrollLeft, setScrollLeft] = useState(0);

    // Remove wheel blocking to restore vertical page scroll.
    // Trackpads will handle horizontal scroll natively via deltaX.
    // Mouse users can use the drag functionality.

    // Drag events
    const onMouseDown = (e) => {
        setIsDragging(true);
        setStartX(e.pageX - rowRef.current.offsetLeft);
        setScrollLeft(rowRef.current.scrollLeft);
    };

    const onMouseLeave = () => {
        setIsDragging(false);
    };

    const onMouseUp = () => {
        setIsDragging(false);
    };

    const onMouseMove = (e) => {
        if (!isDragging) return;
        e.preventDefault();
        const x = e.pageX - rowRef.current.offsetLeft;
        if (Math.abs(x - startX) > 5) { // Threshold to differentiate click from drag
            // Logic handled by click handler check if needed, but for simple scroll:
        }
        const walk = (x - startX) * 2; // scroll-fast
        rowRef.current.scrollLeft = scrollLeft - walk;
    };

    // To prevent firing click after dragging
    const [wasDragging, setWasDragging] = useState(false);

    return (
        <div
            className="movie-row"
            ref={rowRef}
            onMouseDown={(e) => {
                setWasDragging(false);
                onMouseDown(e);
            }}
            onMouseLeave={onMouseLeave}
            onMouseUp={() => {
                onMouseUp();
                setTimeout(() => setWasDragging(false), 50);
            }}
            onMouseMove={(e) => {
                setWasDragging(true);
                onMouseMove(e);
            }}
            onClickCapture={(e) => {
                if (wasDragging) {
                    e.stopPropagation();
                    e.preventDefault();
                }
            }}
        >
            {movies.map((movie) => (
                <div key={movie.id} className="movie-card" onClick={() => !wasDragging && onMovieClick(movie)}>
                    <div className="movie-poster-wrapper">
                        <img src={movie.poster} alt={movie.title} className="movie-poster" />
                        <div className="movie-rating">{movie.rating}</div>
                    </div>
                    <div className="movie-info">
                        <h4>{movie.title}</h4>
                    </div>
                </div>
            ))}
        </div>
    );
};

export default function Films() {
    const [selectedPlatform, setSelectedPlatform] = useState("All");
    const [selectedMovie, setSelectedMovie] = useState(null);

    const filteredCategories = categories.map(category => ({
        ...category,
        movies: category.movies.filter(movie =>
            selectedPlatform === "All" || movie.platforms.includes(selectedPlatform)
        )
    })).filter(category => category.movies.length > 0);

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
                    <Link to="/" className="back-btn">← Retour</Link>
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

            <div className={`films-container ${selectedMovie ? 'sidebar-open' : ''}`}>
                {filteredCategories.length > 0 ? (
                    filteredCategories.map((category, index) => (
                        <div key={index} className="category-section">
                            <h3 className="category-title">{category.title}</h3>
                            <MovieRow
                                movies={category.movies}
                                onMovieClick={setSelectedMovie}
                            />
                        </div>
                    ))
                ) : (
                    <div className="empty-state">
                        <div className="empty-state-icon">🎬</div>
                        <h3>Aucun film trouvé</h3>
                        <p>Essayez de choisir une autre plateforme.</p>
                    </div>
                )}
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
