import { Link } from "react-router-dom";
import "../App.css";

export default function Home() {
    return (
        <div className="page">
            <section className="hero">
                <h1>🎬 CineBot</h1>
                <p>
                    Votre assistant cinéma intelligent propulsé par l'IA.
                    Découvrez où regarder vos films et séries préférés (Netflix, Prime Video, Disney+...)
                    et obtenez les notes IMDb instantanément !
                </p>
                <Link className="btn" to="/chat">
                    🍿 Découvrir des films
                </Link>
            </section>
        </div>
    );
}
