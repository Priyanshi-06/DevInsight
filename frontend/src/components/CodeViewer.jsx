import { useEffect, useRef, useState } from 'react';
import { X } from 'lucide-react';
import { api } from '../api/client';

export default function CodeViewer({ repoId, file, onClose }) {
  const [content, setContent] = useState(null);
  const [truncated, setTruncated] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const highlightRef = useRef(null);

  useEffect(() => {
    if (!file) return;
    setLoading(true);
    setError('');
    setContent(null);
    api
      .getFileContent(repoId, file.path)
      .then((data) => {
        setContent(data.content);
        setTruncated(data.truncated);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [repoId, file?.path]);

  useEffect(() => {
    if (content !== null) {
      highlightRef.current?.scrollIntoView({ behavior: 'instant', block: 'center' });
    }
  }, [content]);

  useEffect(() => {
    function handleKey(e) {
      if (e.key === 'Escape') onClose();
    }
    if (file) document.addEventListener('keydown', handleKey);
    return () => document.removeEventListener('keydown', handleKey);
  }, [file, onClose]);

  if (!file) return null;

  const lines = content !== null ? content.split('\n') : [];
  const hasRange = Boolean(file.startLine && file.endLine);

  return (
    <div className="fixed inset-0 z-40 flex justify-end bg-black/60" onClick={onClose}>
      <div
        className="w-full max-w-3xl h-full bg-zinc-950 border-l border-zinc-800 flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between gap-3 px-4 py-3 border-b border-zinc-800 shrink-0">
          <span className="text-sm font-mono text-zinc-200 truncate">{file.path}</span>
          <button
            type="button"
            onClick={onClose}
            className="text-zinc-500 hover:text-white p-1.5 rounded-md hover:bg-zinc-800 transition shrink-0"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
        <div className="flex-1 overflow-auto">
          {loading && <p className="p-4 text-sm text-zinc-500">Loading…</p>}
          {error && <p className="p-4 text-sm text-red-400">{error}</p>}
          {!loading && !error && (
            <pre className="text-xs font-mono py-2">
              {lines.map((line, i) => {
                const lineNumber = i + 1;
                const isHighlighted = hasRange && lineNumber >= file.startLine && lineNumber <= file.endLine;
                return (
                  <div
                    key={i}
                    ref={isHighlighted && lineNumber === file.startLine ? highlightRef : null}
                    className={`flex px-3 whitespace-pre ${isHighlighted ? 'bg-[#6b2c35]/25' : ''}`}
                  >
                    <span className="w-10 shrink-0 text-right pr-3 text-zinc-600 select-none">{lineNumber}</span>
                    <span className="text-zinc-300">{line || ' '}</span>
                  </div>
                );
              })}
              {truncated && (
                <div className="px-3 py-2 text-amber-400">File truncated — too large to preview in full.</div>
              )}
            </pre>
          )}
        </div>
      </div>
    </div>
  );
}
