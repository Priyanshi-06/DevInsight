import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { MessageSquare, Network, Sparkles, GitPullRequest, FlaskConical, ArrowRight } from 'lucide-react';
import { api } from '../api/client';
import StatusBadge from '../components/StatusBadge';

const FEATURES = [
  { icon: MessageSquare, label: 'Chat with citations' },
  { icon: Network, label: 'Architecture diagrams' },
  { icon: Sparkles, label: 'Contribution picks' },
  { icon: GitPullRequest, label: 'PR draft assistant' },
  { icon: FlaskConical, label: 'Test case generator' },
];

export default function Home() {
  const [url, setUrl] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [repos, setRepos] = useState([]);
  const [loadingRepos, setLoadingRepos] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    api
      .listRepos()
      .then(setRepos)
      .catch(() => {})
      .finally(() => setLoadingRepos(false));
  }, []);

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');
    if (!url.trim()) return;
    setSubmitting(true);
    try {
      const repo = await api.createRepo(url.trim());
      navigate(`/repos/${repo.id}`);
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="max-w-3xl mx-auto px-4 py-16">
      <div className="text-center mb-8">
        <h1 className="text-4xl sm:text-5xl font-bold tracking-tight text-white">
          Understand any <span className="accent-text-gradient">GitHub repo</span>, instantly
        </h1>
        <p className="mt-4 text-zinc-400 max-w-xl mx-auto">
          Paste a public GitHub repository URL. We'll index it and let you ask questions, see how
          it's built, find beginner-friendly issues, and draft your first PR.
        </p>
      </div>

      <div className="flex flex-wrap justify-center gap-2 mb-10">
        {FEATURES.map((f) => {
          const Icon = f.icon;
          return (
            <span
              key={f.label}
              className="inline-flex items-center gap-1.5 rounded-full border border-zinc-800 bg-zinc-900/60 px-3 py-1.5 text-xs text-zinc-400"
            >
              <Icon className="h-3.5 w-3.5 text-[#9c6570]" />
              {f.label}
            </span>
          );
        })}
      </div>

      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          type="text"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://github.com/owner/repo"
          className="flex-1 rounded-lg border border-zinc-800 bg-zinc-900 px-4 py-3 text-sm text-white placeholder:text-zinc-600 focus:outline-none focus:ring-2 focus:ring-[#6b2c35] focus:border-transparent"
        />
        <button
          type="submit"
          disabled={submitting}
          className="px-5 py-3 rounded-lg accent-gradient text-white text-sm font-medium hover:opacity-90 disabled:opacity-50 transition shadow-lg shadow-[#6b2c35]/20"
        >
          {submitting ? 'Starting…' : 'Analyze'}
        </button>
      </form>
      {error && <p className="mt-2 text-sm text-red-400">{error}</p>}

      <div className="mt-14">
        <h2 className="text-sm font-semibold text-zinc-500 uppercase tracking-wide mb-3">
          Previously analyzed
        </h2>
        {loadingRepos ? (
          <p className="text-sm text-zinc-500">Loading…</p>
        ) : repos.length === 0 ? (
          <p className="text-sm text-zinc-500">No repositories yet — analyze one above.</p>
        ) : (
          <ul className="divide-y divide-zinc-800 rounded-xl border border-zinc-800 bg-zinc-900/60 overflow-hidden">
            {repos.map((repo) => (
              <li
                key={repo.id}
                onClick={() => navigate(`/repos/${repo.id}`)}
                className="flex items-center justify-between px-4 py-3 hover:bg-zinc-800/50 cursor-pointer transition group"
              >
                <div className="min-w-0">
                  <p className="font-medium text-white truncate">
                    {repo.owner}/{repo.name}
                  </p>
                  <p className="text-xs text-zinc-500 truncate">{repo.description || 'No description'}</p>
                </div>
                <div className="flex items-center gap-3 shrink-0 ml-3">
                  <StatusBadge status={repo.status} />
                  <ArrowRight className="h-4 w-4 text-zinc-600 group-hover:text-[#9c6570] group-hover:translate-x-0.5 transition" />
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
