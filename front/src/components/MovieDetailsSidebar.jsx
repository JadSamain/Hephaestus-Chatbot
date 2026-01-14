import React from 'react';
import './MovieDetailsSidebar.css';

const platformLogos = {
    "Netflix": "https://upload.wikimedia.org/wikipedia/commons/0/08/Netflix_2015_logo.svg",
    "Prime Video": "https://upload.wikimedia.org/wikipedia/commons/1/11/Amazon_Prime_Video_logo.svg",
    "Disney+": "https://upload.wikimedia.org/wikipedia/commons/3/3e/Disney%2B_logo.svg",
    "Max": "https://upload.wikimedia.org/wikipedia/commons/4/4a/Max_logo.svg",
    "Hulu": "https://upload.wikimedia.org/wikipedia/commons/e/e4/Hulu_Logo.svg",
    "Apple TV+": "https://upload.wikimedia.org/wikipedia/commons/2/28/Apple_TV_Plus_Logo.svg",
    "Paramount+": "https://upload.wikimedia.org/wikipedia/commons/a/a5/Paramount_Plus.svg",
    "Peacock": "https://upload.wikimedia.org/wikipedia/commons/d/d3/NBCUniversal_Peacock_Logo.svg",
    "Canal+": "https://upload.wikimedia.org/wikipedia/commons/1/1a/Canal%2B.svg",
    "Crunchyroll": "https://upload.wikimedia.org/wikipedia/commons/f/f6/Crunchyroll_Logo.svg"
};

export default function MovieDetailsSidebar({ movie, isOpen, onClose }) {
    if (!movie) return null;

    return (
        <>
            {/* Overlay */}
            <div
                className={`sidebar-overlay ${isOpen ? 'active' : ''}`}
                onClick={onClose}
            />

            {/* Sidebar */}
            <div className={`movie-details-sidebar ${isOpen ? 'open' : ''}`}>
                <button className="close-sidebar-btn" onClick={onClose}>✕</button>

                <div className="sidebar-content">
                    <div className="sidebar-poster">
                        <img src={movie.poster} alt={movie.title} />
                        <div className="sidebar-rating">⭐ {movie.rating}</div>
                    </div>

                    <div className="sidebar-info">
                        <h2>{movie.title}</h2>

                        <div className="info-section">
                            <h3>Disponible sur</h3>
                            <div className="platforms-grid">
                                {movie.platforms && movie.platforms.map((platform, index) => (
                                    <div key={index} className="platform-logo-container">
                                        {platformLogos[platform] ? (
                                            <img
                                                src={platformLogos[platform]}
                                                alt={platform}
                                                className="platform-logo"
                                            />
                                        ) : (
                                            <span className="platform-text">{platform}</span>
                                        )}
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </>
    );
}
