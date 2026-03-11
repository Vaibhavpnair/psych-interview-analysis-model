import React, { useState, useRef, useEffect } from 'react';
import Header from './components/Layout/Header';
import Sidebar from './components/Layout/Sidebar';
import AudioPanel from './features/AudioPanel';
import NLPPanel from './features/NLPPanel';
import VisionPanel from './features/VisionPanel';

import QuestionnairePanel from './features/QuestionnairePanel';
import AssessmentPanel from './features/AssessmentPanel';

const panels = {
    audio: AudioPanel,
    nlp: NLPPanel,
    vision: VisionPanel,
    questionnaire: QuestionnairePanel,
    assessment: AssessmentPanel,
};

const panelLabels = {
    audio: 'Speech Prosody Analysis',
    nlp: 'Linguistic Analysis',
    vision: 'Facial Expression Analysis',
    questionnaire: 'DSM-5 Level 1 Cross-Cutting Symptom Measure',
    assessment: 'Structured Multimodal Assessment',
};

function App() {
    const [activeTab, setActiveTab] = useState('audio');
    const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
    const [transitioning, setTransitioning] = useState(false);
    const [displayedTab, setDisplayedTab] = useState('audio');
    const mainRef = useRef(null);

    // Cross-fade transition between tabs
    const handleTabChange = (tab) => {
        if (tab === activeTab) return;
        setTransitioning(true);

        // Phase 1: fade out
        setTimeout(() => {
            setDisplayedTab(tab);
            setActiveTab(tab);
            // Phase 2: fade in (triggered by state change)
            requestAnimationFrame(() => {
                setTransitioning(false);
            });
        }, 180);

        // Scroll to top on tab change
        if (mainRef.current) {
            mainRef.current.scrollTo({ top: 0, behavior: 'smooth' });
        }
    };

    const ActivePanel = panels[displayedTab];

    return (
        <div className="min-h-screen bg-surface">
            {/* Skip link for keyboard users */}
            <a
                href="#main-content"
                className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4
                           focus:z-50 focus:bg-primary focus:text-white focus:px-4 focus:py-2
                           focus:rounded-lg focus:shadow-float"
            >
                Skip to main content
            </a>

            {/* Sidebar */}
            <Sidebar
                activeTab={activeTab}
                onTabChange={handleTabChange}
                collapsed={sidebarCollapsed}
                onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
            />

            {/* Main Content */}
            <div
                className={`transition-all duration-300 ease-out ${sidebarCollapsed ? 'ml-[68px]' : 'ml-[240px]'}`}
            >
                <Header />

                <main
                    id="main-content"
                    ref={mainRef}
                    className="p-8 pt-10 overflow-hidden"
                    role="main"
                    aria-label={panelLabels[displayedTab]}
                >
                    <div
                        className={`transition-opacity duration-180 ease-out
                                   ${transitioning ? 'opacity-0 translate-y-1' : 'opacity-100 translate-y-0'}`}
                        style={{ transition: 'opacity 0.18s ease-out, transform 0.18s ease-out' }}
                    >
                        <ActivePanel />
                    </div>
                </main>
            </div>
        </div>
    );
}

export default App;
