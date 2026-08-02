import { useEffect, useState } from 'react';
import { useParams, useSearchParams } from 'react-router-dom';
import { ChevronDown, ChevronRight, Wand2 } from 'lucide-react';
import { api } from '../api/client';
import DiffViewer from '../components/DiffViewer';

export default function PrAssistant() {
  const { id } = useParams();
  const [searchParams] = useSearchParams();
  const [issueNumber, setIssueNumber] = useState(searchParams.get('issue') || '');
  const [taskDescription, setTaskDescription] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [drafts, setDrafts] = useState([]);
  const [loadingHistory, setLoadingHistory] = useState(true);
  const [expandedId, setExpandedId] = useState(null);

  useEffect(() => {
    api
      .listPrDrafts(id)
      .then((data) => setDrafts(data.drafts || []))
      .catch(() => {})
      .finally(() => setLoadingHistory(false));
  }, [id]);

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');
    if (!issueNumber && !taskDescription.trim()) {
      setError('Provide an issue number or describe a task.');
      return;
    }
    if (issueNumber && (!Number.isInteger(Number(issueNumber)) || Number(issueNumber) < 1)) {
      setError('Issue number must be a positive whole number.');
      return;
    }
    setSubmitting(true);
    try {
      const draft = await api.createPrDraft(id, {
        issueNumber: issueNumber ? Number(issueNumber) : null,
        taskDescription: taskDescription.trim(),
      });
      setDrafts((prev) => [draft, ...prev]);
      setExpandedId(draft.id);
      setTaskDescription('');
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-10">
      <h1 className="text-xl font-semibold text-white mb-2">PR Assistant</h1>
      <p className="text-sm text-zinc-500 mb-6">
        The AI proposes a draft change for you to review — nothing is pushed to GitHub automatically.
      </p>

      <form onSubmit={handleSubmit} className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-4 mb-8 space-y-3">
        <div>
          <label className="block text-xs font-medium text-zinc-500 mb-1">GitHub issue number (optional)</label>
          <input
            type="number"
            min="1"
            step="1"
            value={issueNumber}
            onChange={(e) => setIssueNumber(e.target.value)}
            placeholder="e.g. 42"
            className="w-40 rounded-lg border border-zinc-800 bg-black px-3 py-2 text-sm text-white placeholder:text-zinc-600 focus:outline-none focus:ring-2 focus:ring-[#6b2c35] focus:border-transparent"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-zinc-500 mb-1">
            Or describe a task {issueNumber && '(overrides issue number if filled in)'}
          </label>
          <textarea
            value={taskDescription}
            onChange={(e) => setTaskDescription(e.target.value)}
            rows={3}
            placeholder="e.g. Add input validation to the signup form"
            className="w-full rounded-lg border border-zinc-800 bg-black px-3 py-2 text-sm text-white placeholder:text-zinc-600 focus:outline-none focus:ring-2 focus:ring-[#6b2c35] focus:border-transparent"
          />
        </div>
        {error && <p className="text-sm text-red-400">{error}</p>}
        <button
          type="submit"
          disabled={submitting}
          className="px-4 py-2 rounded-lg accent-gradient text-white text-sm font-medium hover:opacity-90 disabled:opacity-50 transition inline-flex items-center gap-2"
        >
          <Wand2 className="h-4 w-4" />
          {submitting ? 'Drafting… (this can take a minute)' : 'Generate PR draft'}
        </button>
      </form>

      <h2 className="text-sm font-semibold text-zinc-500 uppercase tracking-wide mb-3">Drafts</h2>
      {loadingHistory ? (
        <p className="text-sm text-zinc-500">Loading…</p>
      ) : drafts.length === 0 ? (
        <p className="text-sm text-zinc-500">No drafts yet.</p>
      ) : (
        <div className="space-y-3">
          {drafts.map((draft) => {
            const isOpen = expandedId === draft.id;
            return (
              <div key={draft.id} className="rounded-xl border border-zinc-800 bg-zinc-900/60 overflow-hidden">
                <button
                  type="button"
                  onClick={() => setExpandedId(isOpen ? null : draft.id)}
                  className="w-full flex items-center justify-between gap-3 p-4 text-left hover:bg-zinc-800/40 transition"
                >
                  <div className="min-w-0">
                    <h3 className="font-medium text-white truncate">{draft.pr_title || draft.target_file}</h3>
                    <p className="text-xs font-mono text-zinc-500 mt-0.5 truncate">
                      branch: {draft.branch_name || 'n/a'} · file: {draft.target_file}
                    </p>
                  </div>
                  <div className="flex items-center gap-3 shrink-0">
                    {draft.issue_number && <span className="text-xs text-zinc-500">issue #{draft.issue_number}</span>}
                    {isOpen ? (
                      <ChevronDown className="h-4 w-4 text-zinc-500" />
                    ) : (
                      <ChevronRight className="h-4 w-4 text-zinc-500" />
                    )}
                  </div>
                </button>
                {isOpen && (
                  <div className="px-4 pb-4">
                    <p className="text-sm text-zinc-400 mb-3">{draft.explanation}</p>
                    <DiffViewer diff={draft.diff_text} />
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
