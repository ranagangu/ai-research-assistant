import React, { useState, useEffect } from 'react';
import { adminService } from '../../services/api';
import { 
  Users, 
  FileText, 
  MessageSquare, 
  Layers, 
  HardDrive, 
  Loader2, 
  ShieldAlert, 
  TrendingUp,
  Mail,
  Calendar
} from 'lucide-react';

export default function AdminDashboard() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchStats = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await adminService.getStats();
      setStats(data);
    } catch (err) {
      console.error(err);
      setError('Failed to fetch administrator statistics. Ensure your account has admin privileges.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  if (loading) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-12">
        <Loader2 className="animate-spin text-brand-400 mb-3" size={36} />
        <p className="text-slate-400 text-xs font-semibold">Loading system metrics...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex-1 p-8 md:p-12 flex flex-col items-center justify-center max-w-lg mx-auto text-center">
        <div className="p-4 bg-rose-500/10 text-rose-400 border border-rose-500/20 rounded-3xl mb-4">
          <ShieldAlert size={42} />
        </div>
        <h2 className="text-xl font-bold text-white mb-2">Access Denied</h2>
        <p className="text-slate-400 text-sm mb-6 leading-relaxed">{error}</p>
        <button
          onClick={fetchStats}
          className="glass-btn-primary"
        >
          Try Reloading
        </button>
      </div>
    );
  }

  const cardData = [
    { label: 'Total Users', value: stats.total_users, icon: Users, color: 'text-sky-400 bg-sky-500/10 border-sky-500/20' },
    { label: 'Ingested Documents', value: stats.total_documents, icon: FileText, color: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20' },
    { label: 'Total User Queries', value: stats.total_queries, icon: MessageSquare, color: 'text-violet-400 bg-violet-500/10 border-violet-500/20' },
    { label: 'Vector DB Chunks', value: stats.system_stats.chroma_chunks, icon: Layers, color: 'text-brand-400 bg-brand-500/10 border-brand-500/20' },
  ];

  return (
    <div className="flex-1 p-6 md:p-10 flex flex-col min-h-0">
      <div className="mb-8">
        <h1 className="text-2xl md:text-3xl font-extrabold text-white flex items-center gap-2">
          <TrendingUp className="text-brand-400" /> Admin Analytics
        </h1>
        <p className="text-slate-400 text-sm mt-1">
          Monitor system metrics, vector store status, disk allocation, and user query analytics.
        </p>
      </div>

      {/* Stats Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {cardData.map((card, i) => {
          const Icon = card.icon;
          return (
            <div key={i} className="glass-panel p-6 rounded-2xl border border-white/5 flex items-center justify-between">
              <div>
                <span className="text-xs text-slate-500 font-semibold uppercase tracking-wider block">{card.label}</span>
                <span className="text-3xl font-black text-white mt-1.5 block">{card.value}</span>
              </div>
              <div className={`p-4 rounded-xl border ${card.color}`}>
                <Icon size={22} />
              </div>
            </div>
          );
        })}
      </div>

      {/* Disk Space & Database size */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        <div className="glass-panel p-6 rounded-2xl border border-white/5 lg:col-span-1 flex flex-col justify-between">
          <div>
            <h3 className="font-bold text-white text-sm flex items-center gap-2 mb-4">
              <HardDrive size={16} className="text-brand-400" /> Disk space allocation
            </h3>
            <div className="space-y-4">
              <div>
                <div className="flex justify-between text-xs font-semibold text-slate-400 mb-1">
                  <span>Uploads Storage Size</span>
                  <span className="text-white">{stats.system_stats.upload_dir_size_mb} MB</span>
                </div>
              </div>
              <div>
                <div className="flex justify-between text-xs font-semibold text-slate-400 mb-1">
                  <span>Free Disk Space</span>
                  <span className="text-white">{stats.system_stats.free_disk_space_gb} GB</span>
                </div>
              </div>
            </div>
          </div>
          <div className="text-[10px] text-slate-500 border-t border-white/5 pt-3 mt-4 font-semibold uppercase tracking-wider">
            Disk details refer to local machine
          </div>
        </div>

        {/* User Engagement list */}
        <div className="glass-panel p-6 rounded-2xl border border-white/5 lg:col-span-2">
          <h3 className="font-bold text-white text-sm flex items-center gap-2 mb-4">
            <Users size={16} className="text-brand-400" /> User Directory & Activity
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-white/5 text-slate-500 text-[10px] font-bold uppercase tracking-wider">
                  <th className="py-2.5">User Profile</th>
                  <th className="py-2.5">Role</th>
                  <th className="py-2.5">Documents</th>
                  <th className="py-2.5">Queries</th>
                  <th className="py-2.5">Joined Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {stats.system_stats.users_list.map((u) => (
                  <tr key={u.id} className="text-xs text-slate-300 hover:bg-white/5 transition-colors">
                    <td className="py-3 flex items-center gap-2">
                      <Mail size={13} className="text-slate-500" />
                      <span className="font-semibold text-slate-200">{u.email}</span>
                    </td>
                    <td className="py-3">
                      <span className={`px-1.5 py-0.5 rounded text-[10px] uppercase font-bold tracking-wider ${
                        u.role === 'admin' ? 'bg-brand-500/20 text-brand-300' : 'bg-slate-800 text-slate-400'
                      }`}>
                        {u.role}
                      </span>
                    </td>
                    <td className="py-3 font-semibold text-slate-200">{u.document_count}</td>
                    <td className="py-3 font-semibold text-slate-200">{u.query_count}</td>
                    <td className="py-3 text-slate-500 flex items-center gap-1">
                      <Calendar size={12} />
                      <span>{new Date(u.created_at).toLocaleDateString()}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
