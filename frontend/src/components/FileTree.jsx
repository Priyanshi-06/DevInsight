import { useMemo, useState } from 'react';
import { File, Folder, FolderOpen } from 'lucide-react';

function buildTree(paths) {
  const root = { name: '', children: {}, isFile: false };
  for (const path of paths) {
    const parts = path.split('/');
    let node = root;
    parts.forEach((part, idx) => {
      const isFile = idx === parts.length - 1;
      if (!node.children[part]) {
        node.children[part] = { name: part, children: {}, isFile };
      }
      node = node.children[part];
    });
  }
  return root;
}

function Node({ node, depth }) {
  const [open, setOpen] = useState(depth < 1);
  const entries = Object.values(node.children).sort((a, b) => {
    if (a.isFile !== b.isFile) return a.isFile ? 1 : -1;
    return a.name.localeCompare(b.name);
  });

  if (node.isFile) {
    return (
      <div className="flex items-center gap-1.5 py-0.5 text-zinc-400" style={{ paddingLeft: depth * 16 }}>
        <File className="h-3.5 w-3.5 text-zinc-600 shrink-0" />
        <span className="truncate">{node.name}</span>
      </div>
    );
  }

  return (
    <div>
      {node.name && (
        <button
          onClick={() => setOpen(!open)}
          className="flex items-center gap-1.5 py-0.5 w-full text-left text-zinc-200 hover:text-[#9c6570] transition"
          style={{ paddingLeft: depth * 16 }}
        >
          {open ? (
            <FolderOpen className="h-3.5 w-3.5 text-zinc-500 shrink-0" />
          ) : (
            <Folder className="h-3.5 w-3.5 text-zinc-500 shrink-0" />
          )}
          <span className="truncate font-medium">{node.name}</span>
        </button>
      )}
      {open && entries.map((child) => <Node key={child.name} node={child} depth={depth + 1} />)}
    </div>
  );
}

export default function FileTree({ paths }) {
  const tree = useMemo(() => buildTree(paths || []), [paths]);
  if (!paths || paths.length === 0) {
    return <p className="text-sm text-zinc-500">No files indexed yet.</p>;
  }
  return (
    <div className="text-sm font-mono max-h-96 overflow-y-auto pr-2">
      <Node node={tree} depth={0} />
    </div>
  );
}
