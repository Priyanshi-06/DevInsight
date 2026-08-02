const STYLES = {
  pending: 'bg-amber-500/10 text-amber-400 ring-1 ring-inset ring-amber-500/20',
  fetching: 'bg-amber-500/10 text-amber-400 ring-1 ring-inset ring-amber-500/20',
  chunking: 'bg-amber-500/10 text-amber-400 ring-1 ring-inset ring-amber-500/20',
  embedding: 'bg-amber-500/10 text-amber-400 ring-1 ring-inset ring-amber-500/20',
  completed: 'bg-emerald-500/10 text-emerald-400 ring-1 ring-inset ring-emerald-500/20',
  failed: 'bg-red-500/10 text-red-400 ring-1 ring-inset ring-red-500/20',
};

export default function StatusBadge({ status }) {
  const style = STYLES[status] || 'bg-zinc-800 text-zinc-400 ring-1 ring-inset ring-zinc-700';
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${style}`}>
      {(status === 'pending' || status === 'fetching' || status === 'chunking' || status === 'embedding') && (
        <span className="h-1.5 w-1.5 rounded-full bg-current animate-pulse" />
      )}
      {status}
    </span>
  );
}
