import { useEffect, useRef, useState, useCallback } from 'react';
import { Outlet, useParams } from 'react-router-dom';
import { api } from '../api/client';
import Sidebar from '../components/Sidebar';

export default function RepoLayout() {
  const { id } = useParams();
  const [repo, setRepo] = useState(null);
  const [error, setError] = useState('');
  const timeoutRef = useRef(null);
  const cancelledRef = useRef(false);

  const load = useCallback(async () => {
    try {
      const data = await api.getRepo(id);
      setRepo(data);
      return data;
    } catch (err) {
      setError(err.message);
      return null;
    }
  }, [id]);

  // A self-scheduling timeout chain (rather than setInterval) so polling naturally stops once
  // the repo settles into completed/failed, but can be restarted on demand — e.g. after
  // triggering a re-index, which sends the repo back through pending/fetching/... and needs
  // watching again.
  const startPolling = useCallback(() => {
    clearTimeout(timeoutRef.current);
    async function tick() {
      const data = await load();
      if (cancelledRef.current || !data) return;
      if (data.status !== 'completed' && data.status !== 'failed') {
        timeoutRef.current = setTimeout(tick, 2000);
      }
    }
    tick();
  }, [load]);

  useEffect(() => {
    cancelledRef.current = false;
    setRepo(null);
    setError('');
    startPolling();
    return () => {
      cancelledRef.current = true;
      clearTimeout(timeoutRef.current);
    };
  }, [id, startPolling]);

  return (
    <div className="flex flex-1 min-h-[calc(100vh-3.5rem)]">
      <Sidebar repo={repo} repoId={id} />
      <main className="flex-1 min-w-0">
        {error ? (
          <div className="max-w-4xl mx-auto px-4 py-10 text-sm text-red-400">{error}</div>
        ) : (
          <Outlet context={{ repo, reloadRepo: load, startPolling }} />
        )}
      </main>
    </div>
  );
}
