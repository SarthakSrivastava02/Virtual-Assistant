import React, { useRef, useEffect } from 'react';
import MessageBubble from './MessageBubble';
import ChatInput from './ChatInput';
import WelcomeScreen from './WelcomeScreen';

export default function ChatWindow({
  conversation,
  messages,
  isLoading,
  onSendMessage,
  onOpenUpload,
  useRag,
  onToggleRag,
  strictRag,
  onToggleStrictRag,
  onToggleMobileSidebar,
  focusedDoc,
  onClearFocusDoc,
  systemStatus,
  currentUser
}) {
  const messagesEndRef = useRef(null);

  // Auto-scroll on new message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  return (
    <div className="flex-1 flex flex-col h-full bg-slate-50 dark:bg-slate-950 overflow-hidden relative">
      
      {/* Header Bar */}
      <header className="h-14 border-b border-slate-200/80 dark:border-slate-800 bg-white/70 dark:bg-slate-900/70 backdrop-blur-md px-4 flex items-center justify-between z-10">
        
        {/* Left: Mobile Toggle & Title */}
        <div className="flex items-center space-x-3">
          <button
            onClick={onToggleMobileSidebar}
            className="md:hidden p-1.5 rounded-lg text-slate-500 hover:text-slate-800 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
            title="Toggle Menu"
          >
            ☰
          </button>
          
          <div>
            <h2 className="text-sm font-semibold text-slate-900 dark:text-slate-100 truncate max-w-[200px] sm:max-w-md">
              {conversation?.title || "New Conversation"}
            </h2>
            <div className="flex items-center space-x-2 text-[10px] text-slate-500 dark:text-slate-400">
              <span className="flex items-center space-x-1">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                <span>{systemStatus?.llm_provider || 'AI Assistant'}</span>
              </span>
              <span>•</span>
              <span>FAISS RAG: {useRag ? 'Active' : 'Disabled'}</span>
            </div>
          </div>
        </div>

        {/* Right: Focused Document Badge & Status */}
        <div className="flex items-center space-x-2">
          {focusedDoc && (
            <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-full bg-indigo-50 dark:bg-indigo-950/60 border border-indigo-200 dark:border-indigo-800 text-indigo-700 dark:text-indigo-300 text-xs font-medium">
              <span>📄 {focusedDoc.filename}</span>
              <button
                onClick={onClearFocusDoc}
                className="hover:text-red-500 font-bold ml-1"
                title="Clear document focus"
              >
                ✕
              </button>
            </div>
          )}

          <div className="hidden sm:flex items-center space-x-1 px-2.5 py-1 rounded-full bg-slate-100 dark:bg-slate-800 text-[11px] text-slate-600 dark:text-slate-400 font-mono">
            <span>{messages.length} turns</span>
          </div>
        </div>
      </header>

      {/* Main Messages Container */}
      <main className="flex-1 overflow-y-auto px-4 md:px-8 py-4 space-y-2">
        {messages.length === 0 ? (
          <WelcomeScreen
            onSelectPrompt={onSendMessage}
            onOpenUpload={onOpenUpload}
            currentUser={currentUser}
          />
        ) : (
          <div className="max-w-4xl mx-auto space-y-4">
            {messages.map((msg, index) => (
              <MessageBubble key={msg.id || index} message={msg} />
            ))}

            {/* Typing / Reasoning Loading Animation */}
            {isLoading && (
              <div className="flex items-center space-x-3 py-3 animate-fade-in">
                <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-indigo-600 to-purple-600 text-white flex items-center justify-center text-xs font-semibold shadow-md shadow-indigo-500/20">
                  ⚡
                </div>
                <div className="flex items-center space-x-2 px-4 py-2.5 rounded-2xl rounded-tl-none bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 shadow-sm text-xs text-slate-500 dark:text-slate-400">
                  <div className="flex space-x-1">
                    <div className="w-1.5 h-1.5 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                    <div className="w-1.5 h-1.5 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                    <div className="w-1.5 h-1.5 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                  </div>
                  <span>Thinking and retrieving context...</span>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        )}
      </main>

      {/* Sticky Bottom Input Bar */}
      <footer className="w-full bg-gradient-to-t from-slate-50 dark:from-slate-950 via-slate-50/80 dark:via-slate-950/80 to-transparent pt-3">
        <ChatInput
          onSendMessage={onSendMessage}
          onOpenUpload={onOpenUpload}
          useRag={useRag}
          onToggleRag={onToggleRag}
          strictRag={strictRag}
          onToggleStrictRag={onToggleStrictRag}
          isLoading={isLoading}
        />
      </footer>
    </div>
  );
}
