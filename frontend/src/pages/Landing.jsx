import { Link, useNavigate } from 'react-router-dom';
import {
  ArrowRight, MessageSquare, Network, Sparkles, GitPullRequest, FlaskConical, RefreshCw, GitBranch,
} from 'lucide-react';

const FEATURES = [
  {
    icon: MessageSquare,
    title: 'Chat with citations',
    desc: 'Ask questions in plain English and get answers grounded in the actual source, with exact file and line citations.',
  },
  {
    icon: Network,
    title: 'Architecture diagrams',
    desc: 'A system overview plus a UML-style class diagram for every module — see how the codebase actually fits together.',
  },
  {
    icon: Sparkles,
    title: 'Contribution picks',
    desc: 'Real open GitHub issues, ranked for beginners and summarized with the relevant code already found for you.',
  },
  {
    icon: GitPullRequest,
    title: 'PR draft assistant',
    desc: 'Turn an issue or task into a draft diff — the AI proposes a change, you review before anything goes anywhere.',
  },
  {
    icon: FlaskConical,
    title: 'Test case generator',
    desc: 'Generate unit tests for a chosen file — happy path, edge cases, and mocked dependencies — for you to review.',
  },
  {
    icon: RefreshCw,
    title: 'Stay in sync',
    desc: 'Know the moment a repo has new commits since it was indexed, and refresh the analysis in one click.',
  },
];

const STEPS = [
  {
    n: '01',
    title: 'Paste a repo URL',
    desc: 'Any public GitHub repository. DevInsight downloads it and starts indexing immediately — no setup scripts.',
  },
  {
    n: '02',
    title: 'It builds the index',
    desc: 'Source files are chunked, embedded, and stored so every answer is retrieved from real, grounded context.',
  },
  {
    n: '03',
    title: 'Ask, explore, ship',
    desc: 'Chat with citations, browse the architecture, find beginner issues, and draft your first PR — all in one place.',
  },
];

const mono = { fontFamily: "'JetBrains Mono', ui-monospace, monospace" };

