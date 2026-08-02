function ThinkingDots() {
  return (
    <span className="inline-flex items-center gap-1 py-0.5">
      <span className="h-1.5 w-1.5 rounded-full bg-zinc-500 animate-bounce [animation-delay:-0.3s]" />
      <span className="h-1.5 w-1.5 rounded-full bg-zinc-500 animate-bounce [animation-delay:-0.15s]" />
      <span className="h-1.5 w-1.5 rounded-full bg-zinc-500 animate-bounce" />
    </span>
  );
}

export default function ChatBubble({ role, content, citations, isThinking }) {
  const isUser = role === 'user';
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-2xl rounded-2xl px-4 py-3 text-sm whitespace-pre-wrap ${
          isUser
            ? 'accent-gradient text-white rounded-br-sm shadow-lg shadow-[#6b2c35]/10'
            : 'bg-zinc-900 border border-zinc-800 text-zinc-100 rounded-bl-sm'
        }`}
      >
        {isThinking ? <ThinkingDots /> : <p>{content}</p>}
        {citations && citations.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-1.5">
            {citations.map((c, i) => (
              <span
                key={i}
                title={`${c.file_path} (lines ${c.start_line}-${c.end_line})`}
                className="text-xs font-mono px-2 py-0.5 rounded-md bg-black/30 text-zinc-300 border border-white/10"
              >
                {c.file_path}:{c.start_line}-{c.end_line}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
