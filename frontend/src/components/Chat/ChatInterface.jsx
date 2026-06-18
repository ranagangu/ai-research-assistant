import React, { useState, useEffect, useRef } from 'react';
import { chatService } from '../../services/api';
import { 
  Bot, 
  Send, 
  Plus, 
  Trash2, 
  MessageSquare, 
  Sparkles, 
  Loader2, 
  BookOpen, 
  ChevronRight,
  ExternalLink,
  XCircle,
  Clock
} from 'lucide-react';

export default function ChatInterface() {
  const [sessions, setSessions] = useState([]);
  const [activeSessionId, setActiveSessionId] = useState(null);
  const [sessionDetails, setSessionDetails] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState('');
  
  // Loading & Streaming states
  const [loadingSessions, setLoadingSessions] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [streaming, setStreaming] = useState(false);
  const [activeCitation, setActiveCitation] = useState(null); // stores {filename, chunk_index, text} for modal view

  const chatEndRef = useRef(null);
  const eventSourceRef = useRef(null);

  // 1. Fetch sessions on load
  const fetchSessions = async (selectLatest = true) => {
    setLoadingSessions(true);
    try {
      const data = await chatService.listSessions();
      setSessions(data);
      if (selectLatest && data.length > 0 && !activeSessionId) {
        setActiveSessionId(data[0].id);
      }
    } catch (error) {
      console.error('Failed to load chat sessions:', error);
    } finally {
      setLoadingSessions(false);
    }
  };

  useEffect(() => {
    fetchSessions();
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, []);

  // 2. Fetch session messages when active session changes
  useEffect(() => {
    if (!activeSessionId) {
      setSessionDetails(null);
      setMessages([]);
      return;
    }

    const loadSessionDetails = async () => {
      setLoadingHistory(true);
      try {
        const data = await chatService.getSession(activeSessionId);
        setSessionDetails(data);
        // Parse sources from string to object if stored as string
        const parsedMessages = data.messages.map(m => {
          let sources = m.sources;
          if (typeof m.sources === 'string' && m.sources) {
            try {
              sources = JSON.parse(m.sources);
            } catch (e) {
              sources = [];
            }
          }
          return { ...m, sources };
        });
        setMessages(parsedMessages);
      } catch (error) {
        console.error('Failed to load session details:', error);
      } finally {
        setLoadingHistory(false);
      }
    };

    loadSessionDetails();
  }, [activeSessionId]);

  // 3. Auto Scroll to Bottom on message update
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streaming]);

  // 4. Create new chat session
  const handleCreateSession = async () => {
    try {
      const newSession = await chatService.createSession("Research Session " + (sessions.length + 1));
      setSessions(prev => [newSession, ...prev]);
      setActiveSessionId(newSession.id);
    } catch (error) {
      console.error('Failed to create new session:', error);
    }
  };

  // 5. Delete session
  const handleDeleteSession = async (e, sessionId) => {
    e.stopPropagation();
    if (!window.confirm('Delete this research session and all its messages?')) return;

    try {
      await chatService.deleteSession(sessionId);
      setSessions(prev => prev.filter(s => s.id !== sessionId));
      if (activeSessionId === sessionId) {
        setActiveSessionId(null);
      }
    } catch (error) {
      console.error('Failed to delete session:', error);
    }
  };

  // 6. RAG Streaming execution
  const handleSend = (e) => {
    e.preventDefault();
    if (!inputText.trim() || streaming || !activeSessionId) return;

    const queryText = inputText.trim();
    setInputText('');

    // Append User Message immediately
    const userMsg = {
      id: Date.now().toString(),
      role: 'user',
      content: queryText,
      created_at: new Date().toISOString()
    };
    
    // Append Assistant message placeholder
    const assistantPlaceholder = {
      id: 'stream-placeholder',
      role: 'assistant',
      content: '',
      sources: [],
      created_at: new Date().toISOString(),
      isStreaming: true
    };

    setMessages(prev => [...prev, userMsg, assistantPlaceholder]);
    setStreaming(true);

    // Build event source URL
    const streamUrl = chatService.getStreamUrl(activeSessionId, queryText);
    const eventSource = new EventSource(streamUrl);
    eventSourceRef.current = eventSource;

    let accumulatedAnswer = '';

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        if (data.type === 'token') {
          accumulatedAnswer += data.content;
          setMessages(prev => prev.map(m => {
            if (m.id === 'stream-placeholder') {
              return { ...m, content: accumulatedAnswer };
            }
            return m;
          }));
        } 
        
        else if (data.type === 'done') {
          eventSource.close();
          setStreaming(false);
          // Replace placeholder with final message details
          setMessages(prev => prev.map(m => {
            if (m.id === 'stream-placeholder') {
              return { 
                ...m, 
                id: data.message_id, 
                content: accumulatedAnswer,
                sources: data.sources,
                isStreaming: false
              };
            }
            return m;
          }));
        }
      } catch (err) {
        console.error("Failed parsing stream token:", err);
      }
    };

    eventSource.onerror = (err) => {
      console.error("EventSource stream connection error:", err);
      eventSource.close();
      setStreaming(false);
      setMessages(prev => prev.map(m => {
        if (m.id === 'stream-placeholder') {
          return { 
            ...m, 
            id: 'failed-placeholder', 
            content: accumulatedAnswer + '\n\n[Connection lost. Stream ended or network error. Please refresh and try again.]',
            isStreaming: false
          };
        }
        return m;
      }));
    };
  };

  // 7. Render text with Markdown highlights and inline Citation links
  const renderMessageContent = (text) => {
    // Escape standard code boxes to avoid formatting errors
    const parts = text.split(/(```[\s\S]*?```|`[^`\n]+`)/g);

    return parts.map((part, index) => {
      if (part.startsWith('```') && part.endsWith('```')) {
        const code = part.slice(3, -3).replace(/^[a-zA-Z]+\n/, ''); // remove language identifier
        return (
          <pre key={index} className="bg-slate-950/80 p-3 rounded-xl overflow-x-auto text-xs font-mono my-2 border border-white/5">
            <code>{code}</code>
          </pre>
        );
      }
      
      if (part.startsWith('`') && part.endsWith('`')) {
        return (
          <code key={index} className="bg-slate-900/60 px-1 py-0.5 rounded text-xs text-brand-300 font-mono">
            {part.slice(1, -1)}
          </code>
        );
      }

      // Format markdown lists and citations
      const lines = part.split('\n');
      return lines.map((line, lIdx) => {
        let cleanLine = line.trim();
        
        // Headers
        if (cleanLine.startsWith('###')) {
          return <h3 key={`${index}-${lIdx}`} className="text-sm font-bold mt-2 text-white">{cleanLine.replace('###', '').trim()}</h3>;
        }
        if (cleanLine.startsWith('##')) {
          return <h2 key={`${index}-${lIdx}`} className="text-base font-bold mt-2 text-white">{cleanLine.replace('##', '').trim()}</h2>;
        }
        if (cleanLine.startsWith('#')) {
          return <h1 key={`${index}-${lIdx}`} className="text-lg font-bold mt-2 text-white">{cleanLine.replace('#', '').trim()}</h1>;
        }

        // Bullet list
        if (cleanLine.startsWith('-') || cleanLine.startsWith('*')) {
          return (
            <li key={`${index}-${lIdx}`} className="text-sm text-slate-300 ml-4 list-disc list-item leading-relaxed mb-0.5">
              {parseInlineCitations(cleanLine.substring(1).trim())}
            </li>
          );
        }

        // Standard Paragraph line
        return (
          <p key={`${index}-${lIdx}`} className="text-sm text-slate-300 leading-relaxed mb-2">
            {parseInlineCitations(line)}
          </p>
        );
      });
    });
  };

  // Inline citations parsing e.g. [Document.pdf (Chunk 2)]
  const parseInlineCitations = (lineText) => {
    // Regex matching any patterns inside bracket ending with Chunk digits
    const regex = /\[([^\]]+?\.(?:pdf|docx|txt))\s+\(Chunk\s+(\d+)\)\]/gi;
    const parts = lineText.split(regex);
    if (parts.length <= 1) return lineText;

    const rendered = [];
    let i = 0;
    while (i < parts.length) {
      // Add plain text lead
      rendered.push(parts[i]);
      if (i + 1 < parts.length) {
        const filename = parts[i + 1];
        const chunkIndex = parts[i + 2];
        rendered.push(
          <span 
            key={i} 
            className="inline-flex items-center gap-0.5 px-1.5 py-0.5 text-[10px] font-semibold text-brand-300 bg-brand-500/15 border border-brand-500/25 rounded-md cursor-pointer hover:bg-brand-500/30 transition-all select-none mx-0.5"
            title="Click to view context chunk"
            onClick={() => handleCitationClick(filename, chunkIndex)}
          >
            <BookOpen size={10} />
            {filename.substring(0, 10)}... (C{chunkIndex})
          </span>
        );
        i += 3;
      } else {
        i += 1;
      }
    }
    return rendered;
  };

  const handleCitationClick = (filename, chunkIndex) => {
    // Look up citation chunk text from the message logs if available
    let foundSource = null;
    for (const msg of messages) {
      if (msg.sources) {
        foundSource = msg.sources.find(s => s.filename === filename && s.chunk_index.toString() === chunkIndex.toString());
        if (foundSource) break;
      }
    }

    if (foundSource) {
      setActiveCitation(foundSource);
    } else {
      setActiveCitation({
        filename,
        chunk_index: chunkIndex,
        text: "Full citation content details are listed in the message's Citation Hub below."
      });
    }
  };

  return (
    <div className="flex-1 flex min-h-0 relative">
      {/* Session mini sidebar */}
      <div className="hidden lg:flex flex-col w-64 border-r border-white/5 bg-slate-950/35 shrink-0 select-none">
        <div className="p-4 border-b border-white/5">
          <button
            onClick={handleCreateSession}
            className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-brand-500/10 hover:bg-brand-500/20 border border-brand-500/20 text-brand-300 font-semibold rounded-xl text-xs tracking-wider uppercase active:scale-95 transition-all"
          >
            <Plus size={14} />
            <span>New Session</span>
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-3 space-y-1">
          {loadingSessions ? (
            <div className="h-32 flex items-center justify-center">
              <Loader2 className="animate-spin text-slate-600" size={20} />
            </div>
          ) : sessions.length === 0 ? (
            <div className="h-32 flex flex-col items-center justify-center text-center px-4">
              <MessageSquare size={20} className="text-slate-600 mb-2" />
              <p className="text-xs text-slate-500">No chat history. Start a new session.</p>
            </div>
          ) : (
            sessions.map((session) => {
              const isActive = activeSessionId === session.id;
              return (
                <div
                  key={session.id}
                  onClick={() => setActiveSessionId(session.id)}
                  className={`group w-full flex items-center justify-between px-3 py-2.5 rounded-xl cursor-pointer transition-all border ${
                    isActive 
                      ? 'bg-brand-600/10 border-brand-500/35 text-white' 
                      : 'border-transparent text-slate-400 hover:bg-white/5 hover:text-slate-200'
                  }`}
                >
                  <div className="flex items-center gap-2.5 truncate min-w-0">
                    <MessageSquare size={16} className={isActive ? "text-brand-400" : "text-slate-500"} />
                    <span className="text-xs truncate font-medium">{session.title}</span>
                  </div>
                  <button
                    onClick={(e) => handleDeleteSession(e, session.id)}
                    className="p-1 opacity-0 group-hover:opacity-100 hover:text-rose-400 hover:bg-rose-500/10 rounded-md transition-all shrink-0"
                  >
                    <Trash2 size={12} />
                  </button>
                </div>
              );
            })
          )}
        </div>
      </div>

      {/* Main chat interface */}
      <div className="flex-1 flex flex-col bg-slate-950/10 min-w-0 relative">
        {!activeSessionId ? (
          <div className="flex-1 flex flex-col items-center justify-center p-8 text-center">
            <div className="p-4 bg-brand-500/10 text-brand-400 rounded-3xl mb-4 border border-brand-500/20">
              <Bot size={42} />
            </div>
            <h2 className="text-xl font-bold text-white mb-2">Research Workspace</h2>
            <p className="text-slate-400 text-sm max-w-sm mb-6">
              Create a new research session to start querying your documents with Retrieval-Augmented Generation.
            </p>
            <button
              onClick={handleCreateSession}
              className="glass-btn-primary flex items-center gap-2"
            >
              <Plus size={18} />
              Create Session
            </button>
          </div>
        ) : (
          <>
            {/* Chat Header */}
            <div className="p-4 border-b border-white/5 bg-slate-950/20 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-brand-600/15 border border-brand-500/20 text-brand-400 rounded-lg">
                  <Bot size={16} />
                </div>
                <div>
                  <h3 className="text-xs font-bold text-white leading-none">{sessionDetails?.title || "Active Session"}</h3>
                  <span className="text-[9px] text-slate-500 tracking-wider flex items-center gap-1 mt-0.5 font-semibold uppercase">
                    <Clock size={9} /> RAG Enabled
                  </span>
                </div>
              </div>
            </div>

            {/* Messages Scroll Area */}
            <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-6">
              {loadingHistory ? (
                <div className="h-full flex items-center justify-center">
                  <Loader2 className="animate-spin text-brand-400" size={32} />
                </div>
              ) : messages.length === 0 ? (
                <div className="h-full flex flex-col items-center justify-center text-center py-20">
                  <Bot size={32} className="text-brand-400 mb-3" />
                  <h4 className="font-bold text-white text-sm">Ask your first question</h4>
                  <p className="text-xs text-slate-500 max-w-xs mt-1">
                    Ask a question grounded in your document vector store, or query general facts.
                  </p>
                </div>
              ) : (
                messages.map((msg) => {
                  const isUser = msg.role === 'user';
                  return (
                    <div 
                      key={msg.id} 
                      className={`flex gap-4 ${isUser ? 'justify-end' : 'justify-start'}`}
                    >
                      {/* Avatar */}
                      {!isUser && (
                        <div className="w-8 h-8 rounded-xl bg-brand-600/20 border border-brand-500/20 text-brand-300 flex items-center justify-center shrink-0">
                          <Bot size={16} />
                        </div>
                      )}

                      <div className="flex flex-col max-w-[85%] md:max-w-[70%]">
                        {/* Bubble */}
                        <div 
                          className={`p-4 rounded-2xl relative ${
                            isUser 
                              ? 'bg-brand-600 text-white rounded-tr-none border border-brand-500/30' 
                              : 'glass-panel rounded-tl-none border border-white/5'
                          }`}
                        >
                          <div className="prose-chat">
                            {isUser ? <p className="text-sm leading-relaxed">{msg.content}</p> : renderMessageContent(msg.content)}
                          </div>
                          
                          {/* Typing indicator */}
                          {msg.isStreaming && msg.content === '' && (
                            <div className="flex items-center gap-1 py-1.5 px-0.5">
                              <span className="w-1.5 h-1.5 bg-brand-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                              <span className="w-1.5 h-1.5 bg-brand-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                              <span className="w-1.5 h-1.5 bg-brand-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                            </div>
                          )}
                        </div>

                        {/* Citations list footer (RAG specific) */}
                        {!isUser && msg.sources && msg.sources.length > 0 && (
                          <div className="mt-2.5 flex flex-wrap gap-1.5">
                            {msg.sources.map((src, sIdx) => (
                              <button
                                key={sIdx}
                                onClick={() => setActiveCitation(src)}
                                className="flex items-center gap-1.5 text-[9px] font-semibold text-slate-400 hover:text-slate-200 bg-white/5 border border-white/5 rounded-lg px-2.5 py-1 hover:bg-white/10 transition-colors"
                              >
                                <BookOpen size={10} />
                                <span>{src.filename.substring(0, 12)}... (Chunk {src.chunk_index})</span>
                              </button>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })
              )}
            </div>

            {/* Chat Input form */}
            <form onSubmit={handleSend} className="p-4 border-t border-white/5 bg-slate-950/20 flex gap-2 items-center">
              <input
                type="text"
                className="flex-1 glass-input py-3"
                placeholder="Ask about your research papers, notes, or general facts..."
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                disabled={streaming}
              />
              <button
                type="submit"
                disabled={!inputText.trim() || streaming}
                className="p-3 rounded-xl bg-brand-600 hover:bg-brand-500 text-white disabled:opacity-40 disabled:pointer-events-none hover:shadow-lg hover:shadow-brand-500/20 active:scale-95 transition-all duration-200 border border-brand-500/30"
              >
                {streaming ? <Loader2 size={18} className="animate-spin" /> : <Send size={18} />}
              </button>
            </form>
          </>
        )}
      </div>

      {/* Citation Popover Modal */}
      {activeCitation && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center p-4 z-50 animate-in fade-in duration-200">
          <div className="w-full max-w-lg glass-panel rounded-2xl border border-white/5 flex flex-col overflow-hidden max-h-[80vh] shadow-2xl relative animate-in zoom-in-95 duration-200">
            <div className="p-5 border-b border-white/5 flex items-center justify-between bg-white/5">
              <div className="flex items-center gap-2">
                <BookOpen size={16} className="text-brand-400" />
                <h4 className="font-bold text-white text-sm truncate">Source Citation context</h4>
              </div>
              <button 
                onClick={() => setActiveCitation(null)}
                className="text-slate-400 hover:text-white p-1 hover:bg-white/5 rounded-lg transition-all"
              >
                <XCircle size={18} />
              </button>
            </div>

            <div className="p-4 bg-slate-950/20 border-b border-white/5 text-xs text-slate-400 flex justify-between gap-4 font-semibold uppercase tracking-wider">
              <div>
                <span>Document:</span>
                <span className="text-white ml-1.5">{activeCitation.filename}</span>
              </div>
              <div>
                <span>Chunk:</span>
                <span className="text-white ml-1.5">{activeCitation.chunk_index}</span>
              </div>
            </div>

            <div className="flex-1 p-5 overflow-y-auto text-sm leading-relaxed text-slate-300 font-light whitespace-pre-line bg-slate-950/10">
              {activeCitation.text}
            </div>

            <div className="p-4 border-t border-white/5 bg-slate-950/30 flex justify-end">
              <button
                onClick={() => setActiveCitation(null)}
                className="glass-btn-secondary py-2 px-4 text-xs font-semibold"
              >
                Close View
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
