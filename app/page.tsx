'use client';

import { useState, useEffect, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { ShieldAlert, CheckCircle, XCircle, Clock, Loader2 } from 'lucide-react';

interface QuizData {
  question: string;
  codeSnippet: string;
  options: string[];
}

function QuizContent() {
  const searchParams = useSearchParams();
  const commitSha = searchParams.get('commit') || 'Mock-Commit-12345';

  const [status, setStatus] = useState('loading'); 
  const [timeLeft, setTimeLeft] = useState(60);
  const [quiz, setQuiz] = useState<QuizData | null>(null);

  // Fake Backend Call for fetching Quiz
  useEffect(() => {
    const fetchFakeQuiz = () => {
      setTimeout(() => {
        setQuiz({
          question: "Identify the vulnerability in this PR code:",
          codeSnippet: `function authenticateUser(req) {\n  const user = db.query("SELECT * FROM users WHERE id = " + req.body.id);\n  return user;\n}`,
          options: [
            "Cross-Site Scripting (XSS)",
            "SQL Injection (SQLi)",
            "Insecure Direct Object Reference (IDOR)",
            "No vulnerability present"
          ]
        });
        setStatus('quiz');
      }, 1500); // ১.৫ সেকেন্ডের ফেক লোডিং
    };

    fetchFakeQuiz();
  }, []);

  // Timer Logic
  useEffect(() => {
    if (status === 'quiz' && timeLeft > 0) {
      const timer = setTimeout(() => setTimeLeft(timeLeft - 1), 1000);
      return () => clearTimeout(timer);
    } else if (status === 'quiz' && timeLeft === 0) {
      setStatus('fail');
    }
  }, [timeLeft, status]);

  // Fake Submit Call
  const handleAnswer = (selectedOption: string) => {
    setStatus('loading'); 

    // ফেক সাবমিশন লজিক (SQLi সিলেক্ট করলে পাস, বাকিগুলোতে ফেইল)
    setTimeout(() => {
      if (selectedOption === "SQL Injection (SQLi)") {
        setStatus('success');
      } else {
        setStatus('fail');
      }
    }, 1000); // ১ সেকেন্ডের ফেক চেকিং
  };

  if (status === 'loading') {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-black text-blue-500 font-mono tracking-widest uppercase">
        <Loader2 size={48} className="animate-spin mb-4" />
        <p>Mocking Backend... Loading UI...</p>
      </div>
    );
  }

  if (status === 'success') {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-green-950 text-green-400 p-4 font-mono">
        <CheckCircle size={80} className="mb-4 text-green-500 shadow-green-500 drop-shadow-[0_0_15px_rgba(34,197,94,0.8)]" />
        <h1 className="text-4xl font-bold mb-2">✅ VERIFIED</h1>
        <p className="text-xl">The Bouncer just unlocked your PR.</p>
        <p className="mt-4 text-sm bg-black px-4 py-2 rounded border border-green-800 text-green-300">Commit: {commitSha}</p>
      </div>
    );
  }

  if (status === 'fail') {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-red-950 text-red-500 p-4 font-mono">
        <XCircle size={80} className="mb-4 shadow-red-500 drop-shadow-[0_0_15px_rgba(239,68,68,0.8)]" />
        <h1 className="text-4xl font-bold mb-2 uppercase">🛑 Access Denied</h1>
        <p className="text-xl">You failed the check or time ran out.</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-black text-gray-200 p-4 font-mono">
      <div className="border border-red-800 bg-zinc-950 p-8 max-w-2xl w-full shadow-[0_0_25px_rgba(153,27,27,0.4)]">
        <div className="flex justify-between items-center mb-6 border-b border-zinc-800 pb-4">
          <div className="flex items-center gap-2 text-red-500">
            <ShieldAlert size={28} />
            <h1 className="text-xl font-bold uppercase tracking-widest">Gatekeeper Check</h1>
          </div>
          <div className="flex items-center gap-2 text-yellow-500">
            <Clock size={20} />
            <span className="text-2xl font-bold">{timeLeft}s</span>
          </div>
        </div>

        <div className="mb-6">
          <p className="text-sm text-gray-400 mb-2 uppercase tracking-wide">Target Commit SHA:</p>
          <p className="bg-black p-3 text-green-500 text-sm break-all border border-zinc-800">{commitSha}</p>
        </div>

        <div className="mb-6">
          <p className="text-sm text-gray-400 mb-2 uppercase tracking-wide">{quiz?.question}</p>
          <pre className="bg-black p-4 text-sm text-blue-400 border border-zinc-800 overflow-x-auto">
            <code>{quiz?.codeSnippet}</code>
          </pre>
        </div>

        <div className="space-y-3 mt-8">
          {quiz?.options?.map((option, index) => (
            <button 
              key={index}
              onClick={() => handleAnswer(option)} 
              className="w-full text-left p-4 border border-zinc-800 hover:border-blue-500 hover:bg-blue-950 hover:text-blue-400 transition-all"
            >
              [{String.fromCharCode(65 + index)}] {option}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

export default function InterrogationRoom() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-black flex justify-center items-center text-red-500 font-mono tracking-widest uppercase">Initializing...</div>}>
      <QuizContent />
    </Suspense>
  );
}