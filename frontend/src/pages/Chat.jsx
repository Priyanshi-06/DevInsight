import { useEffect, useRef, useState } from 'react';
import { useOutletContext, useParams } from 'react-router-dom';
import { MessageSquare, PanelRightClose, PanelRightOpen, Plus, Send, Trash2 } from 'lucide-react';
import { api } from '../api/client';
import ChatBubble from '../components/ChatBubble';
import CodeViewer from '../components/CodeViewer';

const RAIL_COLLAPSE_KEY = 'chat-rail-collapsed';

function makeSessionId() {
  return crypto.randomUUID();
}

export default function Chat() {
  const { id } = useParams();
  const { repo } = useOutletContext();
  const repoReady = repo?.status === 'completed';
  const [sessionId, setSessionId] = useState(() => {
    const key = `chat-session-${id}`;
    const existing = sessionStorage.getItem(key);
    if (existing) return existing;
    const fresh = makeSessionId();
    sessionStorage.setItem(key, fresh);
    return fresh;
  });
  const [sessions, setSessions] = useState([]);
  const [loadingSessions, setLoadingSessions] = useState(true);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [error, setError] = useState('');
  const [viewerFile, setViewerFile] = useState(null);
  const [railCollapsed, setRailCollapsed] = useState(() => localStorage.getItem(RAIL_COLLAPSE_KEY) === 'true');
  const bottomRef = useRef(null);

  useEffect(() => {
    localStorage.setItem(RAIL_COLLAPSE_KEY, String(railCollapsed));
  }, [railCollapsed]);

  function refreshSessions() {
    api
      .listChatSessions(id)
      .then((data) => setSessions(data.sessions || []))
      .catch(() => {});
  }

  useEffect(() => {
    setLoadingSessions(true);
    api
      .listChatSessions(id)
      .then((data) => setSessions(data.sessions || []))
      .catch(() => {})
      .finally(() => setLoadingSessions(false));
  }, [id]);

  useEffect(() => {
    sessionStorage.setItem(`chat-session-${id}`, sessionId);
    api
      .getChatHistory(id, sessionId)
      .then((history) => setMessages(history.messages || []))
      .catch(() => {});
  }, [id, sessionId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  function handleCitationClick(citation) {
    setViewerFile({ path: citation.file_path, startLine: citation.start_line, endLine: citation.end_line });
  }

  function handleNewChat() {
    setSessionId(makeSessionId());
    setMessages([]);
    setInput('');
    setError('');
  }

  async function handleDeleteSession(e, targetSessionId) {
    e.stopPropagation();
    try {
      await api.deleteChatSession(id, targetSessionId);
      setSessions((prev) => prev.filter((s) => s.session_id !== targetSessionId));
      if (targetSessionId === sessionId) {
        handleNewChat();
      }
    } catch (err) {
      setError(err.message);
    }
  }

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
      refreshSessions();
    } catch (err) {
      setError(err.message);
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="flex h-[calc(100vh-3.5rem)]">
      <div className="flex-1 min-w-0 flex flex-col max-w-4xl mx-auto px-4 py-8">
        <h1 className="text-lg font-semibold text-white mb-4">Ask about this repository</h1>

        <div className="flex-1 overflow-y-auto space-y-4 pb-4">
          {messages.length === 0 && (
            <p className="text-sm text-zinc-500">
              Try: "What does this project do?", "Where is the main entry point?", "How is authentication handled?"
            </p>
          )}
          {messages.map((m, i) => (
            <ChatBubble
              key={i}
              role={m.role}
              content={m.content}
              citations={m.citations}
              onCitationClick={handleCitationClick}
            />
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

        <CodeViewer repoId={id} file={viewerFile} onClose={() => setViewerFile(null)} />
      </div>

      <aside
        className={`shrink-0 border-l border-zinc-800/80 bg-zinc-950/40 flex flex-col transition-[width] duration-150 ${
          railCollapsed ? 'w-12' : 'w-64'
        }`}
      >
        <div className={`p-2 border-b border-zinc-800/80 flex gap-1.5 ${railCollapsed ? 'flex-col items-center' : ''}`}>
          <button
            type="button"
            onClick={handleNewChat}
            title="New chat"
            className={`inline-flex items-center justify-center gap-1.5 rounded-lg accent-gradient text-white text-sm font-medium hover:opacity-90 transition ${
              railCollapsed ? 'h-9 w-9 shrink-0' : 'flex-1 px-3 py-2'
            }`}
          >
            <Plus className="h-4 w-4 shrink-0" />
            {!railCollapsed && 'New chat'}
          </button>
          <button
            type="button"
            onClick={() => setRailCollapsed((c) => !c)}
            title={railCollapsed ? 'Show past chats' : 'Hide past chats'}
            className="h-9 w-9 shrink-0 inline-flex items-center justify-center rounded-lg text-zinc-500 hover:text-white hover:bg-zinc-800/60 transition"
          >
            {railCollapsed ? <PanelRightOpen className="h-4 w-4" /> : <PanelRightClose className="h-4 w-4" />}
          </button>
        </div>
        {!railCollapsed && (
          <div className="flex-1 overflow-y-auto p-2 space-y-1">
            {loadingSessions ? (
              <p className="px-2 py-2 text-xs text-zinc-500">Loading…</p>
            ) : sessions.length === 0 ? (
              <p className="px-2 py-2 text-xs text-zinc-500">No past chats yet.</p>
            ) : (
              sessions.map((s) => (
                <button
                  key={s.session_id}
                  type="button"
                  onClick={() => setSessionId(s.session_id)}
                  className={`group w-full flex items-start gap-2 rounded-lg px-2.5 py-2 text-left text-sm transition ${
                    s.session_id === sessionId
                      ? 'bg-zinc-800 text-white'
                      : 'text-zinc-400 hover:bg-zinc-800/60 hover:text-white'
                  }`}
                >
                  <MessageSquare className="h-3.5 w-3.5 mt-0.5 shrink-0 text-zinc-500" />
                  <span className="flex-1 min-w-0 truncate" title={s.title}>
                    {s.title}
                  </span>
                  <span
                    role="button"
                    tabIndex={0}
                    onClick={(e) => handleDeleteSession(e, s.session_id)}
                    title="Delete chat"
                    className="shrink-0 opacity-0 group-hover:opacity-100 text-zinc-600 hover:text-red-400 transition"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </span>
                </button>
              ))
            )}
          </div>
        )}
      </aside>
    </div>
  );
}
