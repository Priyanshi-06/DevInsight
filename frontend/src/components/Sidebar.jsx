import { Link, useLocation } from 'react-router-dom';
import {
  LayoutDashboard, MessageSquare, Network, Sparkles, GitPullRequest, ExternalLink, ArrowLeft,
} from 'lucide-react';
import StatusBadge from './StatusBadge';

const NAV_ITEMS = [
  { key: '', label: 'Overview', icon: LayoutDashboard },
  { key: 'chat', label: 'Chat', icon: MessageSquare },
  { key: 'architecture', label: 'Architecture', icon: Network },
  { key: 'recommendations', label: 'Recommendations', icon: Sparkles },
  { key: 'pr-assistant', label: 'PR Assistant', icon: GitPullRequest },
];

export default function Sidebar({ repo, repoId }) {
  const location = useLocation();
  const ready = repo?.status === 'completed';
  const failed = repo?.status === 'failed';

  return (
    <aside className="w-64 shrink-0 border-r border-zinc-800/80 bg-zinc-950/60 backdrop-blur-sm min-h-full flex flex-col">
      <div className="p-4 border-b border-zinc-800/80">
        <Link to="/" className="flex items-center gap-2 text-xs text-zinc-500 hover:text-zinc-300 transition mb-3">
          <ArrowLeft className="h-3.5 w-3.5" />
          All repositories
        </Link>
        {repo ? (
          <>
            <p className="font-mono text-sm font-semibold text-white truncate" title={`${repo.owner}/${repo.name}`}>
              {repo.owner}/{repo.name}
            </p>
            <div className="mt-2 flex items-center justify-between">
              <StatusBadge status={repo.status} />
              <a
                href={repo.github_url}
                target="_blank"
                rel="noreferrer"
                className="text-zinc-500 hover:text-[#9c6570] transition"
                title="View on GitHub"
              >
                <ExternalLink className="h-3.5 w-3.5" />
              </a>
            </div>
          </>
        ) : (
          <div className="h-10 animate-pulse rounded-md bg-zinc-800/60" />
        )}
      </div>

      <nav className="flex-1 p-3 space-y-1">
        {NAV_ITEMS.map((item) => {
          const path = item.key ? `/repos/${repoId}/${item.key}` : `/repos/${repoId}`;
          const active = location.pathname === path;
          const Icon = item.icon;
          return (
            <Link
              key={item.key}
              to={path}
              className={`group flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition ${
                active
                  ? 'accent-gradient text-white shadow-lg shadow-[#6b2c35]/20'
                  : 'text-zinc-400 hover:text-white hover:bg-zinc-800/60'
              }`}
            >
              <Icon className={`h-4 w-4 shrink-0 ${active ? 'text-white' : 'text-zinc-500 group-hover:text-[#9c6570]'}`} />
              <span className="flex-1">{item.label}</span>
              {item.key && !ready && !failed && (
                <span className="h-1.5 w-1.5 rounded-full bg-amber-400 animate-pulse" title="Indexing…" />
              )}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
