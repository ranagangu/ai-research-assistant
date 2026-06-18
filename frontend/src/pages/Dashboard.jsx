import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { 
  Bot, 
  FileText, 
  Database, 
  LogOut, 
  User, 
  Menu, 
  X,
  MessageSquare,
  Sparkles
} from 'lucide-react';

// Import child views
import DocumentManager from '../components/Documents/DocumentManager';
import ChatInterface from '../components/Chat/ChatInterface';
import AdminDashboard from '../components/Admin/AdminDashboard';

export default function Dashboard() {
  const { user, logout, isAdmin } = useAuth();
  const [activeTab, setActiveTab] = useState('chat'); // 'chat', 'documents', 'admin'
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    // If not authenticated, context redirect will handle it, but fallback check here
    if (!user) {
      const token = localStorage.getItem('token');
      if (!token) {
        navigate('/login');
      }
    }
  }, [user, navigate]);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const navItems = [
    { id: 'chat', label: 'RAG Research Hub', icon: MessageSquare },
    { id: 'documents', label: 'Document Center', icon: FileText },
  ];

  if (isAdmin) {
    navItems.push({ id: 'admin', label: 'Admin Analytics', icon: Database });
  }

  return (
    <div className="relative min-h-screen bg-[#020617] flex text-slate-100">
      {/* Background radial glows */}
      <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-glow-blue rounded-full blur-3xl opacity-60 pointer-events-none" />
      <div className="absolute bottom-0 left-0 w-[500px] h-[500px] bg-glow-purple rounded-full blur-3xl opacity-60 pointer-events-none" />

      {/* Sidebar for Desktop */}
      <aside className="hidden md:flex flex-col w-64 glass-panel border-r border-white/5 shrink-0 z-20">
        <div className="p-6 flex items-center gap-3 border-b border-white/5">
          <div className="p-2.5 bg-brand-500/10 text-brand-400 rounded-xl border border-brand-500/20">
            <Bot size={22} />
          </div>
          <div>
            <h2 className="font-bold text-white tracking-wide text-sm leading-none flex items-center gap-1.5">
              ResearchAI <Sparkles size={12} className="text-brand-400" />
            </h2>
            <span className="text-[10px] text-slate-500 font-semibold uppercase tracking-wider">Assistant v1.0</span>
          </div>
        </div>

        {/* Sidebar Nav */}
        <nav className="flex-1 px-4 py-6 space-y-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all duration-200 ${
                  isActive 
                    ? 'bg-brand-600 text-white shadow-lg shadow-brand-600/15 border border-brand-500/30' 
                    : 'text-slate-400 hover:bg-white/5 hover:text-slate-100 border border-transparent'
                }`}
              >
                <Icon size={18} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>

        {/* User Profile Area */}
        <div className="p-4 border-t border-white/5 bg-slate-950/20">
          <div className="flex items-center gap-3 mb-4 px-2">
            <div className="w-9 h-9 rounded-full bg-brand-600/20 border border-brand-500/20 flex items-center justify-center text-brand-300 font-bold uppercase">
              {user?.email ? user.email.charAt(0) : 'U'}
            </div>
            <div className="overflow-hidden">
              <p className="text-xs font-semibold text-white truncate">{user?.email}</p>
              <span className="text-[10px] bg-white/5 text-slate-400 px-1.5 py-0.5 rounded capitalize">
                {user?.role || 'User'}
              </span>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="w-full flex items-center justify-center gap-2 px-4 py-2 text-xs font-medium text-slate-400 hover:text-rose-400 hover:bg-rose-500/5 border border-transparent hover:border-rose-500/10 rounded-xl transition-all duration-200"
          >
            <LogOut size={14} />
            <span>Sign Out</span>
          </button>
        </div>
      </aside>

      {/* Sidebar Mobile Overlay */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 bg-black/60 z-30 md:hidden" 
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Mobile Drawer */}
      <aside 
        className={`fixed inset-y-0 left-0 w-64 glass-panel border-r border-white/5 flex flex-col z-40 transform transition-transform duration-300 md:hidden ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="p-6 flex items-center justify-between border-b border-white/5">
          <div className="flex items-center gap-3">
            <Bot size={22} className="text-brand-400" />
            <h2 className="font-bold text-white text-sm">ResearchAI</h2>
          </div>
          <button onClick={() => setSidebarOpen(false)} className="text-slate-400 hover:text-white">
            <X size={20} />
          </button>
        </div>

        <nav className="flex-1 px-4 py-6 space-y-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => {
                  setActiveTab(item.id);
                  setSidebarOpen(false);
                }}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all duration-200 ${
                  isActive 
                    ? 'bg-brand-600 text-white shadow-lg border border-brand-500/30' 
                    : 'text-slate-400 hover:bg-white/5 hover:text-slate-100 border border-transparent'
                }`}
              >
                <Icon size={18} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>

        <div className="p-4 border-t border-white/5">
          <div className="flex items-center gap-3 mb-4 px-2">
            <div className="w-8 h-8 rounded-full bg-brand-600/20 flex items-center justify-center text-brand-300 font-bold uppercase">
              {user?.email ? user.email.charAt(0) : 'U'}
            </div>
            <div className="overflow-hidden">
              <p className="text-xs font-semibold text-white truncate">{user?.email}</p>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="w-full flex items-center justify-center gap-2 px-4 py-2 text-xs font-medium text-slate-400 hover:text-rose-400 hover:bg-rose-500/5 border border-rose-500/10 rounded-xl transition-all duration-200"
          >
            <LogOut size={14} />
            <span>Sign Out</span>
          </button>
        </div>
      </aside>

      {/* Main Workspace content */}
      <div className="flex-1 flex flex-col min-w-0 min-h-screen relative z-10">
        {/* Mobile Header */}
        <header className="md:hidden flex items-center justify-between p-4 border-b border-white/5 bg-slate-950/20 backdrop-blur-md sticky top-0 z-20">
          <button 
            onClick={() => setSidebarOpen(true)}
            className="p-2 text-slate-400 hover:text-white bg-white/5 rounded-xl border border-white/5"
          >
            <Menu size={18} />
          </button>
          <div className="flex items-center gap-2">
            <Bot size={18} className="text-brand-400" />
            <span className="font-bold text-white text-sm">ResearchAI</span>
          </div>
          <div className="w-8 h-8 rounded-full bg-brand-600/20 flex items-center justify-center text-brand-300 font-bold text-sm uppercase">
            {user?.email ? user.email.charAt(0) : 'U'}
          </div>
        </header>

        {/* View render container */}
        <main className="flex-1 flex flex-col min-h-0 overflow-y-auto">
          {activeTab === 'chat' && <ChatInterface />}
          {activeTab === 'documents' && <DocumentManager />}
          {activeTab === 'admin' && isAdmin && <AdminDashboard />}
        </main>
      </div>
    </div>
  );
}
