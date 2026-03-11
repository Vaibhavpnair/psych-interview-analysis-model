import React from 'react';
import { Mic, FileText, Video, Brain, ChevronLeft, ChevronRight, ClipboardList, Stethoscope } from 'lucide-react';

const modules = [
    { id: 'audio', label: 'Speech Analysis', icon: Mic },
    { id: 'nlp', label: 'Linguistic Analysis', icon: FileText },
    { id: 'vision', label: 'Facial Analysis', icon: Video },
    { id: 'questionnaire', label: 'DSM-5 Screening Form', icon: ClipboardList },
    { id: 'assessment', label: 'Structured Assessment', icon: Stethoscope },
];

export default function Sidebar({ activeTab, onTabChange, collapsed, onToggle }) {
    return (
        <aside
            className={`fixed left-0 top-0 h-screen bg-sidebar flex flex-col z-40 transition-all duration-300 ease-out
                ${collapsed ? 'w-[68px]' : 'w-[240px]'}`}
        >
            {/* Logo */}
            <div className="flex items-center gap-3 px-5 py-6 border-b border-white/5">
                <div className="flex-shrink-0 w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
                    <Brain size={18} className="text-white" />
                </div>
                {!collapsed && (
                    <div className="animate-fade-in">
                        <p className="text-white text-sm font-semibold tracking-tight">PDSS</p>
                        <p className="text-slate-500 text-[10px] font-mono">Psychiatric DSS</p>
                    </div>
                )}
            </div>

            {/* Navigation */}
            <nav className="flex-1 px-3 py-6 space-y-1">
                {!collapsed && (
                    <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-widest px-4 mb-3">
                        Modules
                    </p>
                )}
                {modules.map((mod) => {
                    const Icon = mod.icon;
                    const isActive = activeTab === mod.id;
                    return (
                        <button
                            key={mod.id}
                            onClick={() => onTabChange(mod.id)}
                            className={`w-full nav-item ${isActive ? 'active' : ''}`}
                            title={mod.label}
                        >
                            <Icon size={18} />
                            {!collapsed && <span className="whitespace-nowrap">{mod.label}</span>}
                        </button>
                    );
                })}
            </nav>

            {/* Collapse Toggle */}
            <div className="px-3 py-4 border-t border-white/5">
                <button
                    onClick={onToggle}
                    className="w-full nav-item justify-center"
                    title={collapsed ? 'Expand' : 'Collapse'}
                >
                    {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
                    {!collapsed && <span className="text-xs">Collapse</span>}
                </button>
            </div>
        </aside>
    );
}
