import React, { useState } from 'react';

export default function MessageBubble({ message }) {
  const isUser = message.role === 'user';
  const [sourcesOpen, setSourcesOpen] = useState(false);
  const [copiedCode, setCopiedCode] = useState(false);

  const handleCopy = (text) => {
    navigator.clipboard.writeText(text);
    setCopiedCode(true);
    setTimeout(() => setCopiedCode(false), 2000);
  };

  // Basic markdown-like rendering for standard text elements
  const renderFormattedContent = (content) => {
    if (!content) return null;

    // Detect fenced code blocks
    const parts = content.split(/(```[\s\S]*?```)/g);

    return parts.map((part, index) => {
      if (part.startsWith('```') && part.endsWith('```')) {
        const lines = part.slice(3, -3).trim().split('\n');
        const lang = lines[0].match(/^[a-zA-Z0-9_-]+$/) ? lines[0] : '';
        const code = lang ? lines.slice(1).join('\n') : lines.join('\n');

        return (
          <div key={index} className="my-2.5 rounded-lg overflow-hidden bg-slate-900 border border-slate-700/60 text-slate-100 text-xs">
            <div className="flex items-center justify-between px-3 py-1.5 bg-slate-800/80 border-b border-slate-700/60 text-[11px] text-slate-400 font-mono">
              <span>{lang || 'code'}</span>
              <button
                onClick={() => handleCopy(code)}
                className="hover:text-white transition-colors"
              >
                {copiedCode ? '✓ Copied' : 'Copy'}
              </button>
            </div>
            <pre className="p-3 overflow-x-auto font-mono text-[12px] leading-relaxed">
              <code>{code}</code>
            </pre>
          </div>
        );
      }

      // Render regular paragraphs, headings, bold, bullet points
      const lines = part.split('\n');
      return (
        <div key={index} className="space-y-1.5 leading-relaxed">
          {lines.map((line, lIdx) => {
            const trimmed = line.trim();
            if (!trimmed) return <div key={lIdx} className="h-2" />;

            // Headings
            if (trimmed.startsWith('### ')) {
              return <h3 key={lIdx} className="text-sm font-bold text-slate-900 dark:text-slate-100 mt-2">{trimmed.slice(4)}</h3>;
            }
            if (trimmed.startsWith('## ')) {
              return <h2 key={lIdx} className="text-base font-bold text-slate-900 dark:text-slate-100 mt-2.5">{trimmed.slice(3)}</h2>;
            }
            if (trimmed.startsWith('# ')) {
              return <h1 key={lIdx} className="text-lg font-bold text-slate-900 dark:text-slate-100 mt-3">{trimmed.slice(2)}</h1>;
            }

            // Bullet points
            if (trimmed.startsWith('- ') || trimmed.startsWith('* ') || trimmed.startsWith('• ')) {
              return (
                <div key={lIdx} className="flex items-start space-x-2 pl-2">
                  <span className="text-blue-500 font-bold">•</span>
                  <span>{formatInlineText(trimmed.slice(2))}</span>
                </div>
              );
            }

            // Standard line
            return <p key={lIdx}>{formatInlineText(line)}</p>;
          })}
        </div>
      );
    });
  };

  // Helper for inline **bold** and `code`
  const formatInlineText = (text) => {
    const tokens = text.split(/(\*\*.*?\*\*|`.*?`)/g);
    return tokens.map((token, i) => {
      if (token.startsWith('**') && token.endsWith('**')) {
        return <strong key={i} className="font-semibold">{token.slice(2, -2)}</strong>;
      }
      if (token.startsWith('`') && token.endsWith('`')) {
        return (
          <code key={i} className="px-1.5 py-0.5 rounded bg-slate-200 dark:bg-slate-800 text-slate-800 dark:text-slate-200 font-mono text-xs">
            {token.slice(1, -1)}
          </code>
        );
      }
      return token;
    });
  };

  return (
    <div className={`flex w-full py-2.5 ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`flex max-w-[85%] md:max-w-[78%] space-x-3 ${isUser ? 'flex-row-reverse space-x-reverse' : 'flex-row'}`}>
        
        {/* Avatar */}
        <div className={`
          w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center text-xs font-semibold shadow-sm
          ${isUser 
            ? 'bg-blue-600 text-white' 
            : 'bg-gradient-to-tr from-indigo-600 to-purple-600 text-white shadow-indigo-500/20'}
        `}>
          {isUser ? '👤' : '⚡'}
        </div>

        {/* Message Bubble Content */}
        <div className={`
          flex flex-col rounded-2xl px-4 py-3 text-sm shadow-sm transition-all
          ${isUser
            ? 'bg-blue-600 text-white rounded-tr-none'
            : 'bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 text-slate-800 dark:text-slate-200 rounded-tl-none'}
        `}>
          {/* Header metadata */}
          <div className="flex items-center justify-between pb-1.5 text-[11px] opacity-70">
            <span className="font-medium">{isUser ? 'You' : 'Virtual Assistant'}</span>
            {message.created_at && (
              <span className="font-mono text-[10px]">
                {new Date(message.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </span>
            )}
          </div>

          {/* Text Content */}
          <div className="prose-academic">
            {renderFormattedContent(message.content)}
          </div>

          {/* Source Citations from RAG */}
          {message.sources && message.sources.length > 0 && (
            <div className="mt-3 pt-2.5 border-t border-slate-200 dark:border-slate-800">
              <button
                onClick={() => setSourcesOpen(!sourcesOpen)}
                className="flex items-center space-x-1.5 text-[11px] font-semibold text-blue-600 dark:text-blue-400 hover:underline"
              >
                <span>📚</span>
                <span>{message.sources.length} Referenced Source(s)</span>
                <span className="text-[10px]">{sourcesOpen ? '▲ Hide' : '▼ View'}</span>
              </button>

              {sourcesOpen && (
                <div className="mt-2 space-y-2">
                  {message.sources.map((src, sIdx) => (
                    <div 
                      key={sIdx}
                      className="p-2.5 rounded-lg bg-slate-50 dark:bg-slate-800/60 border border-slate-200/80 dark:border-slate-700/60 text-xs"
                    >
                      <div className="flex items-center justify-between text-[11px] font-medium text-slate-700 dark:text-slate-300">
                        <span className="font-semibold text-blue-600 dark:text-blue-400">
                          📄 {src.document_name}
                        </span>
                        <span className="text-slate-400 text-[10px]">
                          Page {src.page_number || 1} • {(src.relevance_score * 100).toFixed(0)}% match
                        </span>
                      </div>
                      <p className="mt-1 text-slate-600 dark:text-slate-400 italic text-[11px] bg-white dark:bg-slate-900/60 p-1.5 rounded border border-slate-100 dark:border-slate-800">
                        "{src.snippet}"
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
