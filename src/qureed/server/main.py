from __future__ import annotations

import argparse

import uvicorn


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the QuReed local server."
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument(
        "--project-root",
        help="Project directory containing qureed.toml",
    )
    args = parser.parse_args()

    from qureed.server.app import create_app

    uvicorn.run(
        create_app(args.project_root, serve_frontend=False),
        host=args.host,
        port=args.port,
    )


if __name__ == "__main__":
    main()
