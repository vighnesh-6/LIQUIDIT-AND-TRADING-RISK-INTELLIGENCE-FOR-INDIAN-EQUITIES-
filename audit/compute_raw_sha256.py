"""Cryptographic hash baseline and integrity verification utility.

Computes SHA-256 digests for all 303 raw Parquet files (300 stocks + 3 market indices)
and data manifest, writes baseline to audit/raw_data_sha256.json, and computes the
aggregate Merkle-style root hash of the stock universe.
"""

import hashlib
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
stocks_dir = PROJECT_ROOT / "data" / "raw" / "stocks"
market_dir = PROJECT_ROOT / "data" / "raw" / "market"
manifest_path = PROJECT_ROOT / "data" / "manifests" / "manifest_data_collection_20261024_150615.json"
output_json_path = Path(__file__).resolve().parent / "raw_data_sha256.json"


def hash_file(filepath: Path) -> str:
    """Computes SHA-256 hex digest of a file in 64 KB chunks."""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def main() -> None:
    market_hashes = {f.name: hash_file(f) for f in sorted(market_dir.glob("*.parquet"))}
    manifest_hash = hash_file(manifest_path) if manifest_path.exists() else None

    # Compute hashes for all 300 stocks
    stock_hashes = {f.name: hash_file(f) for f in sorted(stocks_dir.glob("*.parquet"))}

    # Compute an aggregate Merkle-style root hash of all 300 stock hashes
    stock_combined = "".join(f"{k}:{v}" for k, v in sorted(stock_hashes.items()))
    stock_root_hash = hashlib.sha256(stock_combined.encode("utf-8")).hexdigest()

    out = {
        "manifest_file": manifest_path.name if manifest_path.exists() else None,
        "manifest_sha256": manifest_hash,
        "market_files_sha256": market_hashes,
        "stock_files_count": len(stock_hashes),
        "stock_root_hash_sha256": stock_root_hash,
        "sample_stock_hashes": {k: stock_hashes[k] for k in list(stock_hashes.keys())[:10]},
    }

    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump({"stock_hashes": stock_hashes, "summary": out}, f, indent=2)

    print("Computed SHA-256 for all 303 raw Parquet files and manifest.")
    print(f"Manifest SHA-256: {manifest_hash}")
    print("Market files SHA-256:")
    for k, v in market_hashes.items():
        print(f"  {k}: {v}")
    print(f"Stock files total count: {len(stock_hashes)}")
    print(f"Stock aggregate root hash (SHA-256): {stock_root_hash}")

    # Baseline verification check
    EXPECTED_ROOT = "cdace0ba7662be9d0c49edca3f4db3ca00c2ef31c4704807db1bdef7cff0dcbf"
    if stock_root_hash == EXPECTED_ROOT:
        print("[VERIFIED] Stock Merkle root hash matches cryptographic baseline perfectly!")
    else:
        print(f"[WARNING] Stock Merkle root mismatch: expected {EXPECTED_ROOT}, got {stock_root_hash}")


if __name__ == "__main__":
    main()
