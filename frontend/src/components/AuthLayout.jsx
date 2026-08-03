import { Link } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';

export default function AuthLayout({ children }) {
  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-12 relative bg-black">
      <div
        className="pointer-events-none fixed inset-0 z-0 opacity-40"
        style={{
          backgroundImage:
            'linear-gradient(rgba(255,255,255,0.035) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.035) 1px, transparent 1px)',
          backgroundSize: '64px 64px',
        }}
      />
      <Link
        to="/"
        className="absolute top-6 left-6 z-10 inline-flex items-center gap-1.5 text-xs font-medium text-zinc-500 hover:text-white transition"
      >
        <ArrowLeft className="h-3.5 w-3.5" />
        Back
      </Link>
      <div className="relative z-10 w-full max-w-[420px]">
        <div className="rounded-2xl border border-zinc-800 bg-zinc-900/60 p-10 shadow-2xl shadow-black/50">
          {children}
        </div>
      </div>
    </div>
  );
}
