import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { MessageSquare, Network, Sparkles, GitPullRequest, FlaskConical, ArrowRight, Trash2 } from 'lucide-react';
import { api } from '../api/client';
import StatusBadge from '../components/StatusBadge';

const FEATURES = [
  { icon: MessageSquare, label: 'Chat with citations' },
  { icon: Network, label: 'Architecture diagrams' },
  { icon: Sparkles, label: 'Contribution picks' },
  { icon: GitPullRequest, label: 'PR draft assistant' },
  { icon: FlaskConical, label: 'Test case generator' },
];

// Common full-stack folder pairings — if the user picks one side, it's worth pointing out the
// other exists too, since indexing just "frontend" of an app that also has a "backend" folder
// would leave chat/architecture blind to half the actual system.
const COMPLEMENTARY_FOLDER_PAIRS = [
  ['frontend', 'backend'],
  ['client', 'server'],
  ['web', 'api'],
  ['ui', 'api'],
  ['app', 'server'],
];

function findComplementSuggestion(selectedFolders, availableFolders) {
  const selectedLower = new Set(selectedFolders.map((f) => f.toLowerCase()));
  for (const [a, b] of COMPLEMENTARY_FOLDER_PAIRS) {
    const missing = selectedLower.has(a) ? b : selectedLower.has(b) ? a : null;
    if (!missing) continue;
    const match = availableFolders.find((f) => f.path.toLowerCase() === missing);
    if (match && !selectedLower.has(match.path.toLowerCase())) return match.path;
  }
  return null;
}

export default function Home() {
  const [url, setUrl] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [repos, setRepos] = useState([]);
  const [loadingRepos, setLoadingRepos] = useState(true);
  // Set only when a submitted repo is too large to index whole — holds the folder options and
  // which URL they belong to, so "Continue" knows what to resubmit.
  const [folderPrompt, setFolderPrompt] = useState(null);
  const [selectedFolders, setSelectedFolders] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    api
      .listRepos()
      .then(setRepos)
      .catch(() => {})
      .finally(() => setLoadingRepos(false));
  }, []);

  async function handleDeleteRepo(e, repo) {
    e.stopPropagation();
    if (!window.confirm(`Delete ${repo.owner}/${repo.name}? This removes its analysis and chat history.`)) {
      return;
    }
    try {
      await api.deleteRepo(repo.id);
      setRepos((prev) => prev.filter((r) => r.id !== repo.id));
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');
    if (!url.trim()) return;
    setSubmitting(true);
    try {
      const result = await api.createRepo(url.trim());
      if (result.needs_folder_selection) {
        setFolderPrompt({ url: url.trim(), ...result });
        setSelectedFolders([]);
      } else {
        navigate(`/repos/${result.id}`);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  function toggleFolder(path) {
    setSelectedFolders((prev) =>
      prev.includes(path) ? prev.filter((p) => p !== path) : [...prev, path],
    );
  }

  async function handleConfirmFolders() {
    if (selectedFolders.length === 0) return;
    setError('');
    setSubmitting(true);
    try {
      const result = await api.createRepo(folderPrompt.url, selectedFolders);
      if (result.needs_folder_selection) {
        // A chosen folder turned out to still be too large on its own — drill in one level
        // further instead of indexing it whole.
        setFolderPrompt({ url: folderPrompt.url, ...result });
        setSelectedFolders([]);
      } else {
        navigate(`/repos/${result.id}`);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  function cancelFolderPrompt() {
    setFolderPrompt(null);
    setSelectedFolders([]);
  }

  const complementSuggestion = folderPrompt
    ? findComplementSuggestion(selectedFolders, folderPrompt.folders)
    : null;

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

      {folderPrompt ? (
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-5">
          <p className="text-sm text-white font-medium">
            {folderPrompt.narrowing_within
              ? `${folderPrompt.narrowing_within.join(', ')} is still large`
              : folderPrompt.url.replace('https://github.com/', '')}{' '}
            ({folderPrompt.file_count} files, {(folderPrompt.size_kb / 1024).toFixed(1)}MB)
          </p>
          <p className="mt-1 text-xs text-zinc-500">
            {folderPrompt.narrowing_within
              ? 'Pick more specific subfolders to narrow it down further.'
              : 'Pick one or more folders to index instead of the whole repo — keeps indexing fast and reliable.'}
          </p>
          <div className="mt-4 grid grid-cols-2 sm:grid-cols-3 gap-2">
            {folderPrompt.folders.map((folder) => {
              const checked = selectedFolders.includes(folder.path);
              return (
                <label
                  key={folder.path}
                  className={`flex items-center justify-between gap-2 rounded-lg border px-3 py-2 text-sm cursor-pointer transition ${
                    checked
                      ? 'border-[#6b2c35] bg-[#6b2c35]/10 text-white'
                      : 'border-zinc-800 bg-zinc-900 text-zinc-400 hover:border-zinc-700'
                  }`}
                >
                  <span className="flex items-center gap-2 min-w-0">
                    <input
                      type="checkbox"
                      checked={checked}
                      onChange={() => toggleFolder(folder.path)}
                      className="accent-[#6b2c35]"
                    />
                    <span className="truncate">{folder.path}</span>
                  </span>
                  <span className="text-xs text-zinc-600 shrink-0">{folder.file_count}</span>
                </label>
              );
            })}
          </div>
          {complementSuggestion && (
            <div className="mt-3 flex items-center justify-between gap-3 rounded-lg border border-[#6b2c35]/40 bg-[#6b2c35]/10 px-3 py-2 text-xs text-zinc-300">
              <span>
                Also select <span className="text-white font-medium">{complementSuggestion}</span>? Indexing
                just one side of a full-stack app means chat and architecture won't see the other half.
              </span>
              <button
                type="button"
                onClick={() => toggleFolder(complementSuggestion)}
                className="shrink-0 px-2.5 py-1 rounded-md bg-[#6b2c35] text-white text-xs font-medium hover:opacity-90 transition"
              >
                Add
              </button>
            </div>
          )}
          <div className="mt-4 flex gap-2">
            <button
              type="button"
              onClick={handleConfirmFolders}
              disabled={submitting || selectedFolders.length === 0}
              className="px-4 py-2 rounded-lg accent-gradient text-white text-sm font-medium hover:opacity-90 disabled:opacity-50 transition"
            >
              {submitting ? 'Starting…' : `Analyze ${selectedFolders.length || ''} folder${selectedFolders.length === 1 ? '' : 's'}`.trim()}
            </button>
            <button
              type="button"
              onClick={cancelFolderPrompt}
              className="px-4 py-2 rounded-lg border border-zinc-800 text-zinc-400 text-sm hover:text-white hover:border-zinc-700 transition"
            >
              Cancel
            </button>
          </div>
        </div>
      ) : (
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
      )}
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
                  <span
                    role="button"
                    tabIndex={0}
                    onClick={(e) => handleDeleteRepo(e, repo)}
                    title="Delete analysis"
                    className="opacity-0 group-hover:opacity-100 text-zinc-600 hover:text-red-400 transition"
                  >
                    <Trash2 className="h-4 w-4" />
                  </span>
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
