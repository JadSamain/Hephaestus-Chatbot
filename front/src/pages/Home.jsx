import { Link } from "react-router-dom";
import "../App.css";
import logo from "../img/logo.png";

export default function Home() {
    return (
        <div className="page home-page">
            <img src={logo} alt="POPCORN Logo" className="app-logo" />
            <div className="hero">
                <h1>POPCORN</h1>
                <p>
                    Votre assistant cinéma intelligent propulsé par l'IA.
                    Découvrez où regarder vos films et séries préférés (Netflix, Prime Video, Disney+...)
                    et obtenez les notes IMDb instantanément !
                </p>
                <Link className="btn" to="/chat">
                    Découvrir des films
                </Link>
            </div>
        </div>
    );
}
