import { useEffect, useRef, useState, useCallback } from 'react';
import { Outlet, useParams } from 'react-router-dom';
import { api } from '../api/client';
import Sidebar from '../components/Sidebar';

export default function RepoLayout() {
  const { id } = useParams();
  const [repo, setRepo] = useState(null);
  const [error, setError] = useState('');
  const pollRef = useRef(null);

  const load = useCallback(async () => {
    try {
      const data = await api.getRepo(id);
      setRepo(data);
      if (data.status === 'completed' || data.status === 'failed') {
        clearInterval(pollRef.current);
      }
      return data;
    } catch (err) {
      setError(err.message);
      return null;
    }
  }, [id]);

  useEffect(() => {
    let cancelled = false;
    setRepo(null);
    setError('');

    async function tick() {
      const data = await load();
      if (cancelled || !data) return;
    }

    tick();
    pollRef.current = setInterval(tick, 2000);
    return () => {
      cancelled = true;
      clearInterval(pollRef.current);
    };
  }, [id, load]);

  return (
    <div className="flex flex-1 min-h-[calc(100vh-3.5rem)]">
      <Sidebar repo={repo} repoId={id} />
      <main className="flex-1 min-w-0">
        {error ? (
          <div className="max-w-4xl mx-auto px-4 py-10 text-sm text-red-400">{error}</div>
        ) : (
          <Outlet context={{ repo, reloadRepo: load }} />
        )}
      </main>
    </div>
  );
}
