import React, { useState, useRef } from 'react';

export default function FileUpload({ isOpen, onClose, onUploadSuccess }) {
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState('');
  const [uploadResult, setUploadResult] = useState(null);
  const [errorMsg, setErrorMsg] = useState('');
  const fileInputRef = useRef(null);

  if (!isOpen) return null;

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelected(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFileSelected(e.target.files[0]);
    }
  };

  const handleFileSelected = (file) => {
    setErrorMsg('');
    setUploadResult(null);
    const validExtensions = ['.pdf', '.txt', '.md'];
    const ext = '.' + file.name.split('.').pop().toLowerCase();

    if (!validExtensions.includes(ext)) {
      setErrorMsg(`Invalid file type. Supported formats: ${validExtensions.join(', ')}`);
      return;
    }

    if (file.size > 25 * 1024 * 1024) {
      setErrorMsg('File exceeds 25 MB limit.');
      return;
    }

    setSelectedFile(file);
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    setUploading(true);
    setUploadProgress('Extracting text & generating semantic embeddings...');
    setErrorMsg('');

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const response = await fetch('/upload', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Upload failed');
      }

      const data = await response.json();
      setUploadResult(data);
      setUploadProgress('Document indexed successfully!');
      if (onUploadSuccess) onUploadSuccess(data);
    } catch (err) {
      setErrorMsg(err.message || 'Error occurred while processing file');
    } finally {
      setUploading(false);
    }
  };

  const resetForm = () => {
    setSelectedFile(null);
    setUploadResult(null);
    setErrorMsg('');
    setUploadProgress('');
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fade-in">
      <div className="w-full max-w-lg rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-2xl p-6 text-slate-800 dark:text-slate-100">
        
        {/* Modal Header */}
        <div className="flex items-center justify-between pb-4 border-b border-slate-100 dark:border-slate-800">
          <div className="flex items-center space-x-2.5">
            <span className="text-xl">📎</span>
            <div>
              <h2 className="text-base font-semibold">Upload Knowledge Documents</h2>
              <p className="text-xs text-slate-500 dark:text-slate-400">Add notes or textbooks to your RAG vector index</p>
            </div>
          </div>
          <button
            onClick={() => { resetForm(); onClose(); }}
            className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 p-1 rounded-md"
          >
            ✕
          </button>
        </div>

        {/* Modal Body */}
        <div className="py-5 space-y-4">
          {!uploadResult ? (
            <>
              {/* Drop Zone */}
              <div
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current && fileInputRef.current.click()}
                className={`
                  border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all
                  ${dragActive 
                    ? 'border-blue-500 bg-blue-50/50 dark:bg-blue-950/30' 
                    : 'border-slate-300 dark:border-slate-700 hover:border-slate-400 dark:hover:border-slate-600 bg-slate-50/50 dark:bg-slate-800/30'}
                `}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf,.txt,.md"
                  onChange={handleChange}
                  className="hidden"
                />
                
                <div className="text-3xl mb-2">📄</div>
                <p className="text-sm font-medium text-slate-700 dark:text-slate-300">
                  {selectedFile ? selectedFile.name : 'Click to browse or drag & drop files here'}
                </p>
                <p className="text-xs text-slate-400 mt-1">
                  Supported formats: PDF, TXT, Markdown (Max 25 MB)
                </p>
              </div>

              {/* Status and Error */}
              {errorMsg && (
                <div className="p-3 rounded-lg bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900/60 text-xs text-red-600 dark:text-red-400">
                  ⚠️ {errorMsg}
                </div>
              )}

              {uploading && (
                <div className="space-y-2">
                  <div className="flex items-center space-x-2 text-xs text-blue-600 dark:text-blue-400">
                    <span className="animate-spin">⏳</span>
                    <span>{uploadProgress}</span>
                  </div>
                  <div className="w-full bg-slate-100 dark:bg-slate-800 h-1.5 rounded-full overflow-hidden">
                    <div className="bg-blue-600 h-full w-2/3 animate-pulse rounded-full" />
                  </div>
                </div>
              )}
            </>
          ) : (
            /* Upload Success Result Card */
            <div className="p-4 rounded-xl bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-800/60 space-y-3">
              <div className="flex items-center space-x-2 text-emerald-700 dark:text-emerald-300 font-semibold text-sm">
                <span>✅</span>
                <span>Document Successfully Indexed!</span>
              </div>
              <div className="grid grid-cols-2 gap-2 text-xs text-slate-600 dark:text-slate-300 pt-1">
                <div><strong>File:</strong> {uploadResult.filename}</div>
                <div><strong>Document ID:</strong> #{uploadResult.document_id}</div>
                <div><strong>Pages:</strong> {uploadResult.page_count}</div>
                <div><strong>Chunks Created:</strong> {uploadResult.chunks_created}</div>
              </div>
              <p className="text-xs text-emerald-600 dark:text-emerald-400">
                You can now ask questions about this document in the chat!
              </p>
            </div>
          )}
        </div>

        {/* Modal Actions */}
        <div className="flex items-center justify-end space-x-2.5 pt-3 border-t border-slate-100 dark:border-slate-800">
          <button
            type="button"
            onClick={() => { resetForm(); onClose(); }}
            className="px-4 py-2 rounded-lg text-xs font-medium text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
          >
            {uploadResult ? 'Done' : 'Cancel'}
          </button>

          {!uploadResult ? (
            <button
              type="button"
              onClick={handleUpload}
              disabled={!selectedFile || uploading}
              className={`
                px-4 py-2 rounded-lg text-xs font-medium text-white transition-all
                ${!selectedFile || uploading
                  ? 'bg-slate-300 dark:bg-slate-800 cursor-not-allowed'
                  : 'bg-blue-600 hover:bg-blue-500 shadow-sm shadow-blue-500/20'}
              `}
            >
              {uploading ? 'Processing...' : 'Start Ingestion'}
            </button>
          ) : (
            <button
              type="button"
              onClick={() => { resetForm(); onClose(); }}
              className="px-4 py-2 rounded-lg text-xs font-medium bg-emerald-600 hover:bg-emerald-500 text-white transition-colors"
            >
              Start Chatting with Notes
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
