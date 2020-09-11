from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from graphviz import Digraph

if TYPE_CHECKING:
    from wit import Wit
    from wit_commit import WitCommit


class WitGraph(object):
    GRAPH_FILE_NAME = "graph.gv"

    def __init__(self, wit: Wit):
        self.wit = wit
        self.wit_directory = wit.wit_base_directory_path

    def _add_node(self, grpc: Digraph, commit: WitCommit):
        grpc.node(f'{commit.commit_id}', f'{commit.commit_id}', shape="circle", color="blue", style="filled",
                  fillcolor="blue", fontcolor="#FFFFFF")

    def _add_edge(self, grpc: Digraph, commit: Optional[WitCommit] = None,
                  parent: Optional[WitCommit] = None, label: str = ""):
        commit_id = ""
        parent_id = ""
        if commit is not None:
            commit_id = commit.commit_id
        if parent is not None:
            parent_id = parent.commit_id

        grpc.edge(f'{commit_id}', f'{parent_id}', label=label, constraint='false', color="blue")

    def _add_tag(self, grpc: Digraph, commit: WitCommit, label: str):
        grpc.edge('', f'{commit.commit_id}', label=f'{label}::sw')

    def _add_parent(self, grpc: Digraph, commit: WitCommit):
        parent = commit.get_parent()
        if parent is not None:
            self._add_node(grpc, parent)
            self._add_edge(grpc, commit, parent)
            self._add_parent(grpc, parent)

    def show(self):
        grpc = Digraph(comment='graph')
        head_id = self.wit.references.get_head()
        head_commit = self.wit.commits[head_id]
        self._add_node(grpc, head_commit)
        self._add_parent(grpc, head_commit)
        for tag_name, commit_id in self.wit.references.items():
            commit = self.wit.commits[commit_id]
            self._add_tag(grpc, commit, tag_name)

        grpc.view(self.GRAPH_FILE_NAME, self.wit_directory, cleanup=True)
