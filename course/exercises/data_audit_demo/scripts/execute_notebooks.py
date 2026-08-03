#!/usr/bin/env python3
"""Execute both notebooks from a clean kernel and save ignored QA copies."""

from __future__ import annotations

from pathlib import Path

import nbformat
from nbclient import NotebookClient


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOKS = ROOT / "notebooks"
EXECUTED = ROOT / "executed"


def execute(name: str) -> None:
    source = NOTEBOOKS / name
    target = EXECUTED / name
    notebook = nbformat.read(source, as_version=4)
    client = NotebookClient(
        notebook,
        timeout=60,
        kernel_name="python3",
        resources={"metadata": {"path": str(ROOT)}},
    )
    client.execute()
    target.parent.mkdir(parents=True, exist_ok=True)
    nbformat.write(notebook, target)

    errors = []
    for cell in notebook.cells:
        for output in cell.get("outputs", []):
            if output.get("output_type") == "error":
                errors.append(output.get("ename", "unknown error"))
    if errors:
        raise RuntimeError(f"{name}: {errors}")
    print(f"Executed cleanly: {name}")


def main() -> None:
    execute("01_demo_inicial.ipynb")
    execute("02_demo_resuelto.ipynb")


if __name__ == "__main__":
    main()
