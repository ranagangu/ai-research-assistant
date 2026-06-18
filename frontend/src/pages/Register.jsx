import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Lock, Mail, Loader2, AlertCircle, Bot, CheckCircle } from 'lucide-react';

export default function Register() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const { register } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    
    if (password.length < 6) {
      setError('Password must be at least 6 characters long.');
      return;
    }
    
    if (password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    setSubmitting(true);
    try {
      await register(email, password);
      setSuccess(true);
      setTimeout(() => {
        navigate('/login');
      }, 2000);
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || 'Registration failed. Email may already be in use.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="relative min-h-screen flex items-center justify-center bg-[#030712] px-4 overflow-hidden">
      {/* Decorative Glow Elements */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-glow-purple rounded-full blur-3xl glow-animation pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-glow-blue rounded-full blur-3xl glow-animation pointer-events-none" />

      <div className="w-full max-w-md glass-panel p-8 rounded-2xl relative z-10">
        <div className="flex flex-col items-center mb-8">
          <div className="p-3 bg-brand-600/20 text-brand-400 rounded-2xl mb-4 border border-brand-500/20">
            <Bot size={36} />
          </div>
          <h1 className="text-2xl font-bold text-white text-center">Create Account</h1>
          <p className="text-slate-400 text-sm mt-1">Get started with your AI Research Assistant</p>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-rose-500/10 border border-rose-500/20 text-rose-300 rounded-xl text-sm flex items-center gap-2">
            <AlertCircle size={18} className="shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {success && (
          <div className="mb-6 p-4 bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 rounded-xl text-sm flex items-center gap-2">
            <CheckCircle size={18} className="shrink-0" />
            <span>Account created successfully! Redirecting to login...</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5">
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider">Email Address</label>
            <div className="relative">
              <Mail className="absolute left-3.5 top-3.5 text-slate-500" size={18} />
              <input
                type="email"
                required
                className="w-full glass-input pl-11"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                disabled={success}
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider">Password</label>
            <div className="relative">
              <Lock className="absolute left-3.5 top-3.5 text-slate-500" size={18} />
              <input
                type="password"
                required
                className="w-full glass-input pl-11"
                placeholder="Minimum 6 characters"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                disabled={success}
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider">Confirm Password</label>
            <div className="relative">
              <Lock className="absolute left-3.5 top-3.5 text-slate-500" size={18} />
              <input
                type="password"
                required
                className="w-full glass-input pl-11"
                placeholder="Re-enter password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                disabled={success}
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={submitting || success}
            className="w-full glass-btn-primary mt-4 disabled:opacity-55 disabled:pointer-events-none"
          >
            {submitting ? (
              <>
                <Loader2 size={18} className="animate-spin" />
                Registering...
              </>
            ) : (
              'Register'
            )}
          </button>
        </form>

        <div className="mt-8 text-center text-sm text-slate-400">
          Already have an account?{' '}
          <Link to="/login" className="text-brand-400 hover:text-brand-300 font-semibold transition-colors">
            Sign In
          </Link>
        </div>
      </div>
    </div>
  );
}
