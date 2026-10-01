"""Compatibility entry point for the current DAY 1 report."""
from pathlib import Path
import runpy

if __name__ == '__main__':
    runpy.run_path(str(Path(__file__).with_name('build_day1_final_pdf.py')), run_name='__main__')
