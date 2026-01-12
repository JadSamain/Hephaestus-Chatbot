import { Link } from "react-router-dom";
import "../App.css";
import logo from "../img/logo.png";

export default function Home() {
    return (
        <div className="page home-page">

            <section className="hero">
                <img src={logo} alt="Popcorn Logo" className="hero-logo-bounce" />
                <h1>POPCORN</h1>
                <p>
                    <span style={{ color: '#FFD700', fontWeight: 'bold' }}>Votre assistant cinéma intelligent propulsé par l'IA.</span>
                    <br />
                    Découvrez où regarder vos films et séries préférés et obtenez des recommandations personnalisées.
                </p>
                <Link className="btn" to="/chat">
                    Ouvrir le Chat
                </Link>
            </section>
        </div>
    );
}
