import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Code2, LogOut } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

// Auth pages render their own standalone centered-card layout (see AuthLayout) with no
// persistent header, so the global nav stays out of the way there.
const AUTH_ROUTES = ['/login', '/signup', '/forgot-password'];

export default function TopBar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  if (AUTH_ROUTES.includes(location.pathname)) {
    return null;
  }

  function handleLogout() {
    logout();
    navigate('/login');
  }

  return (
    <header className="h-14 shrink-0 border-b border-zinc-800/80 bg-black/70 backdrop-blur-md sticky top-0 z-20">
      <div className="h-full px-4 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2 font-semibold text-white">
          <span className="accent-gradient inline-flex h-7 w-7 items-center justify-center rounded-lg text-white shadow-lg shadow-[#6b2c35]/30">
            <Code2 className="h-4 w-4" />
          </span>
          <span className="tracking-tight">DevInsight</span>
        </Link>
        {user ? (
          <div className="flex items-center gap-3">
            <span className="text-xs text-zinc-500 hidden sm:inline">{user.email}</span>
            <button
              onClick={handleLogout}
              className="flex items-center gap-1.5 text-xs text-zinc-400 hover:text-white px-2.5 py-1.5 rounded-md hover:bg-zinc-800/60 transition"
            >
              <LogOut className="h-3.5 w-3.5" />
              Log out
            </button>
          </div>
        ) : (
          <div className="flex items-center gap-4">
            <Link to="/login" className="text-xs font-medium text-zinc-400 hover:text-white transition">
              Sign in
            </Link>
            <Link
              to="/signup"
              className="px-3 py-1.5 rounded-md accent-gradient text-white text-xs font-semibold hover:opacity-90 transition"
            >
              Get started
            </Link>
          </div>
        )}
      </div>
    </header>
  );
}
