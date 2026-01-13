import { useState } from "react";
import { Link } from "react-router-dom";
import "../film.css";

const platformsList = [
    "Netflix", "Prime Video", "Disney+", "Max", "Hulu",
    "Apple TV+", "Paramount+", "Peacock", "Canal+", "Crunchyroll"
];

const categories = [
    {
        title: "Tendances cette semaine",
        movies: [
            { id: 1, title: "Inception", rating: 8.8, poster: "https://image.tmdb.org/t/p/w500/9gk7adHYeDvHkCSEqAvQNLV5Uge.jpg", platforms: ["Netflix", "Max"] },
            { id: 2, title: "Interstellar", rating: 8.6, poster: "https://image.tmdb.org/t/p/w500/gEU2QniE6E77NI6lCU6MxlNBvIx.jpg", platforms: ["Prime Video", "Paramount+"] },
            { id: 3, title: "The Dark Knight", rating: 9.0, poster: "https://image.tmdb.org/t/p/w500/qJ2tW6WMUDux911r6m7haRef0WH.jpg", platforms: ["Max", "Canal+"] },
            { id: 4, title: "Avatar", rating: 7.8, poster: "https://image.tmdb.org/t/p/w500/kyeqWdyUXW608qlYkRqosgbbJyK.jpg", platforms: ["Disney+", "Max"] },
            { id: 13, title: "Dune", rating: 8.1, poster: "https://image.tmdb.org/t/p/w500/d5NXSklXo0qyIYkgV94XAgMIckC.jpg", platforms: ["Max", "Canal+"] },
            { id: 14, title: "Oppenheimer", rating: 8.2, poster: "https://image.tmdb.org/t/p/w500/8Gxv8gSFCU0XGDykEGv7zR1n2ua.jpg", platforms: ["Peacock", "Prime Video"] },
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
        ]
    },
    {
        title: "Drames & Émotion",
        movies: [
            { id: 7, title: "Joker", rating: 8.2, poster: "https://image.tmdb.org/t/p/w500/udDclJoHjfjb8EkGsdr7UU7q1ZE.jpg", platforms: ["Max", "Netflix"] },
            { id: 8, title: "Parasite", rating: 8.5, poster: "https://image.tmdb.org/t/p/w500/7IiTTgloJzvGI1TAYymCfbfl3vT.jpg", platforms: ["Hulu", "Max"] },
            { id: 19, title: "The Shawshank Redemption", rating: 9.3, poster: "https://image.tmdb.org/t/p/w500/q6y0Go1tsGEsmtFryDOJo3dEmqu.jpg", platforms: ["Max"] },
            { id: 20, title: "Schindler's List", rating: 9.0, poster: "https://image.tmdb.org/t/p/w500/sF1U4EUQS8YHUYjNl3pMGNIQyr0.jpg", platforms: ["Peacock"] },
        ]
    },
    {
        title: "Animation & Anime",
        movies: [
            { id: 21, title: "Spirited Away", rating: 8.5, poster: "https://image.tmdb.org/t/p/w500/39wmItIWsg5sZMyRUKGnSxQbUgZ.jpg", platforms: ["Crunchyroll", "Max"] },
            { id: 22, title: "Spider-Man: Into the Spider-Verse", rating: 8.4, poster: "https://image.tmdb.org/t/p/w500/iiZZdoQBEYBv6id8su7ImL0oCbD.jpg", platforms: ["Netflix", "Disney+"] },
            { id: 23, title: "Demon Slayer: Mugen Train", rating: 8.2, poster: "https://image.tmdb.org/t/p/w500/h8Rb9gBr48ODIwYUttZNYeMWeQI.jpg", platforms: ["Crunchyroll"] },
            { id: 24, title: "Your Name", rating: 8.5, poster: "https://image.tmdb.org/t/p/w500/q719jXXEzOoYaps6babgKnONONX.jpg", platforms: ["Crunchyroll", "Prime Video"] },
        ]
    }
];

export default function Films() {
    const [selectedPlatform, setSelectedPlatform] = useState("All");

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
                    <h2>Films Populaires</h2>
                    <Link to="/" className="back-btn">← Retour</Link>
                </div>
                <div className="header-right">
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
                {filteredCategories.length > 0 ? (
                    filteredCategories.map((category, index) => (
                        <div key={index} className="category-section">
                            <h3 className="category-title">{category.title}</h3>
                            <div className="movie-row">
                                {category.movies.map((movie) => (
                                    <div key={movie.id} className="movie-card">
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
        </div>
    );
}
