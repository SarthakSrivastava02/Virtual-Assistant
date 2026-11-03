import React from 'react';

export default function WelcomeScreen({ onSelectPrompt, onOpenUpload, currentUser }) {
  const examplePrompts = [
    {
      category: "📚 RAG & Documents",
      icon: "📄",
      title: "Query Knowledge Base",
      prompt: "What operations do semaphores provide according to the notes?",
      desc: "Searches uploaded PDF/TXT files with exact citations"
    },
    {
      category: "🧮 Safe Math Tool",
      icon: "🔢",
      title: "Evaluate Calculations",
      prompt: "calculate sqrt(144) * 5 + 10",
      desc: "Safe AST-evaluated mathematical expressions"
    },
    {
      category: "💻 System Architecture",
      icon: "⚡",
      title: "Operating Systems",
      prompt: "Explain what is a deadlock in Operating Systems and list Coffman conditions.",
      desc: "Comprehensive technical concepts and explanations"
    },
    {
      category: "📝 Task Management",
      icon: "✅",
      title: "To-Do List Tools",
      prompt: "add study computer networks to my todos",
      desc: "Automated persistent task planning and tracking"
    }
  ];

  return (
    <div className="flex-1 flex flex-col items-center justify-center p-6 text-center max-w-3xl mx-auto animate-fade-in">
      
      {/* Hero Badge & Icon */}
      <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-blue-600 via-indigo-600 to-purple-600 flex items-center justify-center text-3xl text-white shadow-xl shadow-blue-500/25 mb-5 ring-4 ring-blue-500/10">
        ⚡
      </div>

      <h1 className="text-2xl md:text-3xl font-bold text-slate-900 dark:text-white tracking-tight">
        {currentUser?.full_name ? `Welcome, ${currentUser.full_name}` : "AI Virtual Assistant"}
      </h1>
      
      <p className="mt-2 text-sm text-slate-600 dark:text-slate-400 max-w-lg leading-relaxed">
        Conversational computing powered by Large Language Models, FAISS vector search, and automated task execution.
      </p>

      {/* Upload Callout Pill */}
      <div className="mt-5">
        <button
          onClick={onOpenUpload}
          className="inline-flex items-center space-x-2 px-4 py-2 rounded-full bg-blue-50 dark:bg-blue-950/50 border border-blue-200 dark:border-blue-800 text-blue-700 dark:text-blue-300 text-xs font-medium hover:bg-blue-100 dark:hover:bg-blue-900/50 transition-colors shadow-sm"
        >
          <span>📎</span>
          <span>Upload Documents / PDF to start Knowledge Mode</span>
          <span className="font-bold">→</span>
        </button>
      </div>

      {/* Suggestion Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mt-8 w-full">
        {examplePrompts.map((item, idx) => (
          <div
            key={idx}
            onClick={() => onSelectPrompt(item.prompt)}
            className="p-3.5 rounded-xl border border-slate-200/90 dark:border-slate-800 bg-white/80 dark:bg-slate-900/80 hover:border-blue-500/60 dark:hover:border-blue-500/60 hover:shadow-md text-left cursor-pointer transition-all group"
          >
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-semibold text-blue-600 dark:text-blue-400">
                {item.category}
              </span>
              <span className="text-base group-hover:scale-110 transition-transform">
                {item.icon}
              </span>
            </div>
            <h3 className="font-semibold text-xs text-slate-800 dark:text-slate-200 mt-1.5">
              {item.title}
            </h3>
            <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-1 line-clamp-1">
              {item.desc}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
