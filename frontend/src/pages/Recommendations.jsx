import { useCallback, useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { RefreshCw, GitPullRequest } from 'lucide-react';
import { api } from '../api/client';

export default function Recommendations() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [items, setItems] = useState([]);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback((refresh = false) => {
    const setBusy = refresh ? setRefreshing : setLoading;
    setBusy(true);
    setError('');
    api
      .getRecommendations(id, refresh)
      .then((data) => {
        setItems(data.recommendations || []);
        setMessage(data.message || '');
      })
      .catch((err) => setError(err.message))
      .finally(() => setBusy(false));
  }, [id]);

  useEffect(() => {
    load(false);
  }, [load]);

  if (loading) {
    return <div className="max-w-4xl mx-auto px-4 py-10 text-sm text-zinc-500">Finding contribution opportunities…</div>;
  }
  if (error) {
    return <div className="max-w-4xl mx-auto px-4 py-10 text-sm text-red-400">{error}</div>;
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-10">
      <div className="flex items-center justify-between mb-2">
        <h1 className="text-xl font-semibold text-white">Contribution Opportunities</h1>
        <button
          onClick={() => load(true)}
          disabled={refreshing}
          className="text-sm px-3 py-1.5 rounded-md border border-zinc-800 text-zinc-300 hover:bg-zinc-800 disabled:opacity-50 inline-flex items-center gap-1.5 transition"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${refreshing ? 'animate-spin' : ''}`} />
          {refreshing ? 'Refreshing…' : 'Refresh'}
        </button>
      </div>
      {message && <p className="text-sm text-amber-400 mb-6">{message}</p>}
      {!message && <div className="mb-6" />}

      {items.length === 0 ? (
        <p className="text-sm text-zinc-500">No open issues found for this repository.</p>
      ) : (
        <div className="space-y-4">
          {items.map((rec) => (
            <div
              key={rec.id}
              className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-4"
            >
              <div className="flex items-start justify-between gap-4">
                <div>
                  <a
                    href={rec.url}
                    target="_blank"
                    rel="noreferrer"
                    className="font-medium text-white hover:text-[#9c6570] transition"
                  >
                    #{rec.issue_number} {rec.title}
                  </a>
                  <div className="flex flex-wrap gap-1.5 mt-2">
                    {rec.labels.map((label) => (
                      <span
                        key={label}
                        className="text-xs px-2 py-0.5 rounded-full bg-zinc-800 text-zinc-300"
                      >
                        {label}
                      </span>
                    ))}
                  </div>
                </div>
                <button
                  onClick={() => navigate(`/repos/${id}/pr-assistant?issue=${rec.issue_number}`)}
                  className="shrink-0 text-xs px-3 py-1.5 rounded-md accent-gradient text-white hover:opacity-90 transition inline-flex items-center gap-1.5"
                >
                  <GitPullRequest className="h-3.5 w-3.5" />
                  Draft a PR
                </button>
              </div>
              <p className="text-sm text-zinc-400 mt-3">{rec.ai_summary}</p>
              {rec.suggested_files?.length > 0 && (
                <div className="mt-3 flex flex-wrap gap-1.5">
                  {rec.suggested_files.map((f) => (
                    <span
                      key={f}
                      className="text-xs font-mono px-2 py-0.5 rounded-md bg-black border border-zinc-800 text-zinc-500"
                    >
                      {f}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
