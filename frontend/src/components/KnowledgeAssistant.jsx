import React, { useState, useEffect } from 'react';

export default function KnowledgeAssistant({
  isOpen,
  onClose,
  onOpenUpload,
  onStartChatWithDoc
}) {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [summaryData, setSummaryData] = useState(null);
  const [summarizingId, setSummarizingId] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    if (isOpen) {
      loadDocuments();
    }
  }, [isOpen]);

  const loadDocuments = async () => {
    setLoading(true);
    try {
      const res = await fetch('/documents');
      if (res.ok) {
        const data = await res.json();
        setDocuments(data);
      }
    } catch (e) {
      console.error("Failed to fetch documents:", e);
    } finally {
      setLoading(false);
    }
  };

  const handleSummarize = async (docId) => {
    setSummarizingId(docId);
    try {
      const res = await fetch(`/documents/${docId}/summarize`, { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        setSummaryData(data);
      }
    } catch (e) {
      console.error("Failed to summarize document:", e);
    } finally {
      setSummarizingId(null);
    }
  };

  const handleDelete = async (docId) => {
    if (!confirm("Are you sure you want to remove this document from the knowledge base?")) return;
    try {
      const res = await fetch(`/documents/${docId}`, { method: 'DELETE' });
      if (res.ok) {
        loadDocuments();
      }
    } catch (e) {
      console.error("Failed to delete document:", e);
    }
  };

  if (!isOpen) return null;

  const filteredDocs = documents.filter(d => 
    d.filename.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fade-in">
      <div className="w-full max-w-3xl rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-2xl p-6 text-slate-800 dark:text-slate-100 max-h-[90vh] flex flex-col">
        
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-slate-100 dark:border-slate-800">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center text-xl text-white shadow-md shadow-blue-500/20">
              📚
            </div>
            <div>
              <h2 className="text-base font-bold">Knowledge Assistant Mode</h2>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Interactive Study & Notes Hub • Direct Document Q&A & Summarization
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 p-1 rounded-md"
          >
            ✕
          </button>
        </div>

        {/* Action & Search Bar */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3 py-4 border-b border-slate-100 dark:border-slate-800 text-xs">
          <div className="relative w-full sm:w-72">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search uploaded notes..."
              className="w-full pl-8 pr-3 py-2 rounded-lg bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-800 dark:text-slate-200 focus:outline-none"
            />
            <span className="absolute left-2.5 top-2.5 text-slate-400">🔍</span>
          </div>

          <button
            onClick={() => {
              onOpenUpload();
              onClose();
            }}
            className="w-full sm:w-auto flex items-center justify-center space-x-2 px-3.5 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-medium transition-colors shadow-sm shadow-blue-500/20"
          >
            <span>+</span>
            <span>Upload New Document</span>
          </button>
        </div>

        {/* Document Cards List */}
        <div className="flex-1 overflow-y-auto py-4 space-y-3">
          {loading ? (
            <div className="py-12 text-center text-xs text-slate-400">
              <span className="animate-spin text-lg inline-block mb-2">⏳</span>
              <p>Loading your knowledge library...</p>
            </div>
          ) : filteredDocs.length === 0 ? (
            <div className="py-12 text-center text-xs text-slate-400 space-y-3">
              <div className="text-4xl">📄</div>
              <p className="font-medium text-slate-600 dark:text-slate-300">No documents in your knowledge base yet.</p>
              <p>Upload your college notes, PDFs, or assignments to ask direct questions with citations.</p>
              <button
                onClick={() => {
                  onOpenUpload();
                  onClose();
                }}
                className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-medium transition-colors"
              >
                Upload First Note
              </button>
            </div>
          ) : (
            filteredDocs.map((doc) => (
              <div
                key={doc.id}
                className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/30 hover:border-slate-300 dark:hover:border-slate-700 transition-all flex flex-col md:flex-row md:items-center justify-between gap-3 text-xs"
              >
                <div className="flex items-start space-x-3">
                  <div className="w-9 h-9 rounded-lg bg-blue-100 dark:bg-blue-950/60 text-blue-600 dark:text-blue-400 flex items-center justify-center font-bold text-sm">
                    {doc.file_type === '.pdf' ? 'PDF' : 'TXT'}
                  </div>
                  <div>
                    <h3 className="font-semibold text-slate-800 dark:text-slate-200 text-sm">
                      {doc.filename}
                    </h3>
                    <div className="flex flex-wrap items-center gap-2 mt-1 text-[11px] text-slate-500 dark:text-slate-400 font-mono">
                      <span>Pages: {doc.page_count}</span>
                      <span>•</span>
                      <span>Chunks: {doc.chunk_count}</span>
                      <span>•</span>
                      <span>Size: {(doc.file_size_bytes / 1024).toFixed(1)} KB</span>
                    </div>
                  </div>
                </div>

                {/* Actions for this document */}
                <div className="flex items-center space-x-2 pt-2 md:pt-0">
                  <button
                    onClick={() => handleSummarize(doc.id)}
                    disabled={summarizingId === doc.id}
                    className="px-3 py-1.5 rounded-lg bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700/60 font-medium transition-colors"
                  >
                    {summarizingId === doc.id ? 'Summarizing...' : '⚡ Summarize'}
                  </button>

                  <button
                    onClick={() => {
                      onStartChatWithDoc(doc);
                      onClose();
                    }}
                    className="px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-medium transition-colors shadow-sm shadow-blue-500/20"
                  >
                    💬 Ask Notes
                  </button>

                  <button
                    onClick={() => handleDelete(doc.id)}
                    className="p-1.5 text-slate-400 hover:text-red-500 transition-colors"
                    title="Delete document"
                  >
                    🗑️
                  </button>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Document Summary Modal Overlay */}
        {summaryData && (
          <div className="p-4 rounded-xl bg-blue-50 dark:bg-slate-800 border border-blue-200 dark:border-slate-700 mt-3 text-xs space-y-2 animate-fade-in">
            <div className="flex items-center justify-between font-bold text-slate-800 dark:text-slate-100">
              <span>📋 Extractive Summary: {summaryData.filename}</span>
              <button
                onClick={() => setSummaryData(null)}
                className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
              >
                ✕
              </button>
            </div>
            <p className="text-slate-700 dark:text-slate-300 leading-relaxed">
              {summaryData.summary}
            </p>
            {summaryData.key_points && summaryData.key_points.length > 0 && (
              <div className="pt-2 border-t border-blue-200/60 dark:border-slate-700 space-y-1">
                <span className="font-semibold text-blue-700 dark:text-blue-300">Key Takeaways:</span>
                <ul className="list-disc pl-4 space-y-0.5 text-slate-600 dark:text-slate-400">
                  {summaryData.key_points.map((kp, i) => (
                    <li key={i}>{kp}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {/* Footer */}
        <div className="pt-3 border-t border-slate-100 dark:border-slate-800 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg text-xs font-medium bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
