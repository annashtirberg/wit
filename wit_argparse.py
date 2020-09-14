import argparse


WitArguments = argparse.Namespace


class WitArgparse(object):
    def __init__(self):
        parser = argparse.ArgumentParser(prog="wit")
        subparsers = parser.add_subparsers(dest="command", required=True, help="Wit command to execute")

        # Create parser for the "init" command
        subparsers.add_parser("init", help="initiate wit repository")

        # Create parser for the "add" command
        parser_add = subparsers.add_parser("add", help="add file to the staging area")
        parser_add.add_argument("add_paths", action="append", nargs="*", help="file or directory to add",
                                metavar="path")

        # Create parser for the "commit" command
        parser_commit = subparsers.add_parser("commit", help="create a commit")
        parser_commit.add_argument("message")

        # Create parser for the "status" command
        subparsers.add_parser("status", help="show current status")

        # Create parser for the "checkout" command
        parser_checkout = subparsers.add_parser("checkout", help="Checkout a specific commit")
        parser_checkout.add_argument("commit_name", help="Branch name or commit id")

        # Create parser for the "graph" command
        subparsers.add_parser("graph", help="Show wit graph")

        # Create parser for the "diff" command
        parser_diff = subparsers.add_parser("diff", help="Show comparison between commits")
        parser_diff_mutual_exclusive_group = parser_diff.add_mutually_exclusive_group()
        parser_diff_mutual_exclusive_group.add_argument("--cached", action="store_true", dest="is_cached",
                                                        help="Use staging area as base for comparison")
        parser_diff.add_argument("old_commit", nargs="?", metavar="commit",
                                 help="Commit name to compare with")
        parser_diff_mutual_exclusive_group.add_argument("new_commit", nargs="?", metavar="newer_commit",
                                                        help="Second commit to compare with")

        self.parser = parser

    def parse(self) -> WitArguments:
        return self.parser.parse_args()  # type: WitArguments
