import { Link } from "react-router-dom";
import "../App.css";

const movies = [
    { id: 1, title: "Inception", rating: 8.8, poster: "https://image.tmdb.org/t/p/w500/9gk7adHYeDvHkCSEqAvQNLV5Uge.jpg" },
    { id: 2, title: "Interstellar", rating: 8.6, poster: "https://image.tmdb.org/t/p/w500/gEU2QniE6E77NI6lCU6MxlNBvIx.jpg" },
    { id: 3, title: "The Dark Knight", rating: 9.0, poster: "https://image.tmdb.org/t/p/w500/qJ2tW6WMUDux911r6m7haRef0WH.jpg" },
    { id: 4, title: "Avatar", rating: 7.8, poster: "https://image.tmdb.org/t/p/w500/kyeqWdyUXW608qlYkRqosgbbJyK.jpg" },
    { id: 5, title: "Avengers: Endgame", rating: 8.4, poster: "https://image.tmdb.org/t/p/w500/or06FN3Dka5tukK1e9sl16pB3iy.jpg" },
    { id: 6, title: "Titanic", rating: 7.9, poster: "https://image.tmdb.org/t/p/w500/9xjZS2rlVxm8SFx8kPC3aIGCOYQ.jpg" },
    { id: 7, title: "Joker", rating: 8.2, poster: "https://image.tmdb.org/t/p/w500/udDclJoHjfjb8EkGsdr7UU7q1ZE.jpg" },
    { id: 8, title: "Parasite", rating: 8.5, poster: "https://image.tmdb.org/t/p/w500/7IiTTgloJzvGI1TAYymCfbfl3vT.jpg" },
    { id: 9, title: "The Matrix", rating: 8.7, poster: "https://image.tmdb.org/t/p/w500/f89U3ADr1oiB1s9GkdPOEpXUk5H.jpg" },
    { id: 10, title: "Fight Club", rating: 8.8, poster: "https://image.tmdb.org/t/p/w500/pB8BM7pdSp6B6Ih7Qf4n6a87u0F.jpg" },
    { id: 11, title: "Pulp Fiction", rating: 8.9, poster: "https://image.tmdb.org/t/p/w500/d5iIlFn5s0ImszYzBPb8JPIfbXD.jpg" },
    { id: 12, title: "Forrest Gump", rating: 8.8, poster: "https://image.tmdb.org/t/p/w500/arw2vcBveWOVZr6pxd9XTd1TdQa.jpg" },
];

export default function Films() {
    return (
        <div className="page films-page">
            <header className="films-header">
                <h2>Films Populaires</h2>
                <Link to="/" className="back-btn">← Retour</Link>
            </header>

            <div className="films-grid-container">
                <div className="films-grid">
                    {movies.map((movie) => (
                        <div key={movie.id} className="movie-card">
                            <div className="movie-poster-wrapper">
                                <img src={movie.poster} alt={movie.title} className="movie-poster" />
                                <div className="movie-rating">{movie.rating}</div>
                            </div>
                            <div className="movie-info">
                                <h3>{movie.title}</h3>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}
