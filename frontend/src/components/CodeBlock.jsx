export default function CodeBlock({ code }) {
  if (!code) return null;
  const lines = code.split('\n');
  return (
    <pre className="text-xs font-mono rounded-lg border border-zinc-800 overflow-x-auto bg-black">
      {lines.map((line, i) => (
        <div key={i} className="flex px-3 py-0.5 whitespace-pre">
          <span className="w-8 shrink-0 text-right pr-3 text-zinc-600 select-none">{i + 1}</span>
          <span className="text-zinc-300">{line || ' '}</span>
        </div>
      ))}
    </pre>
  );
}
