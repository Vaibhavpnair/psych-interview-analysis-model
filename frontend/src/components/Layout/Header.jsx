import React from 'react';
import { Activity, Shield } from 'lucide-react';

export default function Header() {
    return (
        <header className="sticky top-0 z-30 bg-white/80 backdrop-blur-md border-b border-clinical-border">
            <div className="flex items-center justify-between px-8 py-4">
                <div className="flex items-center gap-3">
                    <h1 className="text-lg font-semibold text-clinical-text tracking-tight">
                        Clinical Dashboard
                    </h1>
                    <span className="text-[10px] font-mono font-medium text-clinical-muted bg-surface px-2 py-0.5 rounded-full border border-clinical-border">
                        v0.1
                    </span>
                </div>

                <div className="flex items-center gap-4">
                    <div className="flex items-center gap-2 text-xs text-clinical-muted">
                        <span className="relative flex h-2 w-2">
                            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-accent opacity-75"></span>
                            <span className="relative inline-flex rounded-full h-2 w-2 bg-accent"></span>
                        </span>
                        System Online
                    </div>
                    <div className="h-4 w-px bg-clinical-border" />
                    <div className="flex items-center gap-2 text-sm text-clinical-muted">
                        <Shield size={14} className="text-primary" />
                        <span className="font-medium">PDSS</span>
                    </div>
                </div>
            </div>
        </header>
    );
}
