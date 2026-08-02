from llm.client import chat_completion
from vectorstore.client import get_first_chunks

from ..models import ArchitectureSnapshot
from .imports_parser import (
    build_class_graph,
    build_descriptions,
    build_module_graph,
    to_mermaid_class_diagrams_by_module,
    to_mermaid_hld_group_diagrams,
    to_mermaid_hld_overview,
)


def _generate_summary(repository, graph):
    top_modules = ', '.join(m['module'] for m in graph['module_stats'][:8]) or 'none detected'
    edge_source = graph['module_edges'] or graph['file_edges']
    edge_desc = '; '.join(
        f"{e['source']} -> {e['target']} ({e['weight']})" for e in edge_source[:15]
    ) or 'none detected'

    prompt = (
        f"Repository: {repository.owner}/{repository.name}\n"
        f"Description: {repository.description or 'N/A'}\n"
        f"Primary languages detected (by indexed file count): {graph['language_counts']}\n"
        f"Core modules (by file count): {top_modules}\n"
        f"Detected internal dependencies (source -> target, count): {edge_desc}\n\n"
        "In 3-5 sentences, describe this repository's high-level architecture for a developer who "
        "has never seen it before: what the main modules likely do and how they relate to each other. "
        "Be specific to the module names given, not generic."
    )
    return chat_completion([
        {'role': 'system', 'content': 'You are a senior engineer writing a concise architecture overview.'},
        {'role': 'user', 'content': prompt},
    ])


MAX_DESCRIPTION_PROMPT_LINES = 150
MAX_METHODS_PER_CLASS_IN_PROMPT = 5


def _generate_descriptions(classes):
    """Best-effort, single batched call covering every class AND its methods at once (not one
    call per class/method, which would blow a low-TPM free-tier budget). Capped to a bounded
    number of prompt lines for the same reason — anything beyond the cap, or if this call fails
    entirely, falls back to the heuristic descriptions in build_descriptions()."""
    if not classes:
        return {}, {}

    lines = []
    for record in classes:
        if len(lines) >= MAX_DESCRIPTION_PROMPT_LINES:
            break
        extends = f" extends {', '.join(record['parents'])}" if record['parents'] else ''
        lines.append(f"{record['id']}: class {record['name']}{extends} (in {record['file_path']})")
        for method_name in record.get('methods', [])[:MAX_METHODS_PER_CLASS_IN_PROMPT]:
            if len(lines) >= MAX_DESCRIPTION_PROMPT_LINES:
                break
            lines.append(f"{record['id']}.{method_name}: method `{method_name}` of class {record['name']}")

    prompt = (
        "For each item below (a class, or a `ClassId.method_name` method of that class), respond "
        "with EXACTLY one line in the format `<id>: <one short, simple, plain-language sentence "
        "describing what it is responsible for>`, in the same order, one per line, no extra "
        "commentary before or after, no markdown.\n\n" + '\n'.join(lines)
    )

    response = chat_completion([
        {'role': 'system', 'content': 'You explain what code classes and methods do in plain, simple language for beginners.'},
        {'role': 'user', 'content': prompt},
    ])

    class_purposes = {}
    method_purposes = {}
    for line in (response or '').splitlines():
        if ':' not in line:
            continue
        key, desc = line.split(':', 1)
        key, desc = key.strip(), desc.strip()
        if '.' in key:
            class_id, method_name = key.split('.', 1)
            method_purposes.setdefault(class_id, {})[method_name] = desc
        else:
            class_purposes[key] = desc
    return class_purposes, method_purposes


def generate_architecture(repository, force=False):
    if not force:
        existing = ArchitectureSnapshot.objects.filter(repository=repository).first()
        if existing:
            return existing, False

    chunks_result = get_first_chunks(repository.id)
    documents = chunks_result.get('documents') or []
    metadatas = chunks_result.get('metadatas') or []
    file_chunks = [(meta['file_path'], doc) for doc, meta in zip(documents, metadatas)]

    graph = build_module_graph(file_chunks, repository.file_tree or [])
    hld_mermaid = to_mermaid_hld_overview(graph['module_edges'], graph['module_stats'])
    hld_group_diagrams = to_mermaid_hld_group_diagrams(graph['module_edges'], graph['module_stats'])

    class_graph = build_class_graph(file_chunks, repository.file_tree or [], graph['file_edges'])
    lld_diagrams = to_mermaid_class_diagrams_by_module(class_graph)

    classes = class_graph['classes'] if class_graph else []
    try:
        purposes_by_id, method_purposes_by_id = _generate_descriptions(classes)
    except Exception:
        purposes_by_id, method_purposes_by_id = {}, {}
    lld_descriptions = build_descriptions(classes, purposes_by_id, method_purposes_by_id)

    try:
        summary = _generate_summary(repository, graph)
    except Exception:
        summary = ''

    snapshot, _ = ArchitectureSnapshot.objects.update_or_create(
        repository=repository,
        defaults={
            'hld_mermaid': hld_mermaid,
            'hld_group_diagrams': hld_group_diagrams,
            'lld_diagrams': lld_diagrams,
            'lld_descriptions': lld_descriptions,
            'summary': summary,
            'module_stats': graph['module_stats'],
        },
    )
    return snapshot, True
