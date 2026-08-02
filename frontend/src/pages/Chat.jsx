import { useEffect, useRef, useState } from 'react';
import { useOutletContext, useParams } from 'react-router-dom';
import { Send } from 'lucide-react';
import { api } from '../api/client';
import ChatBubble from '../components/ChatBubble';

function makeSessionId() {
  return crypto.randomUUID();
}

export default function Chat() {
  const { id } = useParams();
  const { repo } = useOutletContext();
  const repoReady = repo?.status === 'completed';
  const [sessionId] = useState(() => {
    const key = `chat-session-${id}`;
    const existing = sessionStorage.getItem(key);
    if (existing) return existing;
    const fresh = makeSessionId();
    sessionStorage.setItem(key, fresh);
    return fresh;
  });
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [error, setError] = useState('');
  const bottomRef = useRef(null);

  useEffect(() => {
    api
      .getChatHistory(id, sessionId)
      .then((history) => setMessages(history.messages || []))
      .catch(() => {});
  }, [id, sessionId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  async function handleSend(e) {
    e.preventDefault();
    const text = input.trim();
    if (!text || sending || !repoReady) return;
    setError('');
    setInput('');
    setMessages((prev) => [...prev, { role: 'user', content: text }]);
    setSending(true);
    try {
      const res = await api.sendChatMessage(id, text, sessionId);
      setMessages((prev) => [...prev, { role: 'assistant', content: res.answer, citations: res.citations }]);
    } catch (err) {
      setError(err.message);
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 flex flex-col h-[calc(100vh-3.5rem)]">
      <h1 className="text-lg font-semibold text-white mb-4">Ask about this repository</h1>

      <div className="flex-1 overflow-y-auto space-y-4 pb-4">
        {messages.length === 0 && (
          <p className="text-sm text-zinc-500">
            Try: "What does this project do?", "Where is the main entry point?", "How is authentication handled?"
          </p>
        )}
        {messages.map((m, i) => (
          <ChatBubble key={i} role={m.role} content={m.content} citations={m.citations} />
        ))}
        {sending && <ChatBubble role="assistant" isThinking />}
        <div ref={bottomRef} />
      </div>

      {error && <p className="text-sm text-red-400 mb-2">{error}</p>}
      {!repoReady && (
        <p className="text-sm text-zinc-500 mb-2">
          {repo?.status === 'failed'
            ? 'Repository indexing failed, so chat is unavailable.'
            : `This repository is still being indexed (${repo?.status || 'loading'})… chat unlocks once indexing completes.`}
        </p>
      )}

      <form onSubmit={handleSend} className="flex gap-2 border-t border-zinc-800 pt-4">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={!repoReady || sending}
          placeholder="Ask a question about the codebase…"
          className="flex-1 rounded-lg border border-zinc-800 bg-zinc-900 px-4 py-3 text-sm text-white placeholder:text-zinc-600 focus:outline-none focus:ring-2 focus:ring-[#6b2c35] focus:border-transparent disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={!repoReady || sending}
          className="px-5 py-3 rounded-lg accent-gradient text-white text-sm font-medium hover:opacity-90 disabled:opacity-50 transition inline-flex items-center gap-2"
        >
          <Send className="h-4 w-4" />
          Send
        </button>
      </form>
    </div>
  );
}
