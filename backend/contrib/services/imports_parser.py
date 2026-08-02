import os
import re
from collections import Counter

PY_FROM_IMPORT_RE = re.compile(r'^\s*from\s+(\.*[\w.]*)\s+import\s+(.+)$', re.MULTILINE)
PY_PLAIN_IMPORT_RE = re.compile(r'^\s*import\s+(\.*[\w.,\s]+)$', re.MULTILINE)
JS_IMPORT_RE = re.compile(
    r'''(?:import\s+(?:[^'";]*?\sfrom\s+)?['"]([^'"]+)['"])|(?:require\(\s*['"]([^'"]+)['"]\s*\))'''
)
JAVA_IMPORT_RE = re.compile(r'^\s*import\s+(?:static\s+)?([\w.]+)\s*;', re.MULTILINE)
GO_IMPORT_RE = re.compile(r'^\s*"([\w./\-]+)"', re.MULTILINE)
RUBY_REQUIRE_RE = re.compile(r'''require(?:_relative)?\s+['"]([^'"]+)['"]''')

LANG_BY_EXT = {
    '.py': 'python',
    '.js': 'javascript', '.jsx': 'javascript', '.mjs': 'javascript', '.cjs': 'javascript',
    '.ts': 'javascript', '.tsx': 'javascript',
    '.java': 'java',
    '.go': 'go',
    '.rb': 'ruby',
}

PY_CLASS_RE = re.compile(r'^\s*class\s+(\w+)\s*(?:\(([^)]*)\))?\s*:', re.MULTILINE)
JS_CLASS_RE = re.compile(r'^\s*(?:export\s+)?(?:default\s+)?class\s+(\w+)(?:\s+extends\s+([\w.]+))?', re.MULTILINE)
JAVA_CLASS_RE = re.compile(
    r'^\s*(?:public|private|protected)?\s*(?:abstract\s+|final\s+)?class\s+(\w+)(?:\s+extends\s+(\w+))?',
    re.MULTILINE,
)
RUBY_CLASS_RE = re.compile(r'^\s*class\s+(\w+)(?:\s*<\s*([\w:]+))?', re.MULTILINE)
GO_STRUCT_RE = re.compile(r'^\s*type\s+(\w+)\s+struct\b', re.MULTILINE)


