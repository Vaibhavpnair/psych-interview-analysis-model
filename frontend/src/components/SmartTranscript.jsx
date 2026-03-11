/**
 * SmartTranscript — Zone C of the dashboard.
 * Annotated transcript with highlighted absolutist terms, filler words, and pauses.
 */

import { useState } from 'react';

export default function SmartTranscript({ segments = [] }) {
    const [searchTerm, setSearchTerm] = useState('');

    if (segments.length === 0) {
        return (
            <div className="card-floating animate-in h-96 flex flex-col">
                <h3 className="text-[10px] font-bold uppercase tracking-widest text-surface-400 mb-6">
                    Annotated Transcript
                </h3>
                <div className="flex-1 flex flex-col items-center justify-center text-surface-400 gap-3 border-2 border-dashed border-surface-800 rounded-xl">
                    <span className="text-3xl opacity-20">📜</span>
                    <p className="text-sm font-medium text-surface-500">Transcript generation in progress...</p>
                </div>
            </div>
        );
    }

    const formatTime = (seconds) => {
        const m = Math.floor(seconds / 60);
        const s = Math.floor(seconds % 60);
        return `${m}:${s.toString().padStart(2, '0')}`;
    };

    // Words to highlight based on clinical significance
    const HIGHLIGHTS = {
        absolutist: ['always', 'never', 'completely', 'forever', 'must', 'should', 'cannot', 'impossible'],
        filler: ['uhm', 'uh', 'like', 'you know', 'actually', 'basically'],
        avoidance: ['maybe', 'perhaps', 'suppose', 'think', 'feel', 'guess', 'likely'],
    };

    const highlightText = (text) => {
        if (!text) return text;
        const words = text.split(' ');

        return words.map((word, i) => {
            const cleanWord = word.toLowerCase().replace(/[.,!?;:]/g, '');
            let colorClass = '';

            if (HIGHLIGHTS.absolutist.includes(cleanWord)) colorClass = 'bg-risk-high/10 text-risk-high border-risk-high/30';
            else if (HIGHLIGHTS.filler.includes(cleanWord)) colorClass = 'bg-primary-500/10 text-primary-400 border-primary-500/20';
            else if (HIGHLIGHTS.avoidance.includes(cleanWord)) colorClass = 'bg-amber-500/10 text-amber-500 border-amber-500/20';

            if (colorClass) {
                return (
                    <span
                        key={i}
                        className={`${colorClass} px-1 rounded border inline-block cursor-help transition-all hover:bg-current/20`}
                        title={`Marker: ${cleanWord}`}
                    >
                        {word}{' '}
                    </span>
                );
            }
            return word + ' ';
        });
    };

    const filteredSegments = segments.filter(seg =>
        seg.text.toLowerCase().includes(searchTerm.toLowerCase())
    );

    return (
        <div className="card-floating animate-in h-[600px] flex flex-col group/transcript">
            {/* Header + Search */}
            <div className="flex items-center justify-between mb-6 shrink-0">
                <h3 className="text-[10px] font-bold uppercase tracking-widest text-surface-400">
                    Smart Transcript
                </h3>
                <div className="relative">
                    <input
                        type="text"
                        placeholder="Search transcript..."
                        className="bg-surface-800/50 border border-surface-700/50 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-primary-500/50 w-48 transition-all"
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                    />
                    <span className="absolute right-3 top-2 opacity-30 text-xs">🔍</span>
                </div>
            </div>

            {/* Legend */}
            <div className="flex gap-4 mb-4 shrink-0 pb-3 border-b border-surface-800">
                <BadgeLegend color="text-risk-high" label="Absolutist" />
                <BadgeLegend color="text-amber-500" label="Avoidance" />
                <BadgeLegend color="text-primary-400" label="Filler" />
            </div>

            {/* Scrollable Container */}
            <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar">
                <div className="space-y-4">
                    {filteredSegments.map((seg) => (
                        <div
                            key={seg.segment_id || seg.timestamp_start}
                            className="group flex gap-4 p-4 rounded-xl hover:bg-surface-800/30 border border-transparent hover:border-surface-700/30 transition-all cursor-pointer"
                            onClick={() => console.log(`Seek to ${seg.timestamp_start}`)} // TODO: Bind to player
                        >
                            {/* Metadata */}
                            <div className="flex flex-col items-center gap-2 shrink-0 w-12 pt-1">
                                <span className="text-[10px] font-mono font-bold text-primary-500">
                                    {formatTime(seg.timestamp_start)}
                                </span>
                                <div className={`w-1.5 h-1.5 rounded-full ${seg.speaker === 'patient' ? 'bg-primary-500' : 'bg-surface-600'
                                    }`} />
                            </div>

                            {/* Content */}
                            <div className="flex-1 space-y-2">
                                <div className="flex items-center gap-2">
                                    <span className={`text-[10px] font-black uppercase tracking-widest px-2 py-0.5 rounded shadow-sm ${seg.speaker === 'patient'
                                            ? 'bg-primary-500/20 text-primary-400'
                                            : 'bg-surface-700 text-surface-400'
                                        }`}>
                                        {seg.speaker}
                                    </span>
                                    {seg.flag && (
                                        <span className="text-[10px] bg-risk-high/10 text-risk-high px-2 py-0.5 rounded font-bold border border-risk-high/20">
                                            {seg.flag}
                                        </span>
                                    )}
                                </div>
                                <p className="text-sm text-surface-200 leading-relaxed font-medium">
                                    {highlightText(seg.text)}
                                </p>
                            </div>
                        </div>
                    ))}

                    {filteredSegments.length === 0 && (
                        <div className="text-center py-20 text-surface-500 text-sm italic">
                            No segments match your search criteria
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

function BadgeLegend({ color, label }) {
    return (
        <div className="flex items-center gap-1.5">
            <div className={`w-1 h-1 rounded-full bg-current ${color}`} />
            <span className={`text-[9px] font-bold uppercase tracking-widest ${color} opacity-80`}>{label}</span>
        </div>
    );
}