export default function Landing() {
  const navigate = useNavigate();

  return (
    <div style={{ fontFamily: "'Inter', system-ui, sans-serif" }} className="relative">
      <div
        className="pointer-events-none fixed inset-0 z-0 opacity-40"
        style={{
          backgroundImage:
            'linear-gradient(rgba(255,255,255,0.035) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.035) 1px, transparent 1px)',
          backgroundSize: '64px 64px',
        }}
      />

      <div className="relative z-10">
        {/* HERO */}
        <div className="max-w-4xl mx-auto px-6 pt-24 pb-20 text-center flex flex-col items-center">
          <div
            style={mono}
            className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full border border-zinc-800 text-xs text-[#c99aa1] mb-7"
          >
            <span className="h-1.5 w-1.5 rounded-full bg-[#c99aa1]" />
            Free for public repositories
          </div>
          <h1 className="text-5xl sm:text-6xl font-extrabold tracking-tight text-white leading-[1.05] mb-6">
            Understand any <span className="accent-text-gradient">codebase</span>.
            <br />
            Ship the right change.
          </h1>
          <p className="text-lg text-zinc-400 max-w-xl leading-relaxed mb-10">
            Point DevInsight at a public GitHub repo. It indexes the code, maps the architecture, and
            answers your questions — every answer cites the exact file and line it came from.
          </p>
          <div className="flex flex-wrap items-center justify-center gap-3 mb-16">
            <Link
              to="/signup"
              className="px-6 py-3 rounded-lg accent-gradient text-white text-sm font-semibold hover:opacity-90 transition shadow-lg shadow-[#6b2c35]/20 inline-flex items-center gap-2"
            >
              Get started — free
              <ArrowRight className="h-4 w-4" />
            </Link>
            <Link
              to="/login"
              className="px-6 py-3 rounded-lg border border-zinc-800 text-white text-sm font-semibold hover:bg-zinc-900 transition"
            >
              Sign in
            </Link>
          </div>

          <button
            type="button"
            onClick={() => navigate('/signup')}
            className="w-full max-w-xl rounded-xl border border-zinc-800 bg-zinc-900/80 p-1.5 flex items-center gap-2 shadow-2xl shadow-black/40 hover:border-[#6b2c35]/50 transition text-left"
          >
            <GitBranch className="h-4 w-4 text-zinc-600 ml-2 shrink-0" />
            <span style={mono} className="flex-1 px-1 py-2.5 text-sm text-zinc-500 truncate">
              github.com/owner/repo
            </span>
            <span className="px-4 py-2.5 rounded-lg bg-white/[0.06] text-sm font-semibold text-white inline-flex items-center gap-1.5 shrink-0">
              Analyze
              <ArrowRight className="h-3.5 w-3.5" />
            </span>
          </button>
        </div>

        {/* CHAT PREVIEW */}
        <div className="max-w-3xl mx-auto px-6 mb-32">
          <div className="rounded-2xl border border-zinc-800 bg-zinc-950/80 overflow-hidden shadow-2xl shadow-black/50">
            <div className="flex items-center gap-2 px-5 py-3.5 border-b border-zinc-800/80">
              <span className="h-2.5 w-2.5 rounded-full bg-white/10" />
              <span className="h-2.5 w-2.5 rounded-full bg-white/10" />
              <span className="h-2.5 w-2.5 rounded-full bg-white/10" />
              <span style={mono} className="ml-2 text-xs text-zinc-500">
                devinsight — chat
              </span>
            </div>
            <div style={mono} className="p-7 text-sm leading-8">
              <div className="text-zinc-500 mb-3">$ How does authentication work in this repo?</div>
              <div className="text-zinc-300 mb-5">
                JWT-based auth via <span className="text-[#c99aa1]">djangorestframework-simplejwt</span>. Login
                issues a 7-day access token in <span className="text-[#c99aa1]">accounts/views.py:34</span>,
                validated on every request by the configured authentication class.
              </div>
              <div className="flex flex-wrap gap-1.5 mb-6">
                <span className="text-xs px-2 py-0.5 rounded-md bg-black/40 text-zinc-400 border border-white/10">
                  accounts/views.py:20-45
                </span>
                <span className="text-xs px-2 py-0.5 rounded-md bg-black/40 text-zinc-400 border border-white/10">
                  config/settings.py:88-95
                </span>
              </div>
              <div className="text-zinc-500 mb-3">$ Where would I add a rate limit on login?</div>
              <div className="text-zinc-300">
                In <span className="text-[#c99aa1]">accounts/views.py</span>, inside{' '}
                <span className="text-[#c99aa1]">LoginView.post</span> — before the serializer validates
                credentials, so failed attempts don't reach the database.
              </div>
            </div>
          </div>
        </div>

        {/* FEATURES */}
        <div className="max-w-6xl mx-auto px-6 mb-32">
          <div className="text-center mb-14">
            <div className="text-xs font-semibold tracking-widest uppercase text-[#c99aa1] mb-4">
              Capabilities
            </div>
            <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white">
              From raw repo to real answers
            </h2>
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {FEATURES.map((f) => {
              const Icon = f.icon;
              return (
                <div
                  key={f.title}
                  className="rounded-2xl border border-zinc-800 bg-zinc-900/60 p-7 hover:border-[#6b2c35]/50 transition"
                >
                  <span className="inline-flex h-10 w-10 items-center justify-center rounded-lg accent-gradient text-white mb-5">
                    <Icon className="h-4.5 w-4.5" />
                  </span>
                  <h3 className="text-base font-bold text-white mb-2">{f.title}</h3>
                  <p className="text-sm text-zinc-500 leading-relaxed">{f.desc}</p>
                </div>
              );
            })}
          </div>
        </div>

        {/* HOW IT WORKS */}
        <div className="max-w-5xl mx-auto px-6 mb-32">
          <div className="text-center mb-14">
            <div className="text-xs font-semibold tracking-widest uppercase text-[#c99aa1] mb-4">
              Workflow
            </div>
            <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white mb-3">
              Three steps to an answer
            </h2>
            <p className="text-zinc-500">No setup scripts. No manual indexing.</p>
          </div>
          <div className="grid sm:grid-cols-3 gap-10">
            {STEPS.map((s, i) => (
              <div key={s.n} className={`text-left ${i > 0 ? 'sm:border-l sm:border-zinc-800 sm:pl-8' : ''}`}>
                <div style={mono} className="text-xs text-[#c99aa1] mb-3">
                  {s.n}
                </div>
                <h3 className="text-lg font-bold text-white mb-2">{s.title}</h3>
                <p className="text-sm text-zinc-500 leading-relaxed">{s.desc}</p>
              </div>
            ))}
          </div>
        </div>

        {/* CTA */}
        <div className="max-w-4xl mx-auto px-6 mb-24">
          <div className="rounded-3xl border border-zinc-800 p-16 text-center accent-gradient shadow-2xl shadow-[#6b2c35]/20">
            <h2 className="text-3xl font-extrabold tracking-tight text-white mb-3">
              Point it at your repo. See what it finds.
            </h2>
            <p className="text-white/70 mb-8">Free for public repositories. No credit card.</p>
            <Link
              to="/signup"
              className="inline-flex items-center gap-2 px-6 py-3 rounded-lg bg-white text-black text-sm font-semibold hover:opacity-90 transition"
            >
              Get started — free
              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </div>

        {/* FOOTER */}
        <footer className="border-t border-zinc-800/80 px-6 py-10">
          <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4 text-sm text-zinc-500">
            <span>© {new Date().getFullYear()} DevInsight</span>
            <div className="flex items-center gap-6">
              <Link to="/login" className="hover:text-white transition">
                Sign in
              </Link>
              <Link to="/signup" className="hover:text-white transition">
                Get started
              </Link>
            </div>
          </div>
        </footer>
      </div>
    </div>
  );
}
