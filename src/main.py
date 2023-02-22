"""File contains logic of node(Directory, File, etc.) structure."""
from __future__ import annotations

from dataclasses import dataclass, field

from gen.nodes.base import EMPTY_NODES, AbstractNode


@dataclass(kw_only=True)
class File(AbstractNode):
    """Represent a file entity."""

    size: int = field(kw_only=True, default=0)
    atime: str = field(kw_only=True, default='')
    mtime: str = field(kw_only=True, default='')
    _sub_nodes = EMPTY_NODES


@dataclass(kw_only=True)
class HardLink(AbstractNode):
    """Represent a hardlink entity."""

    file_obj: str
    _sub_nodes = EMPTY_NODES


@dataclass
class SymLink(AbstractNode):
    """Represent a symlink entity."""

    file_obj: AbstractNode = field(kw_only=True)
    atime: str = field(kw_only=True, default='')
    mtime: str = field(kw_only=True, default='')
    size: int = field(kw_only=True, default=0)
    _sub_nodes = EMPTY_NODES


@dataclass
class Directory(AbstractNode):
    """Class represents directory entity."""


def main() -> None:
    """Usage example."""
    root_node = Directory(path='/', name='/', owner='root')

    inline_dirs = [Directory(path='/', name=f'inline_dir{_}', owner='root') for _ in range(5)]
    for inline_dir in inline_dirs:
        inline_dir.add_node(File(path=inline_dir.full_path, name='file', owner='user'))
        root_node.add_node(inline_dir)

    print('==================== Direct sub nodes ====================')
    for direct_sub_node in root_node.sub_nodes_generator():
        print(direct_sub_node)

    print('==================== Recursive all sub nodes ====================')
    for sub_node in root_node.sub_nodes_generator(recursive=True):
        print(sub_node)

    print('==================== Recursive only File sub nodes ====================')
    for file_sub_node in root_node.sub_nodes_generator(recursive=True, type_constraint=File):
        print(file_sub_node)


if __name__ == '__main__':
    main()
