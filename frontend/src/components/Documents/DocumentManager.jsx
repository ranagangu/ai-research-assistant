import React, { useState, useEffect, useRef } from 'react';
import { docService } from '../../services/api';
import { 
  Upload, 
  Trash2, 
  FileText, 
  Sparkles, 
  Loader2, 
  CheckCircle, 
  XCircle, 
  HelpCircle, 
  Info,
  Copy,
  Check,
  ChevronRight,
  BookOpen
} from 'lucide-react';

export default function DocumentManager() {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState('');
  const fileInputRef = useRef(null);

  // AI Drawer State
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [selectedDoc, setSelectedDoc] = useState(null);
  const [aiAction, setAiAction] = useState(''); // 'summarize', 'keywords', 'questions'
  const [aiResult, setAiResult] = useState('');
  const [aiLoading, setAiLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  const fetchDocuments = async () => {
    setLoading(true);
    try {
      const data = await docService.list();
      setDocuments(data);
    } catch (error) {
      console.error('Failed to fetch documents:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
    // Poll document statuses every 5 seconds if any doc is 'uploading' or 'processing'
    const interval = setInterval(() => {
      const activeProcessing = documents.some(d => d.status === 'uploading' || d.status === 'processing');
      if (activeProcessing) {
        fetchDocuments();
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [documents]);

  const handleFileChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    // Validate size (10MB)
    if (file.size > 10 * 1024 * 1024) {
      setUploadError('File size exceeds 10MB limit.');
      return;
    }

    setUploadError('');
    setUploading(true);

    try {
      await docService.upload(file);
      fetchDocuments();
    } catch (error) {
      console.error(error);
      setUploadError(error.response?.data?.detail || 'Failed to upload document.');
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this document? This will also remove all its vector embeddings.')) {
      return;
    }

    try {
      await docService.delete(id);
      setDocuments(prev => prev.filter(d => d.id !== id));
      if (selectedDoc?.id === id) {
        setDrawerOpen(false);
      }
    } catch (error) {
      console.error('Failed to delete document:', error);
      alert('Delete failed: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleAiAction = async (doc, action) => {
    setSelectedDoc(doc);
    setAiAction(action);
    setAiResult('');
    setAiLoading(true);
    setDrawerOpen(true);
    setCopied(false);

    try {
      let data;
      if (action === 'summarize') {
        data = await docService.summarize(doc.id);
        setAiResult(data.summary);
      } else if (action === 'keywords') {
        data = await docService.getKeywords(doc.id);
        setAiResult(data.keywords.join(', '));
      } else if (action === 'questions') {
        data = await docService.getQuestions(doc.id);
        setAiResult(data.questions.map((q, i) => `${i + 1}. ${q}`).join('\n'));
      }
    } catch (error) {
      console.error(error);
      setAiResult(error.response?.data?.detail || `AI Operation failed: ${error.message}`);
    } finally {
      setAiLoading(false);
    }
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(aiResult);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'indexed':
        return (
          <span className="flex items-center gap-1 text-xs text-emerald-400 bg-emerald-500/10 px-2.5 py-1 rounded-full border border-emerald-500/20 font-semibold">
            <CheckCircle size={12} /> Indexed
          </span>
        );
      case 'failed':
        return (
          <span className="flex items-center gap-1 text-xs text-rose-400 bg-rose-500/10 px-2.5 py-1 rounded-full border border-rose-500/20 font-semibold">
            <XCircle size={12} /> Failed
          </span>
        );
      case 'processing':
      case 'uploading':
        return (
          <span className="flex items-center gap-1 text-xs text-brand-400 bg-brand-500/10 px-2.5 py-1 rounded-full border border-brand-500/20 font-semibold animate-pulse">
            <Loader2 size={12} className="animate-spin" /> Processing
          </span>
        );
      default:
        return (
          <span className="flex items-center gap-1 text-xs text-slate-400 bg-slate-500/10 px-2.5 py-1 rounded-full font-semibold">
            <HelpCircle size={12} /> {status}
          </span>
        );
    }
  };

  const formatBytes = (bytes, decimals = 2) => {
    if (!bytes) return '0 Bytes';
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
  };

  return (
    <div className="flex-1 p-6 md:p-10 flex flex-col md:flex-row gap-8 min-h-0 relative">
      {/* Primary Workspace */}
      <div className="flex-1 flex flex-col min-w-0">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
          <div>
            <h1 className="text-2xl md:text-3xl font-extrabold text-white flex items-center gap-2">
              <BookOpen className="text-brand-400" /> Document Center
            </h1>
            <p className="text-slate-400 text-sm mt-1">
              Upload PDF, DOCX, or TXT documents to index them in the Chroma Vector Database.
            </p>
          </div>
          
          <div>
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileChange}
              accept=".pdf,.docx,.txt"
              className="hidden"
            />
            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={uploading}
              className="glass-btn-primary py-3 w-full md:w-auto"
            >
              {uploading ? (
                <>
                  <Loader2 size={18} className="animate-spin" />
                  Uploading File...
                </>
              ) : (
                <>
                  <Upload size={18} />
                  Upload Document
                </>
              )}
            </button>
          </div>
        </div>

        {uploadError && (
          <div className="mb-6 p-4 bg-rose-500/10 border border-rose-500/20 text-rose-300 rounded-xl text-sm flex items-center gap-2">
            <XCircle size={18} className="shrink-0" />
            <span>{uploadError}</span>
          </div>
        )}

        {/* Ingestion Dropzone Placeholder for premium styling */}
        {documents.length === 0 && !loading && (
          <div 
            onClick={() => fileInputRef.current?.click()}
            className="flex-1 flex flex-col items-center justify-center border-2 border-dashed border-slate-700/60 rounded-3xl p-10 cursor-pointer hover:border-brand-500/40 hover:bg-brand-500/5 transition-all duration-300 min-h-[300px]"
          >
            <div className="p-5 bg-slate-900/40 rounded-full border border-slate-800 text-slate-400 mb-4">
              <Upload size={36} />
            </div>
            <h3 className="text-lg font-bold text-white mb-1">Upload your research material</h3>
            <p className="text-slate-500 text-sm text-center max-w-sm mb-4">
              Supports PDF, DOCX, and TXT files up to 10MB. Document chunks will be vectorized for instant RAG responses.
            </p>
            <span className="text-xs text-brand-400 font-semibold bg-brand-500/10 border border-brand-500/20 px-3 py-1 rounded-full">
              Click to browse files
            </span>
          </div>
        )}

        {/* Documents Table */}
        {documents.length > 0 && (
          <div className="flex-1 glass-panel rounded-2xl border border-white/5 overflow-hidden flex flex-col min-h-[300px]">
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-white/5 bg-white/5 text-slate-400 text-xs font-semibold uppercase tracking-wider">
                    <th className="px-6 py-4">Document Details</th>
                    <th className="px-6 py-4">File Size</th>
                    <th className="px-6 py-4">Status</th>
                    <th className="px-6 py-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {documents.map((doc) => (
                    <tr key={doc.id} className="hover:bg-white/5 transition-colors group">
                      <td className="px-6 py-4 flex items-center gap-3">
                        <div className="p-2.5 bg-slate-900 rounded-xl border border-slate-800 text-slate-400 group-hover:text-brand-400 group-hover:border-brand-500/20 transition-all">
                          <FileText size={20} />
                        </div>
                        <div className="truncate max-w-[200px] md:max-w-[350px]">
                          <p className="text-sm font-semibold text-white truncate">{doc.filename}</p>
                          <span className="text-[10px] text-slate-500 truncate block">ID: {doc.id}</span>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-sm text-slate-400">
                        {formatBytes(doc.file_size)}
                      </td>
                      <td className="px-6 py-4">
                        {getStatusBadge(doc.status)}
                      </td>
                      <td className="px-6 py-4 text-right">
                        <div className="flex items-center justify-end gap-2">
                          {doc.status === 'indexed' && (
                            <div className="flex items-center gap-1 bg-slate-900/60 p-1 rounded-lg border border-white/5 opacity-0 group-hover:opacity-100 focus-within:opacity-100 transition-opacity">
                              <button
                                onClick={() => handleAiAction(doc, 'summarize')}
                                className="p-1.5 text-xs text-slate-400 hover:text-brand-400 hover:bg-brand-500/10 rounded-md transition-colors flex items-center gap-1"
                                title="Generate Summary"
                              >
                                <Sparkles size={13} />
                                <span>Summary</span>
                              </button>
                              <button
                                onClick={() => handleAiAction(doc, 'questions')}
                                className="p-1.5 text-xs text-slate-400 hover:text-brand-400 hover:bg-brand-500/10 rounded-md transition-colors flex items-center gap-1"
                                title="Generate review questions"
                              >
                                <HelpCircle size={13} />
                                <span>Q&A</span>
                              </button>
                            </div>
                          )}
                          <button
                            onClick={() => handleDelete(doc.id)}
                            className="p-2 text-slate-500 hover:text-rose-400 hover:bg-rose-500/10 rounded-xl border border-transparent hover:border-rose-500/20 transition-all duration-200"
                            title="Delete document"
                          >
                            <Trash2 size={16} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {/* AI Drawer Side Panel */}
      {drawerOpen && selectedDoc && (
        <div className="w-full md:w-96 glass-panel rounded-2xl border border-white/5 flex flex-col shrink-0 overflow-hidden relative animate-in slide-in-from-right duration-300">
          <div className="p-5 border-b border-white/5 flex items-center justify-between bg-white/5">
            <div className="flex items-center gap-2">
              <Sparkles size={16} className="text-brand-400" />
              <h3 className="font-bold text-white text-sm capitalize">{aiAction} Utilities</h3>
            </div>
            <button 
              onClick={() => setDrawerOpen(false)}
              className="text-slate-400 hover:text-white p-1 hover:bg-white/5 rounded-lg transition-all"
            >
              <XCircle size={18} />
            </button>
          </div>

          <div className="p-4 bg-slate-950/20 border-b border-white/5">
            <span className="text-[10px] text-slate-500 font-semibold uppercase tracking-wider block">Target Document</span>
            <span className="text-xs text-white truncate font-medium block mt-0.5">{selectedDoc.filename}</span>
          </div>

          <div className="flex-1 p-5 overflow-y-auto text-sm leading-relaxed text-slate-300">
            {aiLoading ? (
              <div className="h-full flex flex-col items-center justify-center py-12 text-slate-400">
                <Loader2 size={36} className="animate-spin text-brand-400 mb-3" />
                <p className="font-semibold text-xs">Analyzing document content...</p>
                <p className="text-[10px] text-slate-500 mt-1">This may take 10-15 seconds for larger files.</p>
              </div>
            ) : (
              <div className="whitespace-pre-line font-light text-slate-300">
                {aiResult || 'No analysis available.'}
              </div>
            )}
          </div>

          {!aiLoading && aiResult && (
            <div className="p-4 border-t border-white/5 bg-slate-950/30 flex gap-2">
              <button
                onClick={handleCopy}
                className="flex-1 glass-btn-secondary py-2 flex items-center justify-center gap-1.5 text-xs"
              >
                {copied ? (
                  <>
                    <Check size={14} className="text-emerald-400" />
                    <span>Copied!</span>
                  </>
                ) : (
                  <>
                    <Copy size={14} />
                    <span>Copy Results</span>
                  </>
                )}
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
