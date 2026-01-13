import React from 'react';
import { Link } from 'react-router-dom';
import '../App.css'; // Assuming we want to reuse main styles

export default function About() {
    return (
        <div className="app-container" style={{ justifyContent: 'center', alignItems: 'center', flexDirection: 'column' }}>
            <h1 style={{ color: 'white' }}>Page À propos</h1>
            <p style={{ color: 'white', marginTop: '20px' }}>
                Ceci est la page à propos.
            </p>
            <Link to="/chat" className="back-btn" style={{ marginTop: '20px', width: 'auto', padding: '10px 20px' }}>
                Retour au Chat
            </Link>
        </div>
    );
}
