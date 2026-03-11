import React, { useState, useCallback } from 'react';
import axios from 'axios';
import {
    ClipboardList, ChevronRight, RotateCcw,
    AlertTriangle, CheckCircle2, XCircle,
    ArrowRight, Shield, Brain
} from 'lucide-react';
import Section, { SectionDivider } from '../components/Layout/Section';
import ErrorAlert from '../components/UI/ErrorAlert';

const API_URL = 'http://localhost:8000/api/questionnaire';

/* ─── Response Button ─────────────────────────────────── */
const SEVERITY_STYLES = [
    { bg: 'bg-emerald-50 hover:bg-emerald-100 border-emerald-200', text: 'text-emerald-700', ring: 'ring-emerald-300' },
    { bg: 'bg-sky-50 hover:bg-sky-100 border-sky-200', text: 'text-sky-700', ring: 'ring-sky-300' },
    { bg: 'bg-amber-50 hover:bg-amber-100 border-amber-200', text: 'text-amber-700', ring: 'ring-amber-300' },
    { bg: 'bg-orange-50 hover:bg-orange-100 border-orange-200', text: 'text-orange-700', ring: 'ring-orange-300' },
    { bg: 'bg-rose-50 hover:bg-rose-100 border-rose-200', text: 'text-rose-700', ring: 'ring-rose-300' },
];

function ResponseButton({ option, onSelect, disabled }) {
    const style = SEVERITY_STYLES[option.value] || SEVERITY_STYLES[0];
    return (
        <button
            onClick={() => onSelect(option.value)}
            disabled={disabled}
            className={`w-full flex items-center justify-between px-4 py-3.5 rounded-xl border
                       transition-all duration-150 ${style.bg} ${style.text}
                       focus:outline-none focus:ring-2 ${style.ring}
                       disabled:opacity-50 disabled:pointer-events-none`}
            id={`response-${option.value}`}
        >
            <div className="flex items-center gap-3">
                <span className="w-7 h-7 rounded-lg bg-white/80 flex items-center justify-center
                               text-xs font-bold shadow-sm border border-black/5">
                    {option.value}
                </span>
                <div className="text-left">
                    <span className="text-sm font-semibold">{option.label}</span>
                    <p className="text-[10px] opacity-70 mt-0.5">{option.description}</p>
                </div>
            </div>
            <ChevronRight size={14} className="opacity-40" />
        </button>
    );
}

