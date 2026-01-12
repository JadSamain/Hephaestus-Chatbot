import React from 'react';

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
                        <span key={index} className="platform-badge">
                            {platform}
                        </span>
                    ))}
                </div>
            </div>
        </div>
    );
}
