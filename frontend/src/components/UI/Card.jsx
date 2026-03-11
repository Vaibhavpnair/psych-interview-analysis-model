import React from 'react';

export default function Card({ title, subtitle, icon: Icon, children, className = '', animate = true }) {
    return (
        <div className={`card-clinical ${animate ? 'animate-fade-in' : ''} ${className}`}>
            {(title || Icon) && (
                <div className="flex items-center gap-3 px-5 pt-5 pb-3">
                    {Icon && (
                        <div className="w-9 h-9 rounded-lg bg-primary-50 flex items-center justify-center flex-shrink-0">
                            <Icon size={18} className="text-primary" />
                        </div>
                    )}
                    <div>
                        {title && <h3 className="text-sm font-semibold text-clinical-text">{title}</h3>}
                        {subtitle && <p className="text-xs text-clinical-muted mt-0.5">{subtitle}</p>}
                    </div>
                </div>
            )}
            <div className="px-5 pb-5">
                {children}
            </div>
        </div>
    );
}
