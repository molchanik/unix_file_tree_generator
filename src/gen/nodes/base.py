"""The base class for any node(Directory, File, etc.) structure."""
from __future__ import annotations

import typing
from dataclasses import dataclass, field
from os import path


T = typing.TypeVar('T', bound='AbstractNode')


@dataclass(kw_only=True)
class AbstractNode(typing.Generic[T]):
    """Basic node entity params in unix system."""

    path: str
    name: str
    owner: str
    _sub_nodes: list[T] = field(default_factory=list, init=False, repr=False)

    def add_node(self, node: T) -> None:
        """Add AbstractNode instance."""
        self._sub_nodes.append(node)

    def __len__(self) -> int:
        """Return the sub-nodes count."""
        return len(self._sub_nodes)

    @property
    def full_path(self) -> str:
        """Get full path of a file."""
        return path.join(self.path, self.name)

    def sub_nodes_generator(
        self, type_constraint: type[T] | None = None, recursive: bool = False
    ) -> typing.Generator[T, None, None]:
        """
        Allow iterating through all sub-nodes either directly or recursively.
        Allow type constraint for the nodes to limit the lookup results.
        """
        for sub_node in self._sub_nodes:
            if type_constraint is None:
                yield sub_node
            else:
                if isinstance(sub_node, type_constraint):
                    yield sub_node

            if recursive:
                yield from sub_node.sub_nodes_generator(recursive=True, type_constraint=type_constraint)


EMPTY_NODES: list[AbstractNode] = []
