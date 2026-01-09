import { Link } from "react-router-dom";
import "../App.css";

export default function Home() {
    return (
        <div className="page">
            <section className="hero">
                <h1>MeteoBot</h1>
                <p>
                    Votre assistant météo intelligent propulsé par l'IA.
                    Obtenez des prévisions en temps réel et des informations météorologiques
                    personnalisées grâce à notre chatbot alimenté par un modèle local.
                </p>
                <Link className="btn" to="/chat">
                    Ouvrir le chat
                </Link>
            </section>
        </div>
    );
}
