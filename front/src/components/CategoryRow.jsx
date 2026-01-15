import { useRef } from 'react';

const CategoryRow = ({ title, movies, onMovieClick }) => {
    const rowRef = useRef(null);

    const scroll = (direction) => {
        if (rowRef.current) {
            const { current } = rowRef;
            const scrollAmount = direction === 'left' ? -300 : 300;
            current.scrollBy({ left: scrollAmount, behavior: 'smooth' });
        }
    };

    return (
        <div className="category-section">
            <h3 className="category-title">{title}</h3>
            <div className="row-container">
                <button
                    className="scroll-btn left"
                    onClick={() => scroll('left')}
                    aria-label="Scroll left"
                >
                    &#10094;
                </button>

                <div className="movie-row" ref={rowRef}>
                    {movies.map((movie) => (
                        <div
                            key={movie.id}
                            className="movie-card"
                            onClick={() => onMovieClick(movie)}
                        >
                            <div className="movie-poster-wrapper">
                                <img src={movie.poster} alt={movie.title} className="movie-poster" />
                                <div className="movie-rating">{movie.rating}</div>
                            </div>
                            <div className="movie-info">
                                <h4>{movie.title}</h4>
                                <span className="movie-year">{movie.year}</span>
                            </div>
                        </div>
                    ))}
                </div>

                <button
                    className="scroll-btn right"
                    onClick={() => scroll('right')}
                    aria-label="Scroll right"
                >
                    &#10095;
                </button>
            </div>
        </div>
    );
};

export default CategoryRow;
