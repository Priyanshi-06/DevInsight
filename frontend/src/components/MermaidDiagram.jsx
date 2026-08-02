import { useEffect, useRef, useState } from 'react';
import mermaid from 'mermaid';

let initialized = false;

function initMermaid() {
  if (initialized) return;
  mermaid.initialize({
    startOnLoad: false,
    theme: 'dark',
    securityLevel: 'strict',
    themeVariables: {
      darkMode: true,
      background: '#000000',
      primaryColor: '#18181b',
      primaryBorderColor: '#52525b',
      primaryTextColor: '#f4f4f5',
      secondaryColor: '#27272a',
      tertiaryColor: '#18181b',
      lineColor: '#71717a',
      textColor: '#e4e4e7',
      clusterBkg: '#120d0e',
      clusterBorder: '#6b2c35',
      edgeLabelBackground: '#000000',
      fontFamily: 'system-ui, "Segoe UI", Roboto, sans-serif',
    },
  });
  initialized = true;
}

// Mermaid's own click directive requires securityLevel 'loose' (arbitrary callback execution),
// which we deliberately avoid. Instead we detect clicks ourselves via event delegation on the
// rendered SVG: walk up from the click target looking for an element whose id contains one of
// our known node ids (Mermaid embeds the id we assign as a substring of its internal DOM id).
export default function MermaidDiagram({ chart, id, knownIds, onNodeClick }) {
  const containerRef = useRef(null);
  const [error, setError] = useState('');

  // "Latest ref" pattern: knownIds/onNodeClick get a fresh array/function identity on every
  // parent re-render, so keeping them in the effect's dependency array would tear down and
  // rebuild the listener (and re-run the async render) far more than necessary. Reading them via
  // a ref updated on every render keeps the effect deps stable at [chart, id] while the click
  // handler still always sees current values.
  const knownIdsRef = useRef(knownIds);
  const onNodeClickRef = useRef(onNodeClick);
  knownIdsRef.current = knownIds;
  onNodeClickRef.current = onNodeClick;

  useEffect(() => {
    initMermaid();
    let cancelled = false;
    const container = containerRef.current;

    function handleClick(event) {
      const ids = knownIdsRef.current;
      const callback = onNodeClickRef.current;
      if (!callback || !ids?.length) return;
      let el = event.target;
      while (el && el !== container) {
        if (el.id) {
          const match = ids.find((known) => el.id.includes(known));
          if (match) {
            callback(match);
            return;
          }
        }
        el = el.parentElement;
      }
    }

    async function render() {
      setError('');
      try {
        const { svg } = await mermaid.render(`mermaid-${id}`, chart);
        if (!cancelled && containerRef.current) {
          containerRef.current.innerHTML = svg;
        }
      } catch (err) {
        console.error('Mermaid render failed:', id, String(err && err.message), String(err && err.str));
        if (!cancelled) setError('Could not render diagram.');
      }
    }

    if (chart) render();
    container?.addEventListener('click', handleClick);
    return () => {
      cancelled = true;
      container?.removeEventListener('click', handleClick);
    };
  }, [chart, id]);

  if (error) {
    return <p className="text-sm text-red-400">{error}</p>;
  }

  return (
    <div
      ref={containerRef}
      className={`overflow-x-auto ${onNodeClick ? '[&_.node]:cursor-pointer' : ''}`}
    />
  );
}
