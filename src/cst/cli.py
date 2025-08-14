from __future__ import annotations

import argparse


def main() -> None:
	parser = argparse.ArgumentParser(prog="cst", description="CST CLI (skeleton)")
	subparsers = parser.add_subparsers(dest="command", required=True)

	# hello command
	hello_parser = subparsers.add_parser("hello", help="print a greeting")
	hello_parser.add_argument("--name", default="world", help="name to greet")

	args = parser.parse_args()

	if args.command == "hello":
		print(f"hello, {args.name}")
		return

	parser.print_help()


if __name__ == "__main__":
	main()
