import React from 'react';
import { AlertCircle, X } from 'lucide-react';

export default function ErrorAlert({ message, onDismiss }) {
    if (!message) return null;

    return (
        <div className="animate-fade-in bg-red-50 border-l-4 border-risk-high rounded-r-lg p-4 flex items-start gap-3">
            <AlertCircle size={18} className="text-risk-high flex-shrink-0 mt-0.5" />
            <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-red-800">Analysis Error</p>
                <p className="text-xs text-red-600 mt-0.5 break-words">{message}</p>
            </div>
            {onDismiss && (
                <button
                    onClick={onDismiss}
                    className="flex-shrink-0 text-red-400 hover:text-red-600 transition-colors"
                >
                    <X size={16} />
                </button>
            )}
        </div>
    );
}
