"""File contains logic of node(Directory, File, etc.) structure."""
from __future__ import annotations

from dataclasses import dataclass, field

from gen.nodes.base import AbstractLeafNode, AbstractNode


@dataclass(kw_only=True)
class File(AbstractLeafNode):
    """Represent a file entity."""

    size: int = field(kw_only=True, default=0)
    atime: str = field(kw_only=True, default='')
    mtime: str = field(kw_only=True, default='')


@dataclass(kw_only=True)
class HardLink(AbstractLeafNode):
    """Represent a hardlink entity."""

    file_obj: str


@dataclass
class SymLink(AbstractLeafNode):
    """Represent a symlink entity."""

    file_obj: AbstractNode = field(kw_only=True)
    atime: str = field(kw_only=True, default='')
    mtime: str = field(kw_only=True, default='')
    size: int = field(kw_only=True, default=0)


@dataclass
class Directory(AbstractNode):
    """Class represents directory entity."""


def main() -> None:
    """Usage example."""
    root_node = Directory(path='/', name='/', owner='root')
    root_node.add_node(File(path=root_node.full_path, name='root_file', owner='root'))

    inline_dirs = [Directory(path='/', name=f'inline_dir{_}', owner='root') for _ in range(5)]
    for inline_dir in inline_dirs:
        inline_dir.add_node(File(path=inline_dir.full_path, name='file', owner='user'))
        root_node.add_node(inline_dir)

    print('==================== Direct sub nodes ====================')
    for direct_sub_node in root_node.iter_sub_nodes():
        print(direct_sub_node)

    print('==================== Recursive all sub nodes ====================')
    for sub_node in root_node.iter_sub_nodes(scan_depth=1):
        print(sub_node)

    print('==================== Recursive only File sub nodes ====================')
    for file_sub_node in root_node.iter_sub_nodes(scan_depth=2, type_constraint=File):
        print(file_sub_node)

    print('==================== Recursive only Directory sub nodes ====================')
    for file_sub_node in root_node.iter_sub_nodes(scan_depth=3, type_constraint=Directory):
        print(file_sub_node)


if __name__ == '__main__':
    main()
