import React, { useState, useRef, useEffect } from 'react';

export default function ChatInput({
  onSendMessage,
  onOpenUpload,
  useRag,
  onToggleRag,
  strictRag,
  onToggleStrictRag,
  isLoading
}) {
  const [input, setInput] = useState('');
  const textareaRef = useRef(null);

  // Auto-resize textarea height
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 140)}px`;
    }
  }, [input]);

  const handleSubmit = (e) => {
    if (e) e.preventDefault();
    if (!input.trim() || isLoading) return;
    onSendMessage(input.trim());
    setInput('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="w-full max-w-4xl mx-auto px-4 pb-4">
      {/* Input Outer Card */}
      <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-lg shadow-slate-200/50 dark:shadow-none p-2.5 transition-all focus-within:border-blue-500 focus-within:ring-2 focus-within:ring-blue-500/20">
        
        {/* Textarea */}
        <textarea
          ref={textareaRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask a question, request a calculation, or query uploaded notes..."
          rows={1}
          disabled={isLoading}
          className="w-full resize-none bg-transparent px-2.5 py-1.5 text-sm text-slate-800 dark:text-slate-100 placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none leading-relaxed max-h-36"
        />

        {/* Toolbar Footer */}
        <div className="flex items-center justify-between pt-2 px-1 border-t border-slate-100 dark:border-slate-800/80">
          
          {/* Left Controls: Upload & RAG toggles */}
          <div className="flex items-center space-x-2">
            <button
              type="button"
              onClick={onOpenUpload}
              className="flex items-center space-x-1 px-2.5 py-1.5 rounded-lg text-xs font-medium text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
              title="Upload PDF or TXT Document"
            >
              <span>📎</span>
              <span className="hidden sm:inline">Upload Notes</span>
            </button>

            {/* RAG Toggle */}
            <button
              type="button"
              onClick={onToggleRag}
              className={`flex items-center space-x-1 px-2.5 py-1 rounded-full text-[11px] font-medium transition-colors ${
                useRag
                  ? 'bg-blue-500/15 text-blue-600 dark:text-blue-400 border border-blue-500/30'
                  : 'bg-slate-100 dark:bg-slate-800 text-slate-400 border border-transparent'
              }`}
              title="Toggle Knowledge Retrieval from uploaded documents"
            >
              <span>{useRag ? '🧠 RAG: On' : '🧠 RAG: Off'}</span>
            </button>

            {/* Strict RAG Toggle (visible only if RAG enabled) */}
            {useRag && (
              <button
                type="button"
                onClick={onToggleStrictRag}
                className={`hidden md:flex items-center space-x-1 px-2 py-1 rounded-full text-[11px] font-medium transition-colors ${
                  strictRag
                    ? 'bg-purple-500/15 text-purple-600 dark:text-purple-400 border border-purple-500/30'
                    : 'bg-slate-100 dark:bg-slate-800 text-slate-400 border border-transparent'
                }`}
                title="Strict Mode: Only answer from uploaded notes"
              >
                <span>🎯 Strict Notes</span>
              </button>
            )}
          </div>

          {/* Right Controls: Send Button */}
          <button
            type="button"
            onClick={handleSubmit}
            disabled={!input.trim() || isLoading}
            className={`
              flex items-center justify-center w-8 h-8 rounded-xl font-bold text-sm transition-all
              ${!input.trim() || isLoading
                ? 'bg-slate-200 dark:bg-slate-800 text-slate-400 cursor-not-allowed'
                : 'bg-blue-600 hover:bg-blue-500 text-white shadow-md shadow-blue-500/20 active:scale-95'}
            `}
            title="Send message (Enter)"
          >
            {isLoading ? (
              <span className="animate-spin text-xs">⏳</span>
            ) : (
              <span>↑</span>
            )}
          </button>
        </div>
      </div>

      <div className="flex items-center justify-center space-x-2 text-[11px] text-slate-400 mt-2">
        <span>Enter to send • Shift+Enter for newline</span>
      </div>
    </div>
  );
}
