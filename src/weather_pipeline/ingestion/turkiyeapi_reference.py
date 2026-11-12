from pathlib import Path

import httpx


SOURCE_URL = "https://api.turkiyeapi.dev/v2/datasets/provinces.json"

OUTPUT_PATH = Path(
    "data/raw/reference/turkiyeapi/provinces.json"
)


def main() -> None:
    # Prevent accidental overwriting of existing raw data.
    if OUTPUT_PATH.exists():
        raise FileExistsError(
            f"Raw reference file already exists: {OUTPUT_PATH}"
        )

    # Retrieve the original API response.
    with httpx.Client(timeout=30.0) as client:
        response = client.get(SOURCE_URL)
        response.raise_for_status()

    # Preserve the response exactly as received.
    raw_content = response.content

    # Ensure the destination directory exists.
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Exclusive creation prevents overwriting an existing file.
    with OUTPUT_PATH.open("xb") as file:
        file.write(raw_content)

    print("Reference data downloaded successfully.")
    print(f"Source: {SOURCE_URL}")
    print(f"Saved to: {OUTPUT_PATH}")
    print(f"File size: {len(raw_content):,} bytes")


if __name__ == "__main__":
    main()