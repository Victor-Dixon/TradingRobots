"""Offline unit tests for Phase-1 data acquisition pipeline."""

from __future__ import annotations

import unittest
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch

import pandas as pd

from catena_bot import data_downloader


class TestDataDownloader(unittest.TestCase):
    def test_env_raises_when_missing(self) -> None:
        with patch.dict("os.environ", {}, clear=True):
            with self.assertRaisesRegex(SystemExit, "Missing required env var"):
                data_downloader._env("APCA_API_KEY_ID")

    def test_fetch_stock_normalizes_columns_and_sorts(self) -> None:
        index = pd.MultiIndex.from_tuples(
            [
                ("TSLA", datetime(2026, 3, 27, 13, 31, tzinfo=timezone.utc)),
                ("TSLA", datetime(2026, 3, 27, 13, 30, tzinfo=timezone.utc)),
            ],
            names=["symbol", "timestamp"],
        )
        frame = pd.DataFrame(
            {
                "open": [251.0, 250.0],
                "high": [251.2, 250.2],
                "low": [250.8, 249.8],
                "close": [251.1, 250.1],
                "volume": [1200, 1000],
            },
            index=index,
        )

        client = MagicMock()
        client.get_stock_bars.return_value = MagicMock(df=frame)

        with patch.object(data_downloader, "_alpaca_types") as alpaca_types:
            stock_bars_request_cls = MagicMock(side_effect=lambda **kwargs: kwargs)
            fake_timeframe = type("FakeTimeFrame", (), {"Minute": "1Min"})
            alpaca_types.return_value = (MagicMock(), stock_bars_request_cls, fake_timeframe)
            result = data_downloader._fetch_stock(
                client,
                "TSLA",
                datetime(2026, 3, 27, 13, 0, tzinfo=timezone.utc),
                datetime(2026, 3, 27, 14, 0, tzinfo=timezone.utc),
            )

        self.assertEqual(
            list(result.columns), ["timestamp", "symbol", "open", "high", "low", "close", "volume"]
        )
        self.assertEqual(result.iloc[0]["close"], 250.1)
        self.assertEqual(result.iloc[1]["close"], 251.1)
        self.assertIn("UTC", str(result["timestamp"].dtype))

    def test_save_writes_symbol_files_and_slippage_columns(self) -> None:
        with TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            df = pd.DataFrame(
                {
                    "timestamp": [datetime(2026, 3, 27, 14, 0, tzinfo=timezone.utc)],
                    "symbol": ["QQQ"],
                    "open": [400.0],
                    "high": [401.0],
                    "low": [399.5],
                    "close": [400.5],
                    "volume": [1000],
                }
            )

            with patch.object(pd.DataFrame, "to_parquet") as to_parquet:
                data_downloader._save(df, output_dir, "/NQ", slippage_bps=5.0)

            to_parquet.assert_called_once()
            csv_path = output_dir / "_NQ_1m.csv"
            self.assertTrue(csv_path.exists())
            saved = pd.read_csv(csv_path)
            self.assertIn("slippage_bps", saved.columns)
            self.assertIn("slippage_pct", saved.columns)
            self.assertEqual(saved.loc[0, "slippage_bps"], 5.0)


if __name__ == "__main__":
    unittest.main()
