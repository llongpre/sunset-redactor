"""CLI entry point: python run.py <input_dir> [output_dir]"""
import sys
from redactor import pipeline


if __name__ == "__main__":
    input_dir = sys.argv[1] if len(sys.argv) > 1 else "tests/data/provided/inputs"
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "tests/data/provided/outputs"
    pipeline.run(input_dir, output_dir)
