def select_diverse(documents, metadatas, k):
    """Picks up to k chunks from a larger relevance-ranked pool, preferring one chunk per
    distinct file first so near-duplicate chunks from the same file/region (common with
    overlapping chunking) don't crowd out other genuinely relevant files. Falls back to filling
    remaining slots with the next-best chunks (any file) once every file has one pick."""
    by_file = {}
    for doc, meta in zip(documents, metadatas):
        by_file.setdefault(meta['file_path'], []).append((doc, meta))

    selected = []
    selected_set = set()

    # Pass 1: best chunk from each distinct file, in original relevance order.
    for doc, meta in zip(documents, metadatas):
        if len(selected) >= k:
            break
        file_path = meta['file_path']
        if file_path in selected_set:
            continue
        selected_set.add(file_path)
        selected.append((doc, meta))

    # Pass 2: fill any remaining slots with the next-best chunks regardless of file.
    if len(selected) < k:
        chosen_ids = {id(m) for _, m in selected}
        for doc, meta in zip(documents, metadatas):
            if len(selected) >= k:
                break
            if id(meta) in chosen_ids:
                continue
            selected.append((doc, meta))
            chosen_ids.add(id(meta))

    docs = [d for d, _ in selected]
    metas = [m for _, m in selected]
    return docs, metas
