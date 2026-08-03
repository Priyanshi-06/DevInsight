import { useAuth } from '../context/AuthContext';
import Home from '../pages/Home';
import Landing from '../pages/Landing';

// "/" is public: logged-out visitors see the marketing landing page, logged-in users see the
// existing repo dashboard — unchanged from before this page existed.
export default function RootRoute() {
  const { user, loading } = useAuth();

  if (loading) {
    return <div className="max-w-5xl mx-auto px-4 py-10 text-sm text-zinc-500">Loading…</div>;
  }

  return user ? <Home /> : <Landing />;
}
