"""The base class for any node(Directory, File, etc.) structure."""
from __future__ import annotations

import typing
from dataclasses import dataclass, field
from os import path


T = typing.TypeVar('T', bound='AbstractNode')


@dataclass
class AbstractNode(typing.Generic[T]):
    """Basic node entity params in unix system."""

    dest: str
    name: str
    owner: str
    _sub_nodes: list[T] = field(default_factory=list, init=False, repr=False)

    def add_node(self, node: T) -> None:
        """Add AbstractNode instance."""
        self._sub_nodes.append(node)

    @property
    def full_path(self) -> str:
        """Get full path of a file."""
        return path.join(self.dest, self.name)

    def sub_nodes_generator(
        self, type_constraint: type[T] | None = None, recursive: bool = False  # noqa: FBT001, FBT002
    ) -> typing.Generator[T, None, None]:
        """
        Allow iterating through all sub-nodes either directly or recursively.
        Allow type constraint for the nodes to limit the lookup results.
        """
        for sub_node in self._sub_nodes:
            if type_constraint is None or isinstance(sub_node, type_constraint):
                yield sub_node

            if recursive:
                yield from sub_node.sub_nodes_generator(recursive=True, type_constraint=type_constraint)

    def get_nodes_count(self, type_constraint: type[T] | None = None) -> int:
        """Get count of nodes in current node."""
        nodes_count = 0
        for _ in self.sub_nodes_generator(recursive=False, type_constraint=type_constraint):
            nodes_count += 1
        return nodes_count

    def get_all_nodes_count(self, type_constraint: type[T] | None = None) -> int:
        """Get count of nodes in current node and in the sub nodes."""
        nodes_count = 0
        for _ in self.sub_nodes_generator(recursive=True, type_constraint=type_constraint):
            nodes_count += 1
        return nodes_count


EMPTY_NODES: list[AbstractNode] = []


@dataclass(kw_only=True)
class AbstractLeafNode(AbstractNode):
    """Represent a Leaf node base - a node that cannot have sub-nodes."""

    _sub_nodes = EMPTY_NODES

    def add_node(self, node: object) -> typing.NoReturn:
        """Block adding sub-nodes for a Leaf."""
        err = f'Node type {type(self).__name__} cannot have sub-nodes!'
        raise TypeError(err)
