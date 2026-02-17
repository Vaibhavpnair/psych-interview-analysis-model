import { Routes, Route } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import SessionView from './pages/SessionView';
import NewSession from './pages/NewSession';

function App() {
    return (
        <div className="min-h-screen bg-surface-950 text-white">
            {/* Navigation Bar */}
            <nav className="border-b border-surface-800 bg-surface-900/80 backdrop-blur-sm sticky top-0 z-50">
                <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="w-8 h-8 bg-gradient-to-br from-primary-500 to-primary-700 rounded-lg flex items-center justify-center">
                            <span className="text-white font-bold text-sm">Ψ</span>
                        </div>
                        <h1 className="text-lg font-semibold tracking-tight">
                            Psych<span className="text-primary-400">AI</span>
                        </h1>
                    </div>
                    <div className="flex items-center gap-4 text-sm text-surface-200">
                        <span className="px-3 py-1.5 bg-surface-800 rounded-lg text-xs">
                            Decision Support Tool
                        </span>
                        <span>v0.1.0</span>
                    </div>
                </div>
            </nav>

            {/* Main Content */}
            <main className="max-w-7xl mx-auto px-6 py-8">
                <Routes>
                    <Route path="/" element={<Dashboard />} />
                    <Route path="/new-session" element={<NewSession />} />
                    <Route path="/session/:id" element={<SessionView />} />
                </Routes>
            </main>

            {/* Footer */}
            <footer className="border-t border-surface-800 mt-16 py-6 text-center text-xs text-surface-200/50">
                <p>⚠️ This system is for decision support only. Not for autonomous diagnosis.</p>
            </footer>
        </div>
    );
}

export default App;
