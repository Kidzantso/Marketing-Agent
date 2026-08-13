from __future__ import annotations

from app.models import ChangeLogEntry, GraphSnapshot


def run(current: GraphSnapshot, previous: GraphSnapshot | None = None) -> list[ChangeLogEntry]:
    if previous is None:
        return [
            ChangeLogEntry(change_type="added", item=item, after=value)
            for item, value in sorted(current.nodes.items())
        ]
    changes: list[ChangeLogEntry] = []
    all_keys = set(previous.nodes) | set(current.nodes)
    for key in sorted(all_keys):
        before = previous.nodes.get(key)
        after = current.nodes.get(key)
        if before is None:
            changes.append(ChangeLogEntry(change_type="added", item=key, after=after))
        elif after is None:
            changes.append(ChangeLogEntry(change_type="removed", item=key, before=before))
        elif before != after:
            changes.append(ChangeLogEntry(change_type="modified", item=key, before=before, after=after))
    return changes
