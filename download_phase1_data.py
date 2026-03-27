"""Backward-compatible wrapper.

SSOT enforcement: `data_downloader.py` is the active data ingestion entry point.
"""

from data_downloader import main


if __name__ == "__main__":
    main()
