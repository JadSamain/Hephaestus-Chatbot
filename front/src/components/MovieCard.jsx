import React from 'react';

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

export default function MovieCard({ title, year, poster, rating, platforms }) {
    return (
        <div className="movie-card">
            <div className="movie-poster">
                {poster ? (
                    <img src={poster} alt={title} />
                ) : (
                    <div className="no-poster">🎬</div>
                )}
            </div>
            <div className="movie-info">
                <h4>{title} <span className="movie-year">({year})</span></h4>

                <div className="movie-rating">
                    ⭐ {rating}
                </div>

                <div className="movie-platforms">
                    {platforms && platforms.map((platform, index) => (
                        <div key={index} className="platform-logo-badge">
                            {platformLogos[platform] ? (
                                <img
                                    src={platformLogos[platform]}
                                    alt={platform}
                                    className="platform-logo-img"
                                    title={platform}
                                />
                            ) : (
                                <span className="platform-badge">{platform}</span>
                            )}
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}
