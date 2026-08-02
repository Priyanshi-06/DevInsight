function lineClass(line) {
  if (line.startsWith('+') && !line.startsWith('+++')) return 'bg-emerald-500/10 text-emerald-400';
  if (line.startsWith('-') && !line.startsWith('---')) return 'bg-red-500/10 text-red-400';
  if (line.startsWith('@@')) return 'bg-[#6b2c35]/10 text-[#c99aa1]';
  return 'text-zinc-400';
}

export default function DiffViewer({ diff }) {
  if (!diff) return null;
  const lines = diff.split('\n');
  return (
    <pre className="text-xs font-mono rounded-lg border border-zinc-800 overflow-x-auto bg-black">
      {lines.map((line, i) => (
        <div key={i} className={`px-3 py-0.5 whitespace-pre ${lineClass(line)}`}>
          {line || ' '}
        </div>
      ))}
    </pre>
  );
}
