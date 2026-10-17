import argparse
import json
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[1]
sys.path = [str(project_root)] + [
    path for path in sys.path if path != str(project_root / "scripts")
]
from src.route_service import find_route


def main() -> None:
    parser = argparse.ArgumentParser(description="Check the CatTracks route engine.")
    parser.add_argument("--from-stop", required=True)
    parser.add_argument("--to-stop", required=True)
    args = parser.parse_args()

    result = find_route(args.from_stop, args.to_stop)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
