import React, { useState } from 'react';
import axios from 'axios';
import { FileText, Send, Hash, UserCircle, ShieldAlert, BarChart3, Layers } from 'lucide-react';
import Card from '../components/UI/Card';
import Button from '../components/UI/Button';
import StatusBadge from '../components/UI/StatusBadge';
import { SkeletonCard, SkeletonMetricGrid } from '../components/UI/Skeleton';
import CollapsibleSection from '../components/UI/CollapsibleSection';
import RiskBand, { getRiskLevel } from '../components/UI/RiskBand';
import SectionGroup from '../components/UI/SectionGroup';
import ErrorAlert from '../components/UI/ErrorAlert';
import Section, { SectionDivider } from '../components/Layout/Section';
import { AnimatedBar } from '../components/UI/AnimatedPrimitives';

const API_URL = "http://localhost:8000/api";

function LinguisticMetric({ icon: Icon, label, value, color = 'text-primary', hint }) {
    return (
        <div className="flex items-center justify-between p-3 bg-white rounded-lg" role="group" aria-label={`${label}: ${value}`}>
            <div className="flex items-center gap-2">
                <Icon size={14} className={color} aria-hidden="true" />
                <div>
                    <span className="text-xs font-medium text-clinical-muted">{label}</span>
                    {hint && <p className="text-[10px] text-clinical-muted/60 mt-0.5">{hint}</p>}
                </div>
            </div>
            <span className="text-sm font-semibold text-clinical-text">{value}</span>
        </div>
    );
}

function WordChips({ words, label, color = 'bg-primary-50 text-primary' }) {
    if (!words || words.length === 0) return null;
    return (
        <div>
            <p className="text-xs font-medium text-clinical-muted mb-2">{label}</p>
            <div className="flex flex-wrap gap-1.5" role="list" aria-label={label}>
                {words.map((word, i) => (
                    <span key={i} className={`${color} text-xs px-2 py-0.5 rounded-md font-mono`} role="listitem">
                        {word}
                    </span>
                ))}
            </div>
        </div>
    );
}

