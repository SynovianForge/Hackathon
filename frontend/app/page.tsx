'use client';

import { useState, useEffect, useRef, useCallback, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { ShieldAlert, CheckCircle, XCircle, Clock, Loader2 } from 'lucide-react';

const BACKEND = process.env.NEXT_PUBLIC_BACKEND_API_URL || 'http://127.0.0.1:8000';
const TOTAL = 60;

function QuizContent() {
  const searchParams = useSearchParams();
  const quizId   = searchParams.get('quiz_id') || '';
  const commitSha = searchParams.get('commit') || '—';

  const [phase, setPhase]       = useState<'loading' | 'quiz' | 'success' | 'fail' | 'error'>('loading');
  const [question, setQuestion] = useState('');
  const [answer, setAnswer]     = useState('');
  const [timeLeft, setTimeLeft] = useState(TOTAL);
  const [explanation, setExplanation] = useState('');
  const [trustLevel, setTrustLevel]   = useState<number | null>(null);
  const [errorMsg, setErrorMsg]       = useState('');
  const [emptyWarn, setEmptyWarn]     = useState(false);

  // Refs for stale-closure safety in blur / timer handlers
  const submitted   = useRef(false);
  const quizActive  = useRef(false);
  const userIdRef   = useRef('anonymous');

  // ── Submit to backend ────────────────────────────────────────────────────────
  const doSubmit = useCallback((ans: string) => {
    if (submitted.current) return;
    submitted.current = true;
    quizActive.current = false;
    setPhase('loading');

    fetch(`${BACKEND}/api/submit-answer`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: userIdRef.current, quiz_id: quizId, user_answer: ans }),
    })
      .then(r => r.json())
      .then((d: { status: string; explanation: string; new_trust_level: number }) => {
        setExplanation(d.explanation || '');
        setTrustLevel(d.new_trust_level ?? null);
        setPhase(d.status === 'PASS' ? 'success' : 'fail');
      })
      .catch(() => {
        setExplanation('Server error during grading. Contact a senior engineer.');
        setPhase('fail');
      });
  }, [quizId]);

  // ── Load quiz ────────────────────────────────────────────────────────────────
  useEffect(() => {
    if (!quizId) {
      setErrorMsg('Invalid magic link — no quiz_id provided.');
      setPhase('error');
      return;
    }

    fetch(`${BACKEND}/api/quiz/${encodeURIComponent(quizId)}`)
      .then(r => r.ok ? r.json() : r.json().then((d: { detail?: string }) => { throw new Error(d.detail || String(r.status)); }))
      .then((d: { question: string; user_id: string; status: string }) => {
        if (d.status !== 'PENDING') {
          setErrorMsg(`This quiz has already been used (${d.status}). Magic links are one-time only.`);
          setPhase('error');
          return;
        }
        userIdRef.current = d.user_id;
        setQuestion(d.question);
        setPhase('quiz');
        quizActive.current = true;
      })
      .catch(err => {
        setErrorMsg(`Could not load quiz: ${(err as Error).message}`);
        setPhase('error');
      });
  }, [quizId]);

  // ── Timer ────────────────────────────────────────────────────────────────────
  useEffect(() => {
    if (phase !== 'quiz') return;
    if (timeLeft <= 0) { doSubmit(''); return; }
    const t = setTimeout(() => setTimeLeft(tl => tl - 1), 1000);
    return () => clearTimeout(t);
  }, [timeLeft, phase, doSubmit]);

  // ── Anti-cheat: focus loss = instant fail ────────────────────────────────────
  useEffect(() => {
    const onBlur = () => { if (quizActive.current) doSubmit(''); };
    const onHide = () => { if (document.hidden && quizActive.current) doSubmit(''); };
    window.addEventListener('blur', onBlur);
    document.addEventListener('visibilitychange', onHide);
    return () => {
      window.removeEventListener('blur', onBlur);
      document.removeEventListener('visibilitychange', onHide);
    };
  }, [doSubmit]);

  // ── Anti-cheat: no copy / paste / devtools ───────────────────────────────────
  useEffect(() => {
    const block = (e: Event) => e.preventDefault();
    const blockKeys = (e: KeyboardEvent) => {
      const bad = e.key === 'F12'
        || (e.ctrlKey  && e.shiftKey && ['I','J','C'].includes(e.key))
        || (e.metaKey  && e.shiftKey && ['I','J','C'].includes(e.key))
        || (e.ctrlKey  && e.key === 'u')
        || (e.metaKey  && e.key === 'u');
      if (bad) e.preventDefault();
    };
    document.addEventListener('copy',        block);
    document.addEventListener('cut',         block);
    document.addEventListener('paste',       block);
    document.addEventListener('contextmenu', block);
    document.addEventListener('dragover',    block);
    document.addEventListener('drop',        block);
    document.addEventListener('keydown',     blockKeys);
    return () => {
      document.removeEventListener('copy',        block);
      document.removeEventListener('cut',         block);
      document.removeEventListener('paste',       block);
      document.removeEventListener('contextmenu', block);
      document.removeEventListener('dragover',    block);
      document.removeEventListener('drop',        block);
      document.removeEventListener('keydown',     blockKeys);
    };
  }, []);

  const handleSubmit = () => {
    if (!answer.trim()) { setEmptyWarn(true); return; }
    setEmptyWarn(false);
    doSubmit(answer.trim());
  };

  const timerColor = timeLeft <= 10
    ? 'text-red-500 animate-pulse'
    : timeLeft <= 20
      ? 'text-yellow-400'
      : 'text-green-400';

  // ── SCREENS ──────────────────────────────────────────────────────────────────

  if (phase === 'loading') {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-black text-blue-500 font-mono tracking-widest uppercase">
        <Loader2 size={48} className="animate-spin mb-4" />
        <p>Initializing Interrogation Room...</p>
      </div>
    );
  }

  if (phase === 'error') {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-black text-red-500 p-4 font-mono">
        <XCircle size={64} className="mb-4 drop-shadow-[0_0_15px_rgba(239,68,68,0.8)]" />
        <h1 className="text-2xl font-bold mb-3 uppercase tracking-widest">Access Error</h1>
        <p className="text-sm text-red-400 text-center max-w-md bg-zinc-950 border border-red-900 px-6 py-4 rounded">{errorMsg}</p>
      </div>
    );
  }

  if (phase === 'success') {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-green-950 text-green-400 p-4 font-mono">
        <CheckCircle size={80} className="mb-4 drop-shadow-[0_0_20px_rgba(34,197,94,0.9)]" />
        <h1 className="text-4xl font-bold mb-2 uppercase tracking-widest">Verified</h1>
        <p className="text-lg mb-5">The Bouncer just unlocked your PR.</p>
        {explanation && (
          <p className="text-sm text-green-300 text-center max-w-lg mb-4 bg-black px-6 py-4 border border-green-800 leading-relaxed">
            {explanation}
          </p>
        )}
        {trustLevel !== null && (
          <p className="text-xs text-green-600 mb-4">New trust level: {trustLevel} / 100</p>
        )}
        <p className="text-xs bg-black px-4 py-2 border border-green-900 text-green-600">
          Commit: {commitSha}
        </p>
      </div>
    );
  }

  if (phase === 'fail') {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-red-950 text-red-400 p-4 font-mono">
        <XCircle size={80} className="mb-4 drop-shadow-[0_0_20px_rgba(239,68,68,0.9)]" />
        <h1 className="text-4xl font-bold mb-2 uppercase tracking-widest">Access Denied</h1>
        <p className="text-lg mb-5">You failed the check or time ran out.</p>
        {explanation && (
          <p className="text-sm text-red-300 text-center max-w-lg mb-4 bg-black px-6 py-4 border border-red-900 leading-relaxed">
            {explanation}
          </p>
        )}
        {trustLevel !== null && (
          <p className="text-xs text-red-700 mb-4">New trust level: {trustLevel} / 100</p>
        )}
        <p className="text-xs text-red-800 mt-2">
          PR remains blocked — reply @Copypasta-Hunter appeal for manual review.
        </p>
      </div>
    );
  }

  // ── Quiz screen ───────────────────────────────────────────────────────────────
  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-black text-gray-200 p-4 font-mono">
      <div className="border border-red-800 bg-zinc-950 p-8 max-w-2xl w-full shadow-[0_0_25px_rgba(153,27,27,0.4)]">

        {/* Header */}
        <div className="flex justify-between items-center mb-6 border-b border-zinc-800 pb-4">
          <div className="flex items-center gap-2 text-red-500">
            <ShieldAlert size={28} />
            <h1 className="text-xl font-bold uppercase tracking-widest">Gatekeeper Check</h1>
          </div>
          <div className={`flex items-center gap-2 ${timerColor}`}>
            <Clock size={20} />
            <span className="text-2xl font-bold tabular-nums">{timeLeft}s</span>
          </div>
        </div>

        {/* Commit SHA */}
        <div className="mb-5">
          <p className="text-xs text-zinc-500 mb-2 uppercase tracking-wide">Target Commit SHA:</p>
          <p className="bg-black p-3 text-green-500 text-sm break-all border border-zinc-800">{commitSha}</p>
        </div>

        {/* Question */}
        <div className="mb-5">
          <p className="text-xs text-zinc-500 mb-2 uppercase tracking-wide">Question:</p>
          <p className="bg-black p-4 text-blue-300 text-sm border border-zinc-800 leading-relaxed">{question}</p>
        </div>

        {/* Answer */}
        <div className="mb-2">
          <p className="text-xs text-zinc-500 mb-2 uppercase tracking-wide">Your Answer:</p>
          <textarea
            value={answer}
            onChange={e => { setAnswer(e.target.value); setEmptyWarn(false); }}
            placeholder="Type your answer here..."
            rows={4}
            className="w-full bg-black border border-zinc-700 focus:border-blue-600 text-gray-200 text-sm p-3 resize-none outline-none placeholder-zinc-600 transition-colors"
            style={{ userSelect: 'text', WebkitUserSelect: 'text' }}
            autoComplete="off"
            spellCheck={false}
          />
          {emptyWarn && (
            <p className="text-yellow-500 text-xs mt-1">Please write an answer before submitting.</p>
          )}
          <p className="text-xs text-zinc-700 mt-1">
            Copy-paste disabled. Switching windows auto-fails the quiz.
          </p>
        </div>

        {/* Buttons */}
        <div className="flex gap-3 mt-6">
          <button
            onClick={handleSubmit}
            className="flex-1 bg-blue-950 hover:bg-blue-900 border border-blue-700 text-blue-300 font-bold uppercase tracking-widest py-3 transition-colors"
          >
            Submit Answer
          </button>
          <button
            onClick={() => doSubmit('')}
            className="bg-zinc-900 hover:bg-zinc-800 border border-zinc-700 text-zinc-500 font-bold uppercase tracking-widest px-6 py-3 transition-colors"
          >
            Skip
          </button>
        </div>
      </div>
    </div>
  );
}

export default function InterrogationRoom() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-black flex justify-center items-center text-red-500 font-mono tracking-widest uppercase">
        Initializing...
      </div>
    }>
      <QuizContent />
    </Suspense>
  );
}
