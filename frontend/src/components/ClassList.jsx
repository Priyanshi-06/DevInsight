import { useState } from 'react';

export default function ClassList({ classes, expandedId: controlledId, onToggle }) {
  const [internalId, setInternalId] = useState(null);
  const isControlled = controlledId !== undefined;
  const expandedId = isControlled ? controlledId : internalId;
  const toggle = (clsId) => {
    const next = expandedId === clsId ? null : clsId;
    if (isControlled) onToggle?.(next);
    else setInternalId(next);
  };

  if (!classes || classes.length === 0) return null;

  return (
    <div className="mt-3 space-y-1.5">
      {classes.map((cls) => {
        const isOpen = expandedId === cls.id;
        return (
          <div
            key={cls.id}
            id={`class-row-${cls.id}`}
            className={`rounded-md border overflow-hidden transition ${
              isOpen ? 'border-[#2a1418]/60 ring-1 ring-[#6b2c35]/30' : 'border-zinc-800'
            }`}
          >
            <button
              onClick={() => toggle(cls.id)}
              className="w-full flex flex-wrap items-baseline gap-x-2 gap-y-0.5 px-3 py-2 text-left hover:bg-zinc-800/50 transition"
            >
              <span className="font-mono text-xs font-semibold text-zinc-200 shrink-0">
                {cls.name}
              </span>
              <span className="text-xs text-zinc-500">{cls.purpose}</span>
            </button>
            {isOpen && (
              <div className="px-3 pb-3 pt-1 border-t border-zinc-800 bg-zinc-900/50">
                <p className="text-xs text-zinc-500 mb-1">{cls.file_path}</p>
                {cls.parents?.length > 0 && (
                  <p className="text-xs text-zinc-400 mb-1.5">
                    Extends: <span className="font-mono">{cls.parents.join(', ')}</span>
                  </p>
                )}
                <pre className="text-xs font-mono bg-black border border-zinc-800 rounded px-2 py-1 overflow-x-auto whitespace-pre-wrap text-zinc-300">
                  {cls.definition}
                </pre>
                {cls.methods?.length > 0 && (
                  <div className="mt-2 space-y-1">
                    <p className="text-xs font-semibold text-zinc-500">Methods</p>
                    {cls.methods.map((m) => (
                      <div key={m.name} className="flex flex-wrap items-baseline gap-x-2 text-xs">
                        <span className="font-mono text-zinc-300 shrink-0">{m.name}()</span>
                        <span className="text-zinc-500">{m.purpose}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