def detect_language(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    return LANG_BY_EXT.get(ext)


def extract_raw_imports(file_path, text):
    lang = detect_language(file_path)
    if lang == 'python':
        results = []
        for m in PY_FROM_IMPORT_RE.finditer(text):
            module, names_part = m.group(1), m.group(2)
            if module.strip('.') == '' and module:
                # "from . import x, y" / "from .. import x" — each name is itself a submodule
                # relative to the dotted package, e.g. "from . import json" -> ".json"
                for name in names_part.split(','):
                    name = name.strip().split(' as ')[0].strip()
                    if name and re.match(r'^\w+$', name):
                        results.append(f'{module}{name}')
            elif module:
                results.append(module)
        for m in PY_PLAIN_IMPORT_RE.finditer(text):
            for part in m.group(1).split(','):
                part = part.strip().split(' as ')[0].strip()
                if part:
                    results.append(part)
        return results
    if lang == 'javascript':
        return [m.group(1) or m.group(2) for m in JS_IMPORT_RE.finditer(text)]
    if lang == 'java':
        return [m.group(1) for m in JAVA_IMPORT_RE.finditer(text)]
    if lang == 'go':
        return [m.group(1) for m in GO_IMPORT_RE.finditer(text)]
    if lang == 'ruby':
        return [m.group(1) for m in RUBY_REQUIRE_RE.finditer(text)]
    return []


PY_METHOD_RE = re.compile(r'^(\s*)(?:async\s+)?def\s+(\w+)\s*\(')
JS_METHOD_RE = re.compile(r'^(\s*)(?:async\s+)?(?:static\s+)?(?:get\s+|set\s+)?(\w+)\s*\([^)]*\)\s*\{')
JS_KEYWORDS = {
    'if', 'for', 'while', 'switch', 'catch', 'function', 'constructor', 'return',
    'else', 'do', 'try', 'finally',
}


def _extract_python_methods(text, header_indent, header_end):
    """Scans forward from a class header (Python, indentation-scoped) collecting method names
    until a line dedents back to the class's own indentation or shallower."""
    methods = []
    for line in text[header_end:].split('\n'):
        if line.strip() == '':
            continue
        indent = len(line) - len(line.lstrip(' '))
        if indent <= header_indent:
            break
        m = PY_METHOD_RE.match(line)
        if m:
            methods.append(m.group(2))
    return methods


def _extract_js_methods(text, header_indent, header_end):
    """Heuristic, indentation-scoped (JS classes conventionally follow consistent indentation
    even though the language itself is brace-delimited) — good enough for a best-effort diagram,
    not a real parser."""
    methods = []
    depth = 0
    started = False
    for line in text[header_end:].split('\n'):
        depth += line.count('{') - line.count('}')
        if '{' in line:
            started = True
        if started and depth <= 0:
            break
        if line.strip() == '':
            continue
        m = JS_METHOD_RE.match(line)
        if m and m.group(2) not in JS_KEYWORDS:
            methods.append(m.group(2))
    return methods


def extract_classes(file_path, text):
    """Best-effort class/struct extraction for the UML-style low-level diagram: name, direct
    parent(s) if the language expresses inheritance in the class header, the raw definition line
    (kept verbatim as free, no-LLM detail), and method names found in the class body (bounded by
    whatever text is available — typically just the first ~40 lines of the file)."""
    lang = detect_language(file_path)
    classes = []

    if lang == 'python':
        for m in PY_CLASS_RE.finditer(text):
            parents = []
            for p in (m.group(2) or '').split(','):
                p = p.strip()
                if p and '=' not in p and p != 'object':
                    parents.append(p)
            header_indent = len(m.group(0)) - len(m.group(0).lstrip())
            methods = _extract_python_methods(text, header_indent, m.end())
            classes.append({
                'name': m.group(1), 'parents': parents, 'definition': m.group(0).strip(), 'methods': methods,
            })
    elif lang == 'javascript':
        for m in JS_CLASS_RE.finditer(text):
            parents = [m.group(2)] if m.group(2) else []
            header_indent = len(m.group(0)) - len(m.group(0).lstrip())
            methods = _extract_js_methods(text, header_indent, m.end())
            classes.append({
                'name': m.group(1), 'parents': parents, 'definition': m.group(0).strip(), 'methods': methods,
            })
    elif lang == 'java':
        for m in JAVA_CLASS_RE.finditer(text):
            parents = [m.group(2)] if m.group(2) else []
            classes.append({'name': m.group(1), 'parents': parents, 'definition': m.group(0).strip(), 'methods': []})
    elif lang == 'ruby':
        for m in RUBY_CLASS_RE.finditer(text):
            parents = [m.group(2)] if m.group(2) else []
            classes.append({'name': m.group(1), 'parents': parents, 'definition': m.group(0).strip(), 'methods': []})
    elif lang == 'go':
        for m in GO_STRUCT_RE.finditer(text):
            classes.append({'name': m.group(1), 'parents': [], 'definition': m.group(0).strip(), 'methods': []})

    return classes


def _python_candidates(base_dir, module):
    dots = len(module) - len(module.lstrip('.'))
    rest = module.lstrip('.')
    if dots > 0:
        parts = base_dir.split('/') if base_dir else []
        up = dots - 1
        parts = parts[:-up] if up and up <= len(parts) else (parts if not up else [])
        prefix = '/'.join(parts)
        rest_path = rest.replace('.', '/') if rest else ''
        combined = '/'.join(p for p in [prefix, rest_path] if p)
    else:
        combined = rest.replace('.', '/')
    if not combined:
        return []
    return [f'{combined}.py', f'{combined}/__init__.py']


def _js_candidates(base_dir, spec):
    combined = os.path.normpath(os.path.join(base_dir, spec)).replace('\\', '/')
    candidates = [combined]
    for ext in ('.js', '.jsx', '.ts', '.tsx', '.mjs', '.cjs'):
        candidates.append(f'{combined}{ext}')
    for ext in ('.js', '.jsx', '.ts', '.tsx'):
        candidates.append(f'{combined}/index{ext}')
    return candidates


def resolve_internal(source_path, raw_import, file_set, top_level_dirs):
    lang = detect_language(source_path)
    base_dir = os.path.dirname(source_path)

    if lang == 'python':
        for c in _python_candidates(base_dir, raw_import):
            if c in file_set:
                return c
        top = raw_import.lstrip('.').split('.')[0]
        if top and top in top_level_dirs:
            guess = f'{top}/__init__.py'
            return guess if guess in file_set else None
        return None

    if lang == 'javascript':
        if not raw_import.startswith('.'):
            return None
        for c in _js_candidates(base_dir, raw_import):
            if c in file_set:
                return c
        return None

    if lang == 'java':
        suffix = raw_import.replace('.', '/') + '.java'
        for f in file_set:
            if f.endswith(suffix):
                return f
        return None

    if lang == 'go':
        last_segment = raw_import.rstrip('/').split('/')[-1]
        return last_segment if last_segment in top_level_dirs else None

    if lang == 'ruby':
        combined = os.path.normpath(os.path.join(base_dir, raw_import)).replace('\\', '/') \
            if raw_import.startswith('.') else raw_import
        for ext in ('', '.rb'):
            c = f'{combined}{ext}'
            if c in file_set:
                return c
        return None

    return None


def _looks_like_test_file(file_path):
    """Excludes test suites and auto-generated boilerplate from the class diagram: they're
    rarely architecturally interesting (mock classes, dummy fixtures, one class per test case
    or migration) and, since these directories are often among the largest by file count,
    they'd otherwise crowd out real domain classes."""
    segments = [s.lower() for s in file_path.split('/')]
    if any('test' in s or 'spec' in s or s == 'migrations' for s in segments[:-1]):
        return True
    basename = segments[-1]
    return (
        basename.startswith('test_') or basename.startswith('test.')
        or basename.endswith('_test.py') or basename == 'tests.py'
        or '.test.' in basename or '.spec.' in basename
    )


NOISY_CLASS_NAMES = {'Meta', 'Migration'}


def module_of(file_path):
    dir_path = os.path.dirname(file_path)
    if not dir_path:
        return '(root)'
    parts = dir_path.split('/')
    return '/'.join(parts[:2])


def build_module_graph(file_chunks, file_tree):
    file_set = set(file_tree)
    top_level_dirs = {p.split('/')[0] for p in file_tree if '/' in p}

    file_edge_counter = Counter()
    lang_counts = Counter()
    imports_found = 0
    imports_resolved = 0

    for file_path, text in file_chunks:
        lang = detect_language(file_path)
        if lang:
            lang_counts[lang] += 1
        raw_imports = extract_raw_imports(file_path, text)
        imports_found += len(raw_imports)
        for raw in raw_imports:
            target = resolve_internal(file_path, raw, file_set, top_level_dirs)
            if not target or target == file_path:
                continue
            imports_resolved += 1
            file_edge_counter[(file_path, target)] += 1

    # Split resolved imports into cross-module edges (the interesting architecture-level view)
    # and same-module edges (e.g. sibling files within one Django app / one flat package).
    module_edge_counter = Counter()
    same_module_file_edges = {}
    for (src, tgt), w in file_edge_counter.items():
        src_mod = module_of(src)
        tgt_mod = tgt if ('/' not in tgt and tgt in top_level_dirs) else module_of(tgt)
        if src_mod == tgt_mod:
            same_module_file_edges.setdefault(src_mod, Counter())[(src, tgt)] += w
        else:
            module_edge_counter[(src_mod, tgt_mod)] += w

    module_edges = [
        {'source': a, 'target': b, 'weight': w}
        for (a, b), w in module_edge_counter.most_common(60)
    ]

    module_file_counts = Counter(module_of(p) for p in file_tree)
    module_stats = [
        {'module': m, 'file_count': c}
        for m, c in module_file_counts.most_common(16)
    ]

    file_edges = [
        {'source': a, 'target': b, 'weight': w}
        for (a, b), w in file_edge_counter.most_common(200)
    ]

    return {
        'module_edges': module_edges,
        'file_edges': file_edges,
        'module_stats': module_stats,
        'language_counts': dict(lang_counts),
        'imports_found': imports_found,
        'imports_resolved': imports_resolved,
    }


def sanitize_id(name):
    return re.sub(r'[^A-Za-z0-9_]', '_', name) or 'root'


def _top_level_group(module):
    return module if module == '(root)' else module.split('/')[0]


_HLD_INIT_DIRECTIVE = "%%{init: {'flowchart': {'curve': 'basis', 'nodeSpacing': 20, 'rankSpacing': 18}}}%%"


_HLD_HORIZONTAL_THRESHOLD = 3


def _pick_direction(node_count):
    """A handful of boxes reads better laid out left-to-right — it fills the width naturally and
    doesn't leave a tall, mostly-empty column. Once there are enough boxes to make a single row
    unreadable (forcing horizontal scroll), fall back to stacking them vertically instead."""
    return 'LR' if node_count <= _HLD_HORIZONTAL_THRESHOLD else 'TB'


def _chain_lines(node_ids_in_order, indent='  '):
    """Mermaid flowcharts only respect a declared TB/LR direction reliably when there's an actual
    edge-based hierarchy to lay out; a set of mostly-disconnected boxes (the common case here —
    most repos have few or no cross-module edges) still gets packed into one wide horizontal row
    regardless of direction. Chaining every node with an invisible link ('~~~', Mermaid's
    layout-only connector) forces a deterministic order along the declared direction (top-to-bottom
    for TB, left-to-right for LR) without adding a visible arrow. classDiagram doesn't need this —
    its layout engine already respects direction TB even for sparse graphs."""
    return [f'{indent}{a} ~~~ {b}' for a, b in zip(node_ids_in_order, node_ids_in_order[1:])]


def to_mermaid_hld_overview(module_edges, module_stats, max_nodes=16, max_edges=40):
    """System-level overview: one box per top-level component/directory (e.g. "back", "docs",
    "tests"), sized by total file count, with edges rolled up from module-level cross-group
    dependencies. Always small (as many boxes as top-level directories, typically a handful),
    so it stays readable regardless of how many individual modules exist underneath each one."""
    if not module_stats:
        return 'graph TB\n  empty["No modules detected"]'

    top_modules = [s['module'] for s in module_stats[:max_nodes]]
    file_counts = {s['module']: s['file_count'] for s in module_stats}

    module_to_group = {m: _top_level_group(m) for m in top_modules}
    group_file_counts = Counter()
    for m in top_modules:
        group_file_counts[module_to_group[m]] += file_counts.get(m, 0)

    group_edge_counter = Counter()
    for edge in module_edges:
        src_group = module_to_group.get(edge['source'])
        tgt_group = module_to_group.get(edge['target'])
        if src_group and tgt_group and src_group != tgt_group:
            group_edge_counter[(src_group, tgt_group)] += edge['weight']

    ordered_groups = group_file_counts.most_common()
    direction = _pick_direction(len(ordered_groups))
    lines = [_HLD_INIT_DIRECTIVE, f'graph {direction}']
    node_ids = {}

    def node_id(group):
        if group not in node_ids:
            node_ids[group] = f'g{len(node_ids)}_{sanitize_id(group)}'
        return node_ids[group]

    for group, count in ordered_groups:
        label = group.replace('"', "'")
        files_word = 'file' if count == 1 else 'files'
        lines.append(f'  {node_id(group)}["{label} ({count} {files_word})"]')

    lines.extend(_chain_lines([node_id(g) for g, _ in ordered_groups]))

    for (src, tgt), _weight in group_edge_counter.most_common(max_edges):
        lines.append(f'  {node_id(src)} --> {node_id(tgt)}')

    return '\n'.join(lines)


def to_mermaid_hld_group_diagrams(module_edges, module_stats, max_nodes=16):
    """Per-component detail: a small diagram for each top-level directory that has more than one
    module, showing its modules stacked vertically with edges among them. Groups with a single
    module aren't worth a whole diagram — they're already fully represented by the overview."""
    if not module_stats:
        return []

    top_modules = [s['module'] for s in module_stats[:max_nodes]]
    file_counts = {s['module']: s['file_count'] for s in module_stats}

    groups = {}
    for module in top_modules:
        groups.setdefault(_top_level_group(module), []).append(module)

    diagrams = []
    for group, modules in sorted(groups.items(), key=lambda kv: -sum(file_counts.get(m, 0) for m in kv[1])):
        if len(modules) <= 1:
            continue

        module_set = set(modules)
        direction = _pick_direction(len(modules))
        lines = [_HLD_INIT_DIRECTIVE, f'graph {direction}']
        node_ids = {}

        def node_id(module):
            if module not in node_ids:
                node_ids[module] = f'm{len(node_ids)}_{sanitize_id(module)}'
            return node_ids[module]

        for module in modules:
            label = module.replace('"', "'")
            count = file_counts.get(module, 0)
            files_word = 'file' if count == 1 else 'files'
            lines.append(f'  {node_id(module)}["{label} ({count} {files_word})"]')

        lines.extend(_chain_lines([node_id(m) for m in modules]))

        for edge in module_edges:
            if edge['source'] in module_set and edge['target'] in module_set:
                lines.append(f"  {node_id(edge['source'])} --> {node_id(edge['target'])}")

        diagrams.append({'group': group, 'mermaid': '\n'.join(lines), 'module_count': len(modules)})

    return diagrams


def build_class_graph(file_chunks, file_tree, file_edges, max_classes=60, max_edges=90):
    """Low-level design data: extracted classes/structs grouped by module, with inheritance
    (where the language expresses it in the class header) and best-effort association edges
    derived from the existing file import graph. Returns None if no classes were found at all
    (e.g. a purely functional/procedural codebase)."""
    classes_by_file = {}
    for file_path, text in file_chunks:
        if _looks_like_test_file(file_path):
            continue
        found = [c for c in extract_classes(file_path, text) if c['name'] not in NOISY_CLASS_NAMES]
        if found:
            classes_by_file[file_path] = found

    if not classes_by_file:
        return None

    module_file_counts = Counter(module_of(p) for p in file_tree)
    files_in_priority_order = sorted(
        classes_by_file.keys(), key=lambda f: (-module_file_counts[module_of(f)], f),
    )

    classes = []
    node_ids = {}
    first_class_id_by_file = {}
    ids_by_name = {}

    for file_path in files_in_priority_order:
        if len(classes) >= max_classes:
            break
        for entry in classes_by_file[file_path]:
            if len(classes) >= max_classes:
                break
            node_id = f'c{len(classes)}_{sanitize_id(entry["name"])}'
            node_ids[(file_path, entry['name'])] = node_id
            record = {
                'id': node_id,
                'name': entry['name'],
                'parents': entry['parents'],
                'file_path': file_path,
                'module': module_of(file_path),
                'definition': entry['definition'],
                'methods': entry.get('methods', [])[:12],
            }
            classes.append(record)
            first_class_id_by_file.setdefault(file_path, node_id)
            ids_by_name.setdefault(entry['name'], node_id)

    # Matching a parent class purely by short name is unreliable across an entire repo: e.g. a
    # Django app literally named "app" generates a local class called `AppConfig(AppConfig)`,
    # which would otherwise name-collide with every *other* app's unrelated `extends AppConfig`
    # (Django's own external base class). Only trust a name match as real local inheritance when
    # it's grounded in an actual resolved import: same file, or the child's file has a resolved
    # import edge to the candidate parent's file.
    file_by_id = {record['id']: record['file_path'] for record in classes}
    file_edge_pairs = {(edge['source'], edge['target']) for edge in file_edges}

    inheritance_edges = []
    linked_pairs = set()
    for record in classes:
        for parent_name in record['parents']:
            short_name = parent_name.split('.')[-1].split('::')[-1]
            parent_id = ids_by_name.get(short_name)
            if not parent_id or parent_id == record['id']:
                continue
            parent_file = file_by_id[parent_id]
            if parent_file != record['file_path'] and (record['file_path'], parent_file) not in file_edge_pairs:
                continue
            inheritance_edges.append((record['id'], parent_id))
            linked_pairs.add((record['id'], parent_id))
            linked_pairs.add((parent_id, record['id']))

    association_edges = []
    for edge in file_edges:
        src_id = first_class_id_by_file.get(edge['source'])
        tgt_id = first_class_id_by_file.get(edge['target'])
        if not src_id or not tgt_id or src_id == tgt_id:
            continue
        if (src_id, tgt_id) in linked_pairs:
            continue
        association_edges.append((src_id, tgt_id))
        linked_pairs.add((src_id, tgt_id))
        linked_pairs.add((tgt_id, src_id))

    total_edge_budget = max_edges
    inheritance_edges = inheritance_edges[:total_edge_budget]
    association_edges = association_edges[:max(total_edge_budget - len(inheritance_edges), 0)]

    return {
        'classes': classes,
        'inheritance_edges': inheritance_edges,
        'association_edges': association_edges,
    }


def _heuristic_class_purpose(name, parents, file_path):
    """Free, deterministic fallback description based on common naming conventions (Django/DRF,
    Flask, common OOP suffixes) — always available, no LLM call needed."""
    lower_name = name.lower()
    parent_text = ' '.join(parents).lower()
    ext = os.path.splitext(file_path)[1].lower()

    if 'viewset' in lower_name or 'viewset' in parent_text:
        return 'Handles a set of related API endpoints (list/create/update/delete) for a resource.'
    if lower_name.endswith('view') or parent_text.split('.')[-1] in ('view', 'apiview'):
        return 'Handles HTTP requests for a specific endpoint or page.'
    if lower_name.endswith('serializer'):
        return "Converts a model's data to/from API request and response formats, with validation."
    if lower_name.endswith('admin'):
        return 'Configures how this model is displayed and managed in the admin panel.'
    if lower_name.endswith('config') or 'appconfig' in parent_text:
        return 'App configuration that registers this module with the framework.'
    if lower_name.endswith('form'):
        return "Defines and validates a form's input fields."
    if lower_name.endswith('manager'):
        return 'Provides custom query or creation logic for a model.'
    if 'model' in parent_text.split('.')[-1:] or parent_text.strip() == 'model':
        return 'A database model/table definition.'
    if ext in ('.jsx', '.tsx'):
        return 'A UI component.'
    if not parents:
        return 'A standalone class with no detected base class.'
    return f'A class extending {parents[0]}.'


def _heuristic_method_purpose(name):
    """Free, deterministic fallback for a method description based on common naming
    conventions — always available, no LLM call needed."""
    if name in ('__init__', 'constructor'):
        return 'Initializes a new instance of this class.'
    if name.startswith('get_'):
        return f'Retrieves {name[4:].replace("_", " ")}.'
    if name.startswith('set_'):
        return f'Sets {name[4:].replace("_", " ")}.'
    if name.startswith('is_') or name.startswith('has_'):
        return 'Checks a condition and returns true/false.'
    if name.startswith('validate'):
        return 'Validates input data.'
    if name.startswith('create') or name == 'perform_create':
        return 'Creates a new record or object.'
    if name.startswith('update') or name == 'perform_update':
        return 'Updates an existing record or object.'
    if name.startswith('delete') or name.startswith('remove') or name == 'perform_destroy':
        return 'Deletes or removes a record or resource.'
    if name == 'save':
        return 'Persists this object to the database.'
    if name.startswith('handle') or name.startswith('process'):
        return 'Handles or processes an event or request.'
    if name in ('get', 'post', 'put', 'patch', 'delete', 'render'):
        return f'Handles HTTP {name.upper()} requests.' if name != 'render' else 'Renders output/UI.'
    if name.startswith('_'):
        return 'An internal/helper method.'
    return 'A method on this class.'


def build_descriptions(classes, purposes_by_id=None, method_purposes_by_id=None):
    purposes_by_id = purposes_by_id or {}
    method_purposes_by_id = method_purposes_by_id or {}
    results = []
    for record in classes:
        method_purposes = method_purposes_by_id.get(record['id'], {})
        methods = [
            {'name': name, 'purpose': method_purposes.get(name) or _heuristic_method_purpose(name)}
            for name in record.get('methods', [])
        ]
        results.append({
            'id': record['id'],
            'name': record['name'],
            'file_path': record['file_path'],
            'module': record['module'],
            'parents': record['parents'],
            'definition': record['definition'],
            'methods': methods,
            'purpose': purposes_by_id.get(record['id']) or _heuristic_class_purpose(
                record['name'], record['parents'], record['file_path'],
            ),
        })
    return results


def to_mermaid_class_diagrams_by_module(class_graph):
    """Renders one small Mermaid classDiagram per module instead of a single combined diagram —
    Mermaid lays out disconnected clusters (unrelated modules) side by side horizontally, which
    becomes unreadable once there are more than a handful of modules. Only intra-module edges are
    drawn in each; cross-module relationships are already covered by the High-Level Design view.
    Returns a list of {module, mermaid, class_count}, largest modules first."""
    if class_graph is None:
        return []

    classes = class_graph['classes']
    by_module = {}
    for record in classes:
        by_module.setdefault(record['module'], []).append(record)

    module_of_id = {record['id']: record['module'] for record in classes}

    intra_inherit = {}
    for child_id, parent_id in class_graph['inheritance_edges']:
        if module_of_id.get(child_id) == module_of_id.get(parent_id):
            intra_inherit.setdefault(module_of_id[child_id], []).append((child_id, parent_id))

    intra_assoc = {}
    for src_id, tgt_id in class_graph['association_edges']:
        if module_of_id.get(src_id) == module_of_id.get(tgt_id):
            intra_assoc.setdefault(module_of_id[src_id], []).append((src_id, tgt_id))

    diagrams = []
    for module, members in sorted(by_module.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        lines = ['classDiagram', '  direction TB']
        for record in members:
            label = record['name'].replace('"', "'")
            lines.append(f'  class {record["id"]}["{label}"]')
            for method_name in record.get('methods', []):
                # Mermaid's label text treats a leading/trailing underscore as markdown italics
                # (so "__str__" renders as a garbled "()" with a stray "str") — strip them for
                # the diagram label only; the full name is still shown correctly in the
                # click-through description panel.
                safe_method = re.sub(r'[^A-Za-z0-9_]', '', method_name).strip('_') or 'method'
                lines.append(f'  {record["id"]} : +{safe_method}()')
        for child_id, parent_id in intra_inherit.get(module, []):
            lines.append(f'  {parent_id} <|-- {child_id}')
        for src_id, tgt_id in intra_assoc.get(module, []):
            lines.append(f'  {src_id} --> {tgt_id}')
        diagrams.append({'module': module, 'mermaid': '\n'.join(lines), 'class_count': len(members)})

    return diagrams
