"""Tracks entities across files and assigns consistent, kind-tagged placeholders."""
from redactor.models import Entity, PIIKind


class EntityRegistry:
    def __init__(self) -> None:
        self._map: dict[str, Entity] = {}        # normalized value -> Entity
        self._counters: dict[PIIKind, int] = {}  # kind -> next index

    def get_or_create(self, value: str, kind: PIIKind) -> Entity:
        key = value.lower().strip()
        if key not in self._map:
            n = self._counters.get(kind, 0) + 1
            self._counters[kind] = n
            placeholder = f"[{kind}_{n}]"
            self._map[key] = Entity(value=value, kind=kind, placeholder=placeholder)
        return self._map[key]

    def alias(self, value: str, entity: Entity) -> None:
        """Register an alternate representation pointing to an existing entity."""
        key = value.lower().strip()
        if key not in self._map:
            self._map[key] = entity

    def placeholder_for(self, value: str, kind: PIIKind) -> str:
        return self.get_or_create(value, kind).placeholder

    def all_entities(self) -> list[Entity]:
        return list(self._map.values())
