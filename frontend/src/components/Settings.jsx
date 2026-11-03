import React, { useState, useEffect } from 'react';

export default function Settings({ isOpen, onClose, onSettingsUpdated }) {
  const [geminiKey, setGeminiKey] = useState('');
  const [geminiModel, setGeminiModel] = useState('gemini-1.5-flash');
  const [apiKey, setApiKey] = useState('');
  const [showKey, setShowKey] = useState(false);
  const [model, setModel] = useState('gpt-4o-mini');
  const [provider, setProvider] = useState('auto');
  const [localUrl, setLocalUrl] = useState('http://localhost:11434');
  const [localModel, setLocalModel] = useState('llama3');
  const [topK, setTopK] = useState(4);
  const [saving, setSaving] = useState(false);
  const [successMsg, setSuccessMsg] = useState('');
  const [healthInfo, setHealthInfo] = useState(null);

  useEffect(() => {
    if (isOpen) {
      fetchSettings();
      fetchHealth();
    }
  }, [isOpen]);

  const fetchSettings = async () => {
    try {
      const res = await fetch('/settings');
      if (res.ok) {
        const data = await res.json();
        setGeminiModel(data.gemini_model || 'gemini-1.5-flash');
        setModel(data.openai_model || 'gpt-4o-mini');
        setProvider(data.llm_provider || 'auto');
        setLocalUrl(data.local_llm_url || 'http://localhost:11434');
        setLocalModel(data.local_llm_model || 'llama3');
        setTopK(data.top_k_results || 4);
      }
    } catch (e) {
      console.error("Failed to load settings:", e);
    }
  };

  const fetchHealth = async () => {
    try {
      const res = await fetch('/health');
      if (res.ok) {
        const data = await res.json();
        setHealthInfo(data);
      }
    } catch (e) {
      console.error("Failed to load health info:", e);
    }
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    setSuccessMsg('');

    const payload = {
      gemini_model: geminiModel,
      openai_model: model,
      llm_provider: provider,
      local_llm_url: localUrl,
      local_llm_model: localModel,
      top_k_results: parseInt(topK, 10)
    };

    if (geminiKey.trim()) {
      payload.gemini_api_key = geminiKey.trim();
    }
    if (apiKey.trim()) {
      payload.openai_api_key = apiKey.trim();
    }

    try {
      const res = await fetch('/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (res.ok) {
        setSuccessMsg('Settings saved successfully!');
        if (onSettingsUpdated) onSettingsUpdated();
        setTimeout(() => setSuccessMsg(''), 3000);
      }
    } catch (err) {
      console.error("Error saving settings:", err);
    } finally {
      setSaving(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fade-in">
      <div className="w-full max-w-lg rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-2xl p-6 text-slate-800 dark:text-slate-100 max-h-[90vh] overflow-y-auto">
        
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-slate-100 dark:border-slate-800">
          <div className="flex items-center space-x-2.5">
            <span className="text-xl">⚙️</span>
            <div>
              <h2 className="text-base font-semibold">System Settings</h2>
              <p className="text-xs text-slate-500 dark:text-slate-400">Configure LLM providers, models, and RAG search parameters</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 p-1 rounded-md"
          >
            ✕
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSave} className="py-4 space-y-4 text-xs">
          
          {/* Diagnostic Status Box */}
          {healthInfo && (
            <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700/60 space-y-1">
              <div className="flex items-center justify-between font-medium">
                <span className="text-slate-500 dark:text-slate-400">System Status:</span>
                <span className="text-emerald-500 font-semibold">● {healthInfo.status}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-500 dark:text-slate-400">Active Engine:</span>
                <span className="font-mono text-[11px] text-blue-600 dark:text-blue-400">{healthInfo.llm_provider}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-500 dark:text-slate-400">Indexed Knowledge:</span>
                <span>{healthInfo.documents_count} docs ({healthInfo.total_chunks} chunks)</span>
              </div>
            </div>
          )}

          {/* Provider Selection */}
          <div className="space-y-1.5">
            <label className="font-semibold text-slate-700 dark:text-slate-300">
              Inference Engine / Provider
            </label>
            <select
              value={provider}
              onChange={(e) => setProvider(e.target.value)}
              className="w-full px-3 py-2 rounded-lg bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-800 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
            >
              <option value="auto">Auto (Google Gemini / OpenAI / Smart Offline Engine)</option>
              <option value="gemini">Google Gemini API (Active Key)</option>
              <option value="openai">OpenAI API (GPT-4o / GPT-4o-mini)</option>
              <option value="local_llama">Local LLaMA (Ollama)</option>
            </select>
          </div>

          {/* Google Gemini Configuration */}
          <div className="p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 space-y-3 bg-slate-50/50 dark:bg-slate-800/20">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold text-slate-800 dark:text-slate-200">Google Gemini API</h3>
              <span className="px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 text-[10px] font-mono">Active in Backend</span>
            </div>
            
            <div className="space-y-1">
              <label className="text-slate-600 dark:text-slate-400">Gemini API Key</label>
              <input
                type="text"
                value={geminiKey}
                onChange={(e) => setGeminiKey(e.target.value)}
                placeholder="Enter your Gemini API key"
                className="w-full px-3 py-2 rounded-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 text-slate-800 dark:text-slate-100 font-mono text-[11px]"
              />
            </div>

            <div className="space-y-1">
              <label className="text-slate-600 dark:text-slate-400">Model</label>
              <select
                value={geminiModel}
                onChange={(e) => setGeminiModel(e.target.value)}
                className="w-full px-3 py-2 rounded-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 text-slate-800 dark:text-slate-100"
              >
                <option value="gemini-1.5-flash">gemini-1.5-flash (Fast & Recommended)</option>
                <option value="gemini-1.5-pro">gemini-1.5-pro (High Reasoning)</option>
                <option value="gemini-2.0-flash-exp">gemini-2.0-flash-exp (Next-Gen)</option>
              </select>
            </div>
          </div>

          {/* OpenAI Configuration */}
          <div className="p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 space-y-3 bg-slate-50/50 dark:bg-slate-800/20">
            <h3 className="font-semibold text-slate-800 dark:text-slate-200">OpenAI API Setup (Optional)</h3>
            <div className="space-y-1">
              <label className="text-slate-600 dark:text-slate-400">OpenAI API Key</label>
              <input
                type="password"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder="sk-proj-..."
                className="w-full px-3 py-2 rounded-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 text-slate-800 dark:text-slate-100 font-mono text-[11px]"
              />
            </div>
          </div>

          {/* RAG Parameters */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <label className="font-semibold text-slate-700 dark:text-slate-300">
                Top-K Chunks to Retrieve: {topK}
              </label>
            </div>
            <input
              type="range"
              min="1"
              max="8"
              value={topK}
              onChange={(e) => setTopK(e.target.value)}
              className="w-full accent-blue-600 cursor-pointer"
            />
            <div className="flex justify-between text-[10px] text-slate-400 font-mono">
              <span>1 (Precise)</span>
              <span>4 (Default)</span>
              <span>8 (Comprehensive)</span>
            </div>
          </div>

          {/* Alert Message */}
          {successMsg && (
            <div className="p-2.5 rounded-lg bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 text-xs text-emerald-600 dark:text-emerald-300 font-medium">
              ✓ {successMsg}
            </div>
          )}

          {/* Actions */}
          <div className="flex items-center justify-end space-x-2.5 pt-3 border-t border-slate-100 dark:border-slate-800">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-lg text-xs font-medium text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
            >
              Close
            </button>
            <button
              type="submit"
              disabled={saving}
              className="px-4 py-2 rounded-lg text-xs font-medium bg-blue-600 hover:bg-blue-500 text-white transition-colors shadow-sm shadow-blue-500/20"
            >
              {saving ? "Saving..." : "Save Settings"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
