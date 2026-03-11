import React from 'react';
import { Activity } from 'lucide-react';

export default function LoadingOverlay({ message = 'Processing...', detail = '' }) {
    return (
        <div className="flex flex-col items-center justify-center py-16 animate-fade-in">
            <div className="relative mb-6">
                <div className="w-12 h-12 rounded-full border-2 border-primary-100 flex items-center justify-center">
                    <Activity size={20} className="text-primary animate-pulse-soft" />
                </div>
                <div className="absolute inset-0 w-12 h-12 rounded-full border-2 border-primary/30 animate-pulse-ring" />
            </div>
            <p className="text-sm font-medium text-clinical-text">{message}</p>
            {detail && (
                <p className="text-xs text-clinical-muted mt-1 font-mono">{detail}</p>
            )}
        </div>
    );
}
