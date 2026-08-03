import { useEffect, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  LayoutDashboard, MessageSquare, Network, Sparkles, GitPullRequest, FlaskConical,
  ExternalLink, ArrowLeft, PanelLeftClose, PanelLeftOpen,
} from 'lucide-react';
import StatusBadge from './StatusBadge';

const NAV_ITEMS = [
  { key: '', label: 'Overview', icon: LayoutDashboard },
  { key: 'chat', label: 'Chat', icon: MessageSquare },
  { key: 'architecture', label: 'Architecture', icon: Network },
  { key: 'recommendations', label: 'Recommendations', icon: Sparkles },
  { key: 'pr-assistant', label: 'PR Assistant', icon: GitPullRequest },
  { key: 'tests', label: 'Test Generator', icon: FlaskConical },
];

const COLLAPSE_KEY = 'repo-sidebar-collapsed';

export default function Sidebar({ repo, repoId }) {
  const location = useLocation();
  const ready = repo?.status === 'completed';
  const failed = repo?.status === 'failed';
  const [collapsed, setCollapsed] = useState(() => localStorage.getItem(COLLAPSE_KEY) === 'true');

  useEffect(() => {
    localStorage.setItem(COLLAPSE_KEY, String(collapsed));
  }, [collapsed]);

  return (
    <aside
      className={`shrink-0 border-r border-zinc-800/80 bg-zinc-950/60 backdrop-blur-sm min-h-full flex flex-col transition-[width] duration-150 ${
        collapsed ? 'w-14' : 'w-64'
      }`}
    >
      <div className={`p-3 border-b border-zinc-800/80 ${collapsed ? 'flex flex-col items-center gap-2' : ''}`}>
        <div className={`flex items-center ${collapsed ? '' : 'justify-between mb-3'}`}>
          {!collapsed && (
            <Link to="/" className="flex items-center gap-2 text-xs text-zinc-500 hover:text-zinc-300 transition">
              <ArrowLeft className="h-3.5 w-3.5" />
              All repositories
            </Link>
          )}
          <button
            type="button"
            onClick={() => setCollapsed((c) => !c)}
            title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            className="text-zinc-500 hover:text-white transition shrink-0"
          >
            {collapsed ? <PanelLeftOpen className="h-4 w-4" /> : <PanelLeftClose className="h-3.5 w-3.5" />}
          </button>
        </div>
        {collapsed && (
          <Link to="/" title="All repositories" className="text-zinc-500 hover:text-zinc-300 transition">
            <ArrowLeft className="h-3.5 w-3.5" />
          </Link>
        )}
        {!collapsed &&
          (repo ? (
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
          ))}
      </div>

      <nav className={`flex-1 p-2 space-y-1 ${collapsed ? '' : 'p-3'}`}>
        {NAV_ITEMS.map((item) => {
          const path = item.key ? `/repos/${repoId}/${item.key}` : `/repos/${repoId}`;
          const active = location.pathname === path;
          const Icon = item.icon;
          return (
            <Link
              key={item.key}
              to={path}
              title={collapsed ? item.label : undefined}
              className={`group flex items-center rounded-lg text-sm transition ${
                collapsed ? 'justify-center px-0 py-2.5' : 'gap-3 px-3 py-2'
              } ${
                active
                  ? 'accent-gradient text-white shadow-lg shadow-[#6b2c35]/20'
                  : 'text-zinc-400 hover:text-white hover:bg-zinc-800/60'
              }`}
            >
              <Icon className={`h-4 w-4 shrink-0 ${active ? 'text-white' : 'text-zinc-500 group-hover:text-[#9c6570]'}`} />
              {!collapsed && <span className="flex-1">{item.label}</span>}
              {!collapsed && item.key && !ready && !failed && (
                <span className="h-1.5 w-1.5 rounded-full bg-amber-400 animate-pulse" title="Indexing…" />
              )}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
