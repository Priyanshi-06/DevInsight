import { useEffect, useState } from 'react';
import { useOutletContext, useParams } from 'react-router-dom';
import { ChevronDown, ChevronRight, FlaskConical } from 'lucide-react';
import { api } from '../api/client';
import CodeBlock from '../components/CodeBlock';

export default function TestGenerator() {
  const { id } = useParams();
  const { repo } = useOutletContext();
  const [targetFile, setTargetFile] = useState('');
  const [taskDescription, setTaskDescription] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [drafts, setDrafts] = useState([]);
  const [loadingHistory, setLoadingHistory] = useState(true);
  const [expandedId, setExpandedId] = useState(null);

  useEffect(() => {
    api
      .listTestDrafts(id)
      .then((data) => setDrafts(data.drafts || []))
      .catch(() => {})
      .finally(() => setLoadingHistory(false));
  }, [id]);

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');
    if (!targetFile && !taskDescription.trim()) {
      setError('Pick a file or describe what to test.');
      return;
    }
    setSubmitting(true);
    try {
      const draft = await api.createTestDraft(id, {
        targetFile,
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
      <h1 className="text-xl font-semibold text-white mb-2">Test Case Generator</h1>
      <p className="text-sm text-zinc-500 mb-6">
        The AI writes unit tests — happy path, edge cases, and mocks for external dependencies — for you to review.
      </p>

      <form onSubmit={handleSubmit} className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-4 mb-8 space-y-3">
        <div>
          <label className="block text-xs font-medium text-zinc-500 mb-1">File to test (optional)</label>
          <select
            value={targetFile}
            onChange={(e) => setTargetFile(e.target.value)}
            className="w-full rounded-lg border border-zinc-800 bg-black px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-[#6b2c35] focus:border-transparent"
          >
            <option value="">— pick automatically from description below —</option>
            {(repo?.file_tree || []).map((path) => (
              <option key={path} value={path}>
                {path}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-xs font-medium text-zinc-500 mb-1">
            What should the tests focus on? {targetFile && '(optional if a file is selected)'}
          </label>
          <textarea
            value={taskDescription}
            onChange={(e) => setTaskDescription(e.target.value)}
            rows={3}
            placeholder="e.g. Cover the validation logic and invalid-input handling"
            className="w-full rounded-lg border border-zinc-800 bg-black px-3 py-2 text-sm text-white placeholder:text-zinc-600 focus:outline-none focus:ring-2 focus:ring-[#6b2c35] focus:border-transparent"
          />
        </div>
        {error && <p className="text-sm text-red-400">{error}</p>}
        <button
          type="submit"
          disabled={submitting}
          className="px-4 py-2 rounded-lg accent-gradient text-white text-sm font-medium hover:opacity-90 disabled:opacity-50 transition inline-flex items-center gap-2"
        >
          <FlaskConical className="h-4 w-4" />
          {submitting ? 'Writing tests… (this can take a minute)' : 'Generate tests'}
        </button>
      </form>

      <h2 className="text-sm font-semibold text-zinc-500 uppercase tracking-wide mb-3">Generated test suites</h2>
      {loadingHistory ? (
        <p className="text-sm text-zinc-500">Loading…</p>
      ) : drafts.length === 0 ? (
        <p className="text-sm text-zinc-500">No test suites generated yet.</p>
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
                    <h3 className="font-medium text-white truncate">{draft.test_file_name || `test for ${draft.target_file}`}</h3>
                    <p className="text-xs font-mono text-zinc-500 mt-0.5 truncate">
                      tests: {draft.target_file}
                    </p>
                  </div>
                  <div className="flex items-center gap-3 shrink-0">
                    {draft.framework && <span className="text-xs text-zinc-500">{draft.framework}</span>}
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
                    <CodeBlock code={draft.test_code} />
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
