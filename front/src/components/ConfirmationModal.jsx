import React from 'react';
import '../App.css';

export default function ConfirmationModal({ isOpen, onClose, onConfirm, message }) {
    if (!isOpen) return null;

    return (
        <div className="modal-overlay">
            <div className="modal-content">
                <h3>Confirmation</h3>
                <p>{message}</p>
                <div className="modal-actions">
                    <button className="modal-btn cancel-btn" onClick={onClose}>
                        Annuler
                    </button>
                    <button className="modal-btn confirm-btn" onClick={onConfirm}>
                        Supprimer
                    </button>
                </div>
            </div>
        </div>
    );
}
