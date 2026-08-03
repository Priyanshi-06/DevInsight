import { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { LogIn } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import AuthLayout from '../components/AuthLayout';

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');
    setSubmitting(true);
    try {
      await login(email.trim(), password);
      navigate(location.state?.from?.pathname || '/', { replace: true });
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AuthLayout>
      <h1 className="text-2xl font-bold text-white text-center mb-1.5">Welcome back</h1>
      <p className="text-sm text-zinc-500 text-center mb-8">Sign in to keep analyzing your repositories.</p>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-xs font-semibold text-zinc-400 mb-2">Email</label>
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full rounded-lg border border-zinc-700 bg-black px-3.5 py-3 text-sm text-white placeholder:text-zinc-600 focus:outline-none focus:ring-2 focus:ring-[#6b2c35] focus:border-transparent"
            placeholder="you@example.com"
          />
        </div>
        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="block text-xs font-semibold text-zinc-400">Password</label>
            <Link to="/forgot-password" className="text-xs text-[#c99aa1] hover:text-white transition">
              Forgot password?
            </Link>
          </div>
          <input
            type="password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full rounded-lg border border-zinc-700 bg-black px-3.5 py-3 text-sm text-white placeholder:text-zinc-600 focus:outline-none focus:ring-2 focus:ring-[#6b2c35] focus:border-transparent"
            placeholder="••••••••"
          />
        </div>
        {error && (
          <p className="text-sm text-red-400 bg-red-500/10 border border-red-500/30 rounded-lg px-3 py-2.5">
            {error}
          </p>
        )}
        <button
          type="submit"
          disabled={submitting}
          className="w-full mt-2 px-4 py-3 rounded-lg accent-gradient text-white text-sm font-semibold hover:opacity-90 disabled:opacity-50 transition inline-flex items-center justify-center gap-2"
        >
          <LogIn className="h-4 w-4" />
          {submitting ? 'Signing in…' : 'Sign in'}
        </button>
      </form>

      <p className="mt-7 text-sm text-zinc-500 text-center">
        Don't have an account?{' '}
        <Link to="/signup" className="text-[#c99aa1] hover:text-white transition font-semibold">
          Sign up
        </Link>
      </p>
    </AuthLayout>
  );
}
