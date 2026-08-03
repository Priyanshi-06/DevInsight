import { useState } from 'react';
import { Check, Copy } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

function ThinkingDots() {
  return (
    <span className="inline-flex items-center gap-1 py-0.5">
      <span className="h-1.5 w-1.5 rounded-full bg-zinc-500 animate-bounce [animation-delay:-0.3s]" />
      <span className="h-1.5 w-1.5 rounded-full bg-zinc-500 animate-bounce [animation-delay:-0.15s]" />
      <span className="h-1.5 w-1.5 rounded-full bg-zinc-500 animate-bounce" />
    </span>
  );
}

// Renders assistant answers as real markdown (code blocks, lists, bold, links) using semantic
// <pre>/<code>/<ul> elements — besides looking right, this is what makes copy-pasting a code
// block or list out of the chat retain its line breaks/indentation instead of collapsing to a
// single line, which is what plain-text rendering was doing before.
const markdownComponents = {
  p: ({ children }) => <p className="mb-2 last:mb-0 leading-relaxed">{children}</p>,
  ul: ({ children }) => <ul className="mb-2 last:mb-0 list-disc pl-5 space-y-1">{children}</ul>,
  ol: ({ children }) => <ol className="mb-2 last:mb-0 list-decimal pl-5 space-y-1">{children}</ol>,
  li: ({ children }) => <li className="leading-relaxed">{children}</li>,
  strong: ({ children }) => <strong className="font-semibold text-white">{children}</strong>,
  a: ({ href, children }) => (
    <a href={href} target="_blank" rel="noreferrer" className="text-[#c99aa1] underline hover:text-white transition">
      {children}
    </a>
  ),
  blockquote: ({ children }) => (
    <blockquote className="mb-2 last:mb-0 border-l-2 border-[#6b2c35] pl-3 text-zinc-400">{children}</blockquote>
  ),
  pre: ({ children }) => (
    <pre className="mb-2 last:mb-0 rounded-lg border border-zinc-800 bg-black p-3 overflow-x-auto">{children}</pre>
  ),
  code: ({ className, children }) => {
    const text = String(children).replace(/\n$/, '');
    const isBlock = /language-/.test(className || '') || text.includes('\n');
    if (isBlock) {
      return <code className="font-mono text-xs leading-relaxed whitespace-pre">{text}</code>;
    }
    return (
      <code className="px-1 py-0.5 rounded bg-black/30 text-[#c99aa1] font-mono text-[0.85em]">{text}</code>
    );
  },
};

export default function ChatBubble({ role, content, citations, isThinking, onCitationClick }) {
  const isUser = role === 'user';
  const [copied, setCopied] = useState(false);

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(content || '');
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      // Clipboard access can be blocked (e.g. insecure context/permissions) — fail silently,
      // the user still has normal text-selection copy as a fallback.
    }
  }

  return (
    <div className={`group flex flex-col ${isUser ? 'items-end' : 'items-start'}`}>
      <div
        className={`max-w-2xl rounded-2xl px-4 py-3 text-sm ${
          isUser
            ? 'accent-gradient text-white rounded-br-sm shadow-lg shadow-[#6b2c35]/10'
            : 'bg-zinc-900 border border-zinc-800 text-zinc-100 rounded-bl-sm'
        }`}
      >
        {isThinking ? (
          <ThinkingDots />
        ) : isUser ? (
          <p className="whitespace-pre-wrap">{content}</p>
        ) : (
          <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
            {content}
          </ReactMarkdown>
        )}
        {citations && citations.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-1.5">
            {citations.map((c, i) => (
              <button
                key={i}
                type="button"
                onClick={() => onCitationClick?.(c)}
                title={`View ${c.file_path} (lines ${c.start_line}-${c.end_line})`}
                className="text-xs font-mono px-2 py-0.5 rounded-md bg-black/30 text-zinc-300 border border-white/10 hover:border-[#9c6570] hover:text-white transition cursor-pointer"
              >
                {c.file_path}:{c.start_line}-{c.end_line}
              </button>
            ))}
          </div>
        )}
      </div>
      {!isThinking && (
        <button
          type="button"
          onClick={handleCopy}
          title={copied ? 'Copied!' : 'Copy message'}
          className="mt-1 inline-flex items-center gap-1 px-1.5 py-1 rounded-md text-xs text-zinc-600 hover:text-white hover:bg-zinc-800/60 opacity-0 group-hover:opacity-100 focus:opacity-100 transition"
        >
          {copied ? <Check className="h-3 w-3 text-emerald-400" /> : <Copy className="h-3 w-3" />}
        </button>
      )}
    </div>
  );
}
