import { useCallback, useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { RefreshCw } from 'lucide-react';
import { api } from '../api/client';
import MermaidDiagram from '../components/MermaidDiagram';
import ClassList from '../components/ClassList';

const VIEWS = [
  { key: 'hld', label: 'High-Level Design', hint: 'System overview, then a detail diagram for each multi-module component' },
  { key: 'lld', label: 'Low-Level Design', hint: 'One diagram per module: classes, methods, inheritance, and what each does' },
];

function LldModuleCard({ repoId, diagram, classes }) {
  const [expandedId, setExpandedId] = useState(null);
  const knownIds = classes.map((c) => c.id);

  function handleNodeClick(classId) {
    setExpandedId(classId);
    // A short timeout (rather than requestAnimationFrame, which can be throttled in
    // non-focused/background tabs) reliably runs after React has committed the expanded row to
    // the DOM, so scrollIntoView measures the final layout.
    setTimeout(() => {
      document.getElementById(`class-row-${classId}`)?.scrollIntoView({ behavior: 'instant', block: 'center' });
    }, 50);
  }

  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-4">
      <h3 className="font-mono text-sm font-semibold text-zinc-200 mb-3">
        {diagram.module} <span className="text-zinc-500 font-sans font-normal">({diagram.class_count} classes)</span>
      </h3>
      <MermaidDiagram
        chart={diagram.mermaid}
        id={`${repoId}-lld-${diagram.module.replace(/[^A-Za-z0-9]/g, '_')}`}
        knownIds={knownIds}
        onNodeClick={handleNodeClick}
      />
      <p className="text-xs text-zinc-500 mt-2">Click a class or method in the diagram to jump to its explanation below.</p>
      <ClassList classes={classes} expandedId={expandedId} onToggle={setExpandedId} />
    </div>
  );
}

export default function Architecture() {
  const { id } = useParams();
  const [data, setData] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [view, setView] = useState('hld');

  const load = useCallback((refresh = false) => {
    const setBusy = refresh ? setRefreshing : setLoading;
    setBusy(true);
    setError('');
    api
      .getArchitecture(id, refresh)
      .then(setData)
      .catch((err) => setError(err.message))
      .finally(() => setBusy(false));
  }, [id]);

  useEffect(() => {
    load(false);
  }, [load]);

  if (loading) {
    return <div className="max-w-5xl mx-auto px-4 py-10 text-sm text-zinc-500">Analyzing repository structure…</div>;
  }
  if (error) {
    return <div className="max-w-5xl mx-auto px-4 py-10 text-sm text-red-400">{error}</div>;
  }

  const activeView = VIEWS.find((v) => v.key === view);
  const descriptionsByModule = {};
  for (const cls of data?.lld_descriptions || []) {
    (descriptionsByModule[cls.module] ||= []).push(cls);
  }

  return (
    <div className="max-w-5xl mx-auto px-4 py-10">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-semibold text-white">Architecture Overview</h1>
        <button
          onClick={() => load(true)}
          disabled={refreshing}
          className="text-sm px-3 py-1.5 rounded-md border border-zinc-800 text-zinc-300 hover:bg-zinc-800 disabled:opacity-50 inline-flex items-center gap-1.5 transition"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${refreshing ? 'animate-spin' : ''}`} />
          {refreshing ? 'Regenerating…' : 'Regenerate'}
        </button>
      </div>

      {data?.summary && (
        <div className="mb-8 rounded-xl border border-zinc-800 bg-zinc-900/60 p-4">
          <h2 className="text-sm font-semibold text-zinc-500 uppercase tracking-wide mb-2">Summary</h2>
          <p className="text-sm text-zinc-300 whitespace-pre-wrap">{data.summary}</p>
        </div>
      )}

      <div className="flex items-center justify-between mb-1">
        <h2 className="text-sm font-semibold text-zinc-500 uppercase tracking-wide">Dependency graph</h2>
        <div className="flex gap-1">
          {VIEWS.map((v) => (
            <button
              key={v.key}
              onClick={() => setView(v.key)}
              className={`text-xs px-3 py-1.5 rounded-md transition ${
                view === v.key
                  ? 'accent-gradient text-white'
                  : 'text-zinc-400 hover:bg-zinc-800'
              }`}
            >
              {v.label}
            </button>
          ))}
        </div>
      </div>
      <p className="text-xs text-zinc-500 mb-3">{activeView.hint}</p>

      {view === 'hld' && (
        <div className="mb-8 space-y-4">
          <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-4">
            <h3 className="text-sm font-semibold text-zinc-500 uppercase tracking-wide mb-3">System overview</h3>
            {data?.hld_mermaid ? (
              <MermaidDiagram chart={data.hld_mermaid} id={`${id}-hld-overview`} />
            ) : (
              <p className="text-sm text-zinc-500">No diagram available.</p>
            )}
          </div>
          {data?.hld_group_diagrams?.map((d) => (
            <div
              key={d.group}
              className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-4"
            >
              <h3 className="font-mono text-sm font-semibold text-zinc-200 mb-3">
                {d.group} <span className="text-zinc-500 font-sans font-normal">({d.module_count} modules)</span>
              </h3>
              <MermaidDiagram chart={d.mermaid} id={`${id}-hld-${d.group.replace(/[^A-Za-z0-9]/g, '_')}`} />
            </div>
          ))}
        </div>
      )}

      {view === 'lld' && (
        <div className="mb-8 space-y-4">
          {!data?.lld_diagrams?.length ? (
            <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-4">
              <p className="text-sm text-zinc-500">
                No classes/structs detected in this codebase — see High-Level Design instead.
              </p>
            </div>
          ) : (
            data.lld_diagrams.map((d) => (
              <LldModuleCard
                key={d.module}
                repoId={id}
                diagram={d}
                classes={descriptionsByModule[d.module] || []}
              />
            ))
          )}
        </div>
      )}

      {data?.module_stats?.length > 0 && (
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-4">
          <h2 className="text-sm font-semibold text-zinc-500 uppercase tracking-wide mb-3">
            Core modules
          </h2>
          <ul className="text-sm divide-y divide-zinc-800">
            {data.module_stats.map((m) => (
              <li key={m.module} className="flex justify-between py-1.5">
                <span className="font-mono text-zinc-300">{m.module}</span>
                <span className="text-zinc-500">{m.file_count} files</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
