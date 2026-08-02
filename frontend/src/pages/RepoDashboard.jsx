import { Link, useOutletContext } from 'react-router-dom';
import { MessageSquare, Network, Sparkles, GitPullRequest, ArrowRight } from 'lucide-react';
import FileTree from '../components/FileTree';

const FEATURES = [
  {
    key: 'chat',
    icon: MessageSquare,
    title: 'Chat',
    description: 'Ask questions about the codebase and get answers grounded in the actual source, with file/line citations.',
  },
  {
    key: 'architecture',
    icon: Network,
    title: 'Architecture',
    description: 'A system overview plus a UML-style class diagram for every module — see how the codebase actually fits together.',
  },
  {
    key: 'recommendations',
    icon: Sparkles,
    title: 'Recommendations',
    description: 'Real open GitHub issues, ranked for beginners and summarized with the relevant code already found for you.',
  },
  {
    key: 'pr-assistant',
    icon: GitPullRequest,
    title: 'PR Assistant',
    description: 'Turn an issue or task into a draft diff — the AI proposes a change, you review before anything goes anywhere.',
  },
];

export default function RepoDashboard() {
  const { repo } = useOutletContext();

  if (!repo) {
    return <div className="max-w-5xl mx-auto px-4 py-10 text-sm text-zinc-500">Loading…</div>;
  }

  const inProgress = !['completed', 'failed'].includes(repo.status);
  const ready = repo.status === 'completed';

  return (
    <div className="max-w-5xl mx-auto px-4 py-10">
      <div className="flex items-start justify-between mb-2">
        <div>
          <h1 className="text-2xl font-bold text-white">
            {repo.owner}/{repo.name}
          </h1>
          <p className="text-sm text-zinc-500 mt-1">{repo.description || 'No description'}</p>
        </div>
      </div>

      <div className="flex gap-4 text-xs text-zinc-500 mb-8">
        {repo.language && <span>Language: {repo.language}</span>}
        {typeof repo.stars === 'number' && <span>★ {repo.stars}</span>}
        <a href={repo.github_url} target="_blank" rel="noreferrer" className="text-[#9c6570] hover:text-[#c99aa1] hover:underline">
          View on GitHub
        </a>
      </div>

      {inProgress && (
        <div className="mb-8 rounded-lg border border-amber-500/20 bg-amber-500/10 px-4 py-3 text-sm text-amber-300">
          Indexing in progress ({repo.status})… this page updates automatically, and every feature below unlocks once it's done.
        </div>
      )}
      {repo.status === 'failed' && (
        <div className="mb-8 rounded-lg border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm text-red-300">
          Indexing failed: {repo.error_message || 'Unknown error'}
        </div>
      )}

      <div className="grid sm:grid-cols-2 gap-4 mb-10">
        {FEATURES.map((feature) => {
          const Icon = feature.icon;
          const card = (
            <div
              className={`group h-full rounded-xl border p-5 transition ${
                ready
                  ? 'border-zinc-800 bg-zinc-900/60 hover:border-[#6b2c35]/50 hover:bg-zinc-900'
                  : 'border-zinc-800/60 bg-zinc-900/30 opacity-60'
              }`}
            >
              <div className="flex items-center justify-between mb-3">
                <span className="inline-flex h-9 w-9 items-center justify-center rounded-lg bg-zinc-800 text-[#9c6570] group-hover:accent-gradient group-hover:text-white transition">
                  <Icon className="h-4.5 w-4.5" />
                </span>
                {ready && (
                  <ArrowRight className="h-4 w-4 text-zinc-600 group-hover:text-[#9c6570] group-hover:translate-x-0.5 transition" />
                )}
              </div>
              <h3 className="font-semibold text-white mb-1">{feature.title}</h3>
              <p className="text-sm text-zinc-500 leading-relaxed">{feature.description}</p>
              {!ready && <p className="text-xs text-amber-400 mt-2">Available once indexing completes</p>}
            </div>
          );
          return ready ? (
            <Link key={feature.key} to={`/repos/${repo.id}/${feature.key}`}>
              {card}
            </Link>
          ) : (
            <div key={feature.key}>{card}</div>
          );
        })}
      </div>

      <div>
        <h2 className="text-sm font-semibold text-zinc-500 uppercase tracking-wide mb-3">
          Indexed files {repo.file_tree ? `(${repo.file_tree.length})` : ''}
        </h2>
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-4">
          <FileTree paths={repo.file_tree} />
        </div>
      </div>
    </div>
  );
}
