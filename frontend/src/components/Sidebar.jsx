import React from 'react';

export default function Sidebar({
  conversations,
  activeId,
  onSelectChat,
  onNewChat,
  onDeleteChat,
  onClearHistory,
  onOpenKnowledge,
  onOpenSettings,
  onOpenTodos,
  documentsCount,
  todosCount,
  isDarkMode,
  onToggleTheme,
  isOpen,
  onCloseMobile,
  currentUser,
  onLogout
}) {
  return (
    <>
      {/* Mobile Backdrop */}
      {isOpen && (
        <div 
          onClick={onCloseMobile}
          className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-30 md:hidden transition-opacity"
        />
      )}

      {/* Sidebar Container */}
      <aside className={`
        fixed md:static inset-y-0 left-0 z-40
        w-72 bg-slate-900 text-slate-200 flex flex-col h-full
        border-r border-slate-800 transition-transform duration-300 ease-in-out
        ${isOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}
      `}>
        {/* Brand Header */}
        <div className="p-4 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center text-white font-bold shadow-md shadow-blue-500/20">
              ⚡
            </div>
            <div>
              <h1 className="font-semibold text-sm text-white tracking-wide">Virtual Assistant</h1>
              <p className="text-[11px] text-slate-400">LLM • RAG • Productivity</p>
            </div>
          </div>
          <button 
            onClick={onCloseMobile}
            className="md:hidden text-slate-400 hover:text-white p-1 rounded-md"
            title="Close menu"
          >
            ✕
          </button>
        </div>

        {/* Action: New Chat */}
        <div className="p-3">
          <button
            onClick={() => {
              onNewChat();
              if (onCloseMobile) onCloseMobile();
            }}
            className="w-full flex items-center justify-center space-x-2 px-4 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-500 active:bg-blue-700 text-white font-medium text-sm transition-colors shadow-sm shadow-blue-600/30"
          >
            <span>+</span>
            <span>New Conversation</span>
          </button>
        </div>

        {/* Special Modes & Tools */}
        <div className="px-3 py-1 space-y-1">
          <button
            onClick={onOpenKnowledge}
            className="w-full flex items-center justify-between px-3 py-2 rounded-lg text-xs font-medium text-slate-300 hover:bg-slate-800/80 hover:text-white transition-colors"
          >
            <div className="flex items-center space-x-2">
              <span className="text-sm">📚</span>
              <span>Knowledge Mode (Documents)</span>
            </div>
            <span className="px-1.5 py-0.5 rounded-full bg-blue-500/20 text-blue-300 text-[10px] font-mono">
              {documentsCount} docs
            </span>
          </button>

          <button
            onClick={onOpenTodos}
            className="w-full flex items-center justify-between px-3 py-2 rounded-lg text-xs font-medium text-slate-300 hover:bg-slate-800/80 hover:text-white transition-colors"
          >
            <div className="flex items-center space-x-2">
              <span className="text-sm">📝</span>
              <span>To-Do List</span>
            </div>
            <span className="px-1.5 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 text-[10px] font-mono">
              {todosCount} tasks
            </span>
          </button>
        </div>

        {/* Previous Conversations Section */}
        <div className="px-3 pt-3 pb-1">
          <h2 className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider px-2">
            Recent Chats
          </h2>
        </div>

        <div className="flex-1 overflow-y-auto px-2 space-y-1">
          {conversations.length === 0 ? (
            <div className="text-center py-8 text-xs text-slate-400">
              No conversations yet.<br />Start one above!
            </div>
          ) : (
            conversations.map((conv) => {
              const isActive = conv.id === activeId;
              return (
                <div
                  key={conv.id}
                  onClick={() => {
                    onSelectChat(conv.id);
                    if (onCloseMobile) onCloseMobile();
                  }}
                  className={`
                    group flex items-center justify-between px-3 py-2 rounded-lg cursor-pointer text-xs transition-colors
                    ${isActive ? 'bg-slate-800 text-white font-medium border-l-2 border-blue-500' : 'text-slate-300 hover:bg-slate-800/50 hover:text-slate-100'}
                  `}
                >
                  <div className="flex items-center space-x-2 truncate">
                    <span className="text-slate-400 text-xs">💬</span>
                    <span className="truncate">{conv.title || "Untitled Conversation"}</span>
                  </div>

                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onDeleteChat(conv.id);
                    }}
                    className="opacity-0 group-hover:opacity-100 text-slate-400 hover:text-red-400 p-1 rounded transition-opacity"
                    title="Delete conversation"
                  >
                    🗑️
                  </button>
                </div>
              );
            })
          )}
        </div>

        {/* Footer Actions */}
        <div className="p-3 border-t border-slate-800 space-y-2 bg-slate-900/80">
          
          {/* User Profile Card */}
          {currentUser && (
            <div className="flex items-center justify-between p-2 rounded-xl bg-slate-800/60 border border-slate-700/60 text-xs">
              <div className="flex items-center space-x-2.5 truncate">
                <div className="w-7 h-7 rounded-full bg-blue-600 text-white font-bold flex items-center justify-center text-xs shadow-sm">
                  {currentUser.full_name ? currentUser.full_name[0].toUpperCase() : 'U'}
                </div>
                <div className="truncate">
                  <p className="font-semibold text-slate-200 truncate leading-none">
                    {currentUser.full_name || currentUser.username}
                  </p>
                  <p className="text-[10px] text-slate-400 truncate mt-0.5">
                    @{currentUser.username}
                  </p>
                </div>
              </div>
              <button
                onClick={onLogout}
                className="text-slate-400 hover:text-red-400 p-1 rounded transition-colors"
                title="Log Out"
              >
                🚪
              </button>
            </div>
          )}

          {conversations.length > 0 && (
            <button
              onClick={onClearHistory}
              className="w-full flex items-center space-x-2 px-3 py-1.5 rounded-md text-xs text-red-400 hover:bg-red-500/10 transition-colors"
            >
              <span>🗑️</span>
              <span>Clear All History</span>
            </button>
          )}

          <div className="flex items-center justify-between pt-1">
            <button
              onClick={onOpenSettings}
              className="flex items-center space-x-2 px-2.5 py-1.5 rounded-md text-xs text-slate-300 hover:bg-slate-800 hover:text-white transition-colors"
            >
              <span>⚙️</span>
              <span>Settings</span>
            </button>

            <button
              onClick={onToggleTheme}
              className="p-1.5 rounded-md text-xs text-slate-300 hover:bg-slate-800 hover:text-white transition-colors"
              title="Toggle Dark/Light Mode"
            >
              {isDarkMode ? '☀️ Light' : '🌙 Dark'}
            </button>
          </div>
        </div>
      </aside>
    </>
  );
}
