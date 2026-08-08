import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Check, KeyRound, Mail, ShieldCheck } from 'lucide-react';
import { api } from '../api/client';
import AuthLayout from '../components/AuthLayout';
import PasswordInput from '../components/PasswordInput';

export default function ForgotPassword() {
  const navigate = useNavigate();
  const [step, setStep] = useState('email'); // 'email' | 'otp' | 'password' | 'done'
  const [email, setEmail] = useState('');
  const [otp, setOtp] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [resending, setResending] = useState(false);

  async function handleEmailSubmit(e) {
    e.preventDefault();
    setError('');
    setSubmitting(true);
    try {
      await api.forgotPassword(email.trim());
      setStep('otp');
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  async function handleResend() {
    setResending(true);
    setError('');
    try {
      await api.forgotPassword(email.trim());
    } catch (err) {
      setError(err.message);
    } finally {
      setResending(false);
    }
  }

  async function handleOtpSubmit(e) {
    e.preventDefault();
    setError('');
    setSubmitting(true);
    try {
      await api.verifyOtp({ email: email.trim(), otp: otp.trim() });
      setStep('password');
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  async function handlePasswordSubmit(e) {
    e.preventDefault();
    setError('');
    if (password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }
    setSubmitting(true);
    try {
      await api.resetPassword({ email: email.trim(), otp: otp.trim(), password });
      setStep('done');
      setTimeout(() => navigate('/login', { replace: true }), 2000);
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  if (step === 'done') {
    return (
      <AuthLayout>
        <div className="flex justify-center mb-5">
          <span className="inline-flex h-12 w-12 items-center justify-center rounded-xl bg-emerald-500/15 text-emerald-400">
            <Check className="h-5 w-5" />
          </span>
        </div>
        <h1 className="text-2xl font-bold text-white text-center mb-2">Password reset</h1>
        <p className="text-sm text-zinc-500 text-center">Redirecting you to sign in…</p>
      </AuthLayout>
    );
  }

  if (step === 'password') {
    return (
      <AuthLayout>
        <div className="flex justify-center mb-5">
          <span className="inline-flex h-12 w-12 items-center justify-center rounded-xl bg-emerald-500/15 text-emerald-400">
            <ShieldCheck className="h-5 w-5" />
          </span>
        </div>
        <h1 className="text-2xl font-bold text-white text-center mb-1.5">Code verified</h1>
        <p className="text-sm text-zinc-500 text-center mb-8">Choose a new password for your account.</p>

        <form onSubmit={handlePasswordSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-zinc-400 mb-2">New password</label>
            <PasswordInput
              required
              minLength={8}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="At least 8 characters"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-zinc-400 mb-2">Confirm new password</label>
            <PasswordInput
              required
              minLength={8}
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="Re-enter your new password"
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
            <KeyRound className="h-4 w-4" />
            {submitting ? 'Resetting…' : 'Reset password'}
          </button>
        </form>
      </AuthLayout>
    );
  }

  if (step === 'otp') {
    return (
      <AuthLayout>
        <h1 className="text-2xl font-bold text-white text-center mb-1.5">Enter your code</h1>
        <p className="text-sm text-zinc-500 text-center mb-8 leading-relaxed">
          We sent a 6-digit code to
          <br />
          <span className="text-zinc-300 font-semibold">{email}</span>
        </p>

        <form onSubmit={handleOtpSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-zinc-400 mb-2">Reset code</label>
            <input
              type="text"
              inputMode="numeric"
              required
              maxLength={6}
              value={otp}
              onChange={(e) => setOtp(e.target.value.replace(/\D/g, ''))}
              className="w-full rounded-lg border border-zinc-700 bg-black px-3.5 py-3 text-center text-lg tracking-[0.5em] text-white placeholder:text-zinc-600 placeholder:tracking-normal focus:outline-none focus:ring-2 focus:ring-[#6b2c35] focus:border-transparent"
              placeholder="000000"
            />
          </div>
          {error && (
            <p className="text-sm text-red-400 bg-red-500/10 border border-red-500/30 rounded-lg px-3 py-2.5">
              {error}
            </p>
          )}
          <button
            type="submit"
            disabled={submitting || otp.length !== 6}
            className="w-full mt-2 px-4 py-3 rounded-lg accent-gradient text-white text-sm font-semibold hover:opacity-90 disabled:opacity-50 transition inline-flex items-center justify-center gap-2"
          >
            <ShieldCheck className="h-4 w-4" />
            {submitting ? 'Verifying…' : 'Verify code'}
          </button>
        </form>

        <div className="mt-7 flex items-center justify-between text-sm">
          <button
            type="button"
            onClick={() => {
              setStep('email');
              setOtp('');
              setError('');
            }}
            className="text-zinc-500 hover:text-white transition"
          >
            Use a different email
          </button>
          <button
            type="button"
            onClick={handleResend}
            disabled={resending}
            className="text-[#c99aa1] hover:text-white transition font-semibold disabled:opacity-50"
          >
            {resending ? 'Sending…' : 'Resend code'}
          </button>
        </div>
      </AuthLayout>
    );
  }

  return (
    <AuthLayout>
      <h1 className="text-2xl font-bold text-white text-center mb-1.5">Reset your password</h1>
      <p className="text-sm text-zinc-500 text-center mb-8 leading-relaxed">
        Enter your email and we'll send you a 6-digit code.
      </p>

      <form onSubmit={handleEmailSubmit} className="space-y-4">
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
          <Mail className="h-4 w-4" />
          {submitting ? 'Sending…' : 'Send reset code'}
        </button>
      </form>

      <p className="mt-7 text-sm text-zinc-500 text-center">
        <Link to="/login" className="text-[#c99aa1] hover:text-white transition font-semibold">
          Back to sign in
        </Link>
      </p>
    </AuthLayout>
  );
}