/* ─── Domain Result Card ──────────────────────────────── */
function DomainCard({ result }) {
    const exceeded = result.exceeded;
    return (
        <div className={`card-clinical p-4 border-l-4 ${exceeded
            ? 'border-l-rose-400 bg-rose-50/50'
            : 'border-l-emerald-400 bg-emerald-50/30'
            }`}>
            <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                    {exceeded
                        ? <AlertTriangle size={14} className="text-rose-500" />
                        : <CheckCircle2 size={14} className="text-emerald-500" />
                    }
                    <span className="text-sm font-semibold text-clinical-text">
                        {result.domain_label}
                    </span>
                </div>
                <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${exceeded
                    ? 'bg-rose-100 text-rose-700'
                    : 'bg-emerald-100 text-emerald-700'
                    }`}>
                    {exceeded ? 'Threshold Exceeded' : 'Below Threshold'}
                </span>
            </div>
            <div className="flex items-center gap-4 text-xs text-clinical-muted">
                <span>
                    Max score: <strong className="text-clinical-text">{result.max_score}</strong> / 4
                </span>
                <span>
                    Threshold: ≥ {result.threshold_value}
                    ({result.threshold_type === 'slight' ? 'Slight' : 'Mild'})
                </span>
                <span>{result.questions_answered} question{result.questions_answered !== 1 ? 's' : ''}</span>
            </div>
        </div>
    );
}

/* ─── Main Panel ──────────────────────────────────────── */
export default function QuestionnairePanel() {
    const [sessionId, setSessionId] = useState(null);
    const [currentQuestion, setCurrentQuestion] = useState(null);
    const [results, setResults] = useState(null);
    const [loading, setLoading] = useState(false);
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState(null);

    const handleStart = useCallback(async () => {
        setLoading(true);
        setError(null);
        setResults(null);
        try {
            const res = await axios.post(`${API_URL}/start`);
            setSessionId(res.data.session_id);
            setCurrentQuestion(res.data.first_question);
        } catch (err) {
            setError(err.response?.data?.detail || err.message);
        } finally {
            setLoading(false);
        }
    }, []);

    const handleAnswer = useCallback(async (score) => {
        if (!sessionId || !currentQuestion || submitting) return;
        setSubmitting(true);
        setError(null);
        try {
            const res = await axios.post(`${API_URL}/${sessionId}/answer`, {
                question_id: currentQuestion.id,
                score,
            });
            if (res.data.completed) {
                // Fetch results
                const resultsRes = await axios.get(`${API_URL}/${sessionId}/results`);
                setResults(resultsRes.data);
                setCurrentQuestion(null);
            } else {
                setCurrentQuestion(res.data.next_question);
            }
        } catch (err) {
            setError(err.response?.data?.detail || err.message);
        } finally {
            setSubmitting(false);
        }
    }, [sessionId, currentQuestion, submitting]);

    const handleRestart = useCallback(() => {
        setSessionId(null);
        setCurrentQuestion(null);
        setResults(null);
        setError(null);
    }, []);

    // Progress
    const progress = currentQuestion
        ? ((currentQuestion.question_number - 1) / currentQuestion.total_questions) * 100
        : results ? 100 : 0;

    return (
        <div className="animate-fade-in -mx-8 -mt-10" role="region" aria-label="DSM-5 Cross-Cutting Symptom Measure">

            {/* ── Header ── */}
            <Section bg="sage" gradient>
                <div className="flex items-center justify-between mb-1">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-xl bg-primary-50 flex items-center justify-center">
                            <ClipboardList size={20} className="text-primary" />
                        </div>
                        <div>
                            <h2 className="text-xl font-semibold text-clinical-text">
                                DSM-5 Level 1 Cross-Cutting Symptom Measure
                            </h2>
                            <p className="text-xs text-clinical-muted mt-0.5">Adult — 23 questions across 13 symptom domains</p>
                        </div>
                    </div>
                    {(currentQuestion || results) && (
                        <button
                            onClick={handleRestart}
                            className="btn-secondary text-xs px-3 py-1.5 rounded-lg inline-flex items-center gap-1.5"
                            id="restart-questionnaire"
                        >
                            <RotateCcw size={12} />
                            Restart
                        </button>
                    )}
                </div>

                {/* Progress bar */}
                {(currentQuestion || results) && (
                    <div className="mt-4">
                        <div className="flex justify-between text-[10px] text-clinical-muted mb-1.5">
                            <span>Progress</span>
                            <span>{currentQuestion ? `${currentQuestion.question_number} / ${currentQuestion.total_questions}` : 'Complete'}</span>
                        </div>
                        <div className="h-2 bg-white/80 rounded-full overflow-hidden border border-clinical-border">
                            <div
                                className="h-full bg-primary rounded-full transition-all duration-500 ease-out"
                                style={{ width: `${progress}%` }}
                            />
                        </div>
                    </div>
                )}
            </Section>

            {/* ── Error ── */}
            {error && (
                <Section bg="white" padded>
                    <ErrorAlert message={error} onDismiss={() => setError(null)} />
                </Section>
            )}

            {/* ── Welcome / Start Screen ── */}
            {!currentQuestion && !results && !loading && (
                <Section bg="white">
                    <div className="max-w-lg mx-auto text-center py-12 space-y-6">
                        <div className="w-16 h-16 rounded-2xl bg-primary-50 flex items-center justify-center mx-auto">
                            <Shield size={28} className="text-primary" />
                        </div>
                        <div>
                            <h3 className="text-lg font-semibold text-clinical-text">
                                Cross-Cutting Symptom Assessment
                            </h3>
                            <p className="text-sm text-clinical-muted mt-2 leading-relaxed">
                                This standardized screening tool covers 13 psychiatric symptom domains.
                                Rate each item based on how much the described problem has troubled
                                the patient in the past <strong>2 weeks</strong>.
                            </p>
                        </div>
                        <div className="bg-amber-50 border border-amber-200 rounded-xl px-4 py-3 text-left">
                            <p className="text-xs text-amber-700 leading-relaxed">
                                <strong>Note:</strong> This is a screening measure only. Exceeding a domain threshold
                                suggests further clinical inquiry is warranted — it does not constitute a diagnosis.
                            </p>
                        </div>
                        <button
                            onClick={handleStart}
                            className="btn-primary px-8 py-3 rounded-xl inline-flex items-center gap-2 text-sm font-semibold shadow-float"
                            id="start-assessment"
                        >
                            Start Assessment
                            <ArrowRight size={16} />
                        </button>
                    </div>
                </Section>
            )}

            {/* ── Loading ── */}
            {loading && (
                <Section bg="white">
                    <div className="flex items-center justify-center py-20">
                        <div className="animate-spin w-8 h-8 border-2 border-primary border-t-transparent rounded-full" />
                    </div>
                </Section>
            )}

            {/* ── Active Question ── */}
            {currentQuestion && !results && (
                <Section bg="white">
                    <div className="max-w-xl mx-auto py-6 space-y-6">
                        {/* Domain badge */}
                        <div className="flex items-center gap-2">
                            <Brain size={14} className="text-primary" />
                            <span className="text-[10px] font-semibold text-primary uppercase tracking-wide">
                                {currentQuestion.domain_label}
                            </span>
                            <span className="text-[10px] text-clinical-muted">
                                — Question {currentQuestion.question_number} of {currentQuestion.total_questions}
                            </span>
                        </div>

                        {/* Question card */}
                        <div className="card-clinical p-6 bg-white animate-slide-up">
                            <p className="text-base font-medium text-clinical-text leading-relaxed">
                                During the past <strong>TWO (2) WEEKS</strong>, how much have you been
                                bothered by the following problem?
                            </p>
                            <p className="text-lg font-semibold text-clinical-text mt-4 leading-relaxed">
                                "{currentQuestion.text}"
                            </p>
                        </div>

                        {/* Response buttons */}
                        <div className="space-y-2">
                            {currentQuestion.response_options.map((opt) => (
                                <ResponseButton
                                    key={opt.value}
                                    option={opt}
                                    onSelect={handleAnswer}
                                    disabled={submitting}
                                />
                            ))}
                        </div>

                        {submitting && (
                            <div className="flex justify-center">
                                <div className="animate-spin w-5 h-5 border-2 border-primary border-t-transparent rounded-full" />
                            </div>
                        )}
                    </div>
                </Section>
            )}

            {/* ── Results ── */}
            {results && (
                <>
                    <Section bg="white">
                        <div className="max-w-2xl mx-auto space-y-6">
                            {/* Summary header */}
                            <div className="text-center space-y-2">
                                <CheckCircle2 size={32} className="text-emerald-500 mx-auto" />
                                <h3 className="text-lg font-semibold text-clinical-text">
                                    Assessment Complete
                                </h3>
                                <p className="text-sm text-clinical-muted">
                                    {results.total_answered} of {results.total_questions} questions answered
                                </p>
                            </div>

                            {/* Flagged domains summary */}
                            {results.flagged_domains.length > 0 ? (
                                <div className="bg-rose-50 border border-rose-200 rounded-xl px-4 py-3">
                                    <div className="flex items-center gap-2 mb-1.5">
                                        <AlertTriangle size={14} className="text-rose-500" />
                                        <span className="text-sm font-semibold text-rose-700">
                                            {results.flagged_domains.length} domain{results.flagged_domains.length !== 1 ? 's' : ''} exceeded threshold
                                        </span>
                                    </div>
                                    <p className="text-xs text-rose-600 leading-relaxed">
                                        Further clinical inquiry is recommended for flagged domains.
                                        This does not constitute a diagnosis.
                                    </p>
                                </div>
                            ) : (
                                <div className="bg-emerald-50 border border-emerald-200 rounded-xl px-4 py-3">
                                    <div className="flex items-center gap-2">
                                        <CheckCircle2 size={14} className="text-emerald-500" />
                                        <span className="text-sm font-semibold text-emerald-700">
                                            No domains exceeded threshold
                                        </span>
                                    </div>
                                </div>
                            )}
                        </div>
                    </Section>

                    <SectionDivider variant="fade" />

                    {/* Per-domain results */}
                    <Section bg="sage">
                        <div className="max-w-2xl mx-auto space-y-3">
                            <p className="text-[10px] font-semibold text-clinical-muted uppercase tracking-widest mb-2">
                                Domain Results
                            </p>
                            {results.domains.map((dr) => (
                                <DomainCard key={dr.domain} result={dr} />
                            ))}
                        </div>
                    </Section>
                </>
            )}
        </div>
    );
}