export default function NLPPanel() {
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState(null);
    const [error, setError] = useState(null);
    const [textInput, setTextInput] = useState('');

    const handleAnalyze = async () => {
        if (!textInput.trim()) return;
        setLoading(true);
        setError(null);
        setResult(null);

        try {
            const response = await axios.post(`${API_URL}/nlp/analyze`, {
                session_id: "session-" + Date.now(),
                transcript: textInput
            });
            setResult(response.data);
        } catch (err) {
            setError(err.message + ": " + (err.response?.data?.detail || "Backend unavailable"));
        } finally {
            setLoading(false);
        }
    };

    const sentimentLevel = result?.sentiment?.label === 'positive' ? 'positive'
        : result?.sentiment?.label === 'negative' ? 'negative' : 'neutral';

    const linguisticRisk = result
        ? getRiskLevel(
            (result.features?.absolutist_count || 0) * 0.15 +
            (result.sentiment?.label === 'negative' ? 0.4 : 0),
            { low: 0.2, moderate: 0.4, high: 0.6 }
        )
        : null;

    return (
        <div className="animate-fade-in -mx-8 -mt-10" role="region" aria-label="Linguistic Analysis">

            {/* ─── Section 1: Header + Input (mist) ─── */}
            <Section bg="mist" gradient>
                <h2 className="text-xl font-semibold text-clinical-text">Linguistic Analysis</h2>
                <p className="text-sm text-clinical-muted mt-1 mb-6">
                    Extract sentiment, absolutist markers, avoidance words, and pronoun patterns from interview transcripts.
                </p>

                <div className="card-clinical p-5 bg-white">
                    <div className="flex items-center gap-2 mb-3">
                        <FileText size={16} className="text-primary" aria-hidden="true" />
                        <label htmlFor="nlp-transcript" className="text-sm font-medium text-clinical-text">
                            Transcript Input
                        </label>
                        <span className="text-[10px] font-mono text-clinical-muted ml-auto" aria-live="polite">
                            {textInput.length} chars
                        </span>
                    </div>
                    <textarea
                        id="nlp-transcript"
                        className="w-full h-36 p-4 bg-surface rounded-lg border border-clinical-border
                                   text-sm text-clinical-text placeholder-clinical-muted/50
                                   focus:ring-2 focus:ring-primary-100 focus:border-primary outline-none
                                   resize-none transition-all duration-200 font-sans leading-relaxed"
                        placeholder="Paste or type interview transcript here...&#10;&#10;Example: I just feel like nothing ever goes right. I always mess things up and nobody seems to care anymore."
                        value={textInput}
                        onChange={(e) => setTextInput(e.target.value)}
                        aria-describedby="nlp-input-hint"
                    />
                    <p id="nlp-input-hint" className="sr-only">
                        Enter the interview transcript text for linguistic analysis
                    </p>
                    <div className="flex justify-end mt-3">
                        <Button
                            onClick={handleAnalyze}
                            disabled={!textInput.trim()}
                            loading={loading}
                            aria-label="Start linguistic analysis"
                        >
                            <Send size={14} aria-hidden="true" />
                            Analyze
                        </Button>
                    </div>
                </div>
            </Section>

            {/* Error */}
            {error && (
                <Section bg="white" padded>
                    <ErrorAlert message={error} onDismiss={() => setError(null)} />
                </Section>
            )}

            {/* Skeleton */}
            {loading && (
                <Section bg="white" aria-live="polite">
                    <div className="space-y-4">
                        <SkeletonCard height="h-20" />
                        <SkeletonMetricGrid count={4} />
                    </div>
                </Section>
            )}

            {/* ─── Results ─── */}
            {result && (
                <>
                    {/* ─── Section 2: Risk + Sentiment (white) ─── */}
                    <Section bg="white">
                        <div className="space-y-5 animate-slide-up">
                            {linguisticRisk && (
                                <RiskBand
                                    level={linguisticRisk}
                                    label={`Linguistic Pattern: ${linguisticRisk === 'low' ? 'Normal Range' : linguisticRisk === 'moderate' ? 'Elevated Markers' : 'High Absolutist Language'}`}
                                />
                            )}

                            <SectionGroup label="Sentiment Overview">
                                <Card title="Sentiment" icon={Layers}>
                                    <div className="flex items-center justify-between">
                                        <StatusBadge level={sentimentLevel} label={result.sentiment?.label} />
                                        <div className="flex items-center gap-3">
                                            <div className="text-right">
                                                <p className="text-xs text-clinical-muted">Confidence</p>
                                                <p className="text-sm font-semibold text-clinical-text">
                                                    {(result.sentiment?.confidence * 100)?.toFixed(0)}%
                                                </p>
                                            </div>
                                            <AnimatedBar
                                                percentage={(result.sentiment?.confidence || 0) * 100}
                                                color="bg-primary"
                                                height="h-2"
                                                className="w-24"
                                                label="Sentiment confidence"
                                            />
                                        </div>
                                    </div>
                                    <div className="mt-3">
                                        <p className="text-xs text-clinical-muted">Polarity Score</p>
                                        <div className="flex items-center gap-2 mt-1">
                                            <div className="flex-1 h-2 bg-surface rounded-full overflow-hidden relative"
                                                role="meter" aria-valuenow={result.sentiment?.polarity}
                                                aria-valuemin={-1} aria-valuemax={1}
                                                aria-label="Sentiment polarity">
                                                <div className="absolute left-1/2 top-0 w-px h-full bg-clinical-border" />
                                                <div
                                                    className="absolute top-0 h-full bg-primary/60 rounded-full transition-all duration-500"
                                                    style={{
                                                        left: `${Math.min(50, 50 + (result.sentiment?.polarity || 0) * 50)}%`,
                                                        width: `${Math.abs((result.sentiment?.polarity || 0) * 50)}%`,
                                                    }}
                                                />
                                            </div>
                                            <span className="text-xs font-mono text-clinical-muted w-10 text-right">
                                                {result.sentiment?.polarity?.toFixed(2)}
                                            </span>
                                        </div>
                                    </div>
                                </Card>
                            </SectionGroup>
                        </div>
                    </Section>

                    <SectionDivider variant="fade" />

                    {/* ─── Section 3: Key Markers (sage) ─── */}
                    <Section bg="sage">
                        <SectionGroup label="Linguistic Markers">
                            <div className="grid grid-cols-2 gap-2">
                                <LinguisticMetric
                                    icon={ShieldAlert} label="Absolutist Words"
                                    value={result.features?.absolutist_count || 0}
                                    color="text-risk-high" hint="always, never, nothing..."
                                />
                                <LinguisticMetric
                                    icon={UserCircle} label="1st Person Pronouns"
                                    value={result.features?.first_person_pronouns || 0}
                                    color="text-primary" hint="Self-referential language"
                                />
                            </div>
                        </SectionGroup>
                    </Section>

                    <SectionDivider variant="fade" />

                    {/* ─── Section 4: Advanced Detail (stone) ─── */}
                    <Section bg="stone">
                        <CollapsibleSection
                            title="Detailed Markers"
                            subtitle="Sentence complexity, avoidance words, and word-level data"
                            icon={Hash}
                            badge={
                                <span className="text-[10px] font-mono text-clinical-muted bg-white px-1.5 py-0.5 rounded">
                                    {result.processing_time?.toFixed(2)}s
                                </span>
                            }
                        >
                            <div className="space-y-4 mt-3">
                                <div className="grid grid-cols-2 gap-2">
                                    <LinguisticMetric
                                        icon={BarChart3} label="Sentence Complexity"
                                        value={result.features?.sentence_complexity?.toFixed(2) || '—'}
                                        color="text-accent"
                                    />
                                    <LinguisticMetric
                                        icon={Hash} label="Avoidance Words"
                                        value={result.features?.avoidance_words?.length || 0}
                                        color="text-risk-moderate"
                                    />
                                </div>
                                <WordChips
                                    words={result.features?.absolutist_words}
                                    label="Absolutist Words Found"
                                    color="bg-red-50 text-red-600"
                                />
                                <WordChips
                                    words={result.features?.avoidance_words}
                                    label="Avoidance Markers Found"
                                    color="bg-amber-50 text-amber-700"
                                />
                            </div>
                        </CollapsibleSection>
                    </Section>
                </>
            )}
        </div>
    );
}
