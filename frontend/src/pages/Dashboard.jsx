/**
 * Dashboard Page — Landing page with session list and system overview.
 */
import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import RiskBadge from '../components/RiskBadge';

export default function Dashboard() {
    const [sessions, setSessions] = useState([]);

    const MOCK_SESSIONS = [
        { id: '7708c9e5', created_at: '2024-10-17 08:30', risk_band: 'Moderate Concern', risk_score: 0.58 },
        { id: 'f4b2c1d0', created_at: '2024-10-16 11:20', risk_band: 'High Concern', risk_score: 0.85 },
        { id: 'a1b2c3d4', created_at: '2024-10-15 14:15', risk_band: 'Low Concern', risk_score: 0.12 },
    ];

    useEffect(() => {
        setSessions(MOCK_SESSIONS);
    }, []);

    return (
        <div>
            {/* Hero Section */}
            <div className="mb-10">
                <h1 className="text-3xl font-bold mb-2">
                    Interview <span className="text-primary-400">Dashboard</span>
                </h1>
                <p className="text-surface-200/70 max-w-2xl">
                    Multimodal AI analysis of psychiatric interviews. Upload recordings
                    to analyze facial expressions, speech patterns, and linguistic markers.
                </p>
            </div>

            {/* Quick Stats */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-10">
                <StatCard label="Total Sessions" value={sessions.length || 0} icon="📋" />
                <StatCard label="Patients" value="—" icon="👤" />
                <StatCard label="High Risk Flags" value="—" icon="⚡" />
                <StatCard label="Avg Risk Score" value="—" icon="📊" />
            </div>

            {/* Sessions List */}
            <div className="card">
                <div className="flex items-center justify-between mb-6">
                    <h2 className="text-lg font-semibold">Recent Sessions</h2>
                    <Link
                        to="/new-session"
                        className="px-4 py-2 bg-primary-600 hover:bg-primary-500 rounded-lg text-sm font-medium transition-colors"
                    >
                        + New Session
                    </Link>
                </div>

                {sessions.length === 0 ? (
                    <div className="text-center py-16">
                        <div className="text-4xl mb-4">🎙️</div>
                        <h3 className="text-lg font-medium mb-2">No Sessions Yet</h3>
                        <p className="text-surface-200/50 text-sm max-w-md mx-auto mb-6">
                            Create a new session and upload an interview recording (MP4 or WAV)
                            to begin multimodal AI analysis.
                        </p>
                        <Link
                            to="/new-session"
                            className="px-6 py-2.5 bg-primary-600 hover:bg-primary-500 rounded-lg text-sm font-medium transition-colors"
                        >
                            Create First Session
                        </Link>
                    </div>
                ) : (
                    <div className="space-y-2">
                        {sessions.map((session) => (
                            <Link
                                key={session.id}
                                to={`/session/${session.id}`}
                                className="flex items-center justify-between p-4 rounded-lg hover:bg-surface-800/50 transition-colors"
                            >
                                <div>
                                    <p className="font-medium">Session #{session.id.slice(0, 8)}</p>
                                    <p className="text-xs text-surface-200/50">{session.created_at}</p>
                                </div>
                                <RiskBadge band={session.risk_band} score={session.risk_score} />
                            </Link>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}

function StatCard({ label, value, icon }) {
    return (
        <div className="card-hover flex items-center gap-4">
            <span className="text-2xl">{icon}</span>
            <div>
                <p className="text-2xl font-bold text-white">{value}</p>
                <p className="text-xs text-surface-200/50">{label}</p>
            </div>
        </div>
    );
}
