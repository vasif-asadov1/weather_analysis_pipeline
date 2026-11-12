import json

import httpx


URL = "https://api.turkiyeapi.dev/v2/datasets/provinces.json"


def main():
    with httpx.Client(timeout=30.0) as client:
        response = client.get(URL)
        response.raise_for_status()

    provinces = response.json()

    print(f"Response type: {type(provinces).__name__}")
    print(f"Total records: {len(provinces)}")

    if not isinstance(provinces, list) or not provinces:
        raise ValueError("Expected a non-empty list of provinces.")

    print("\nFirst province — original JSON structure:")
    print(json.dumps(provinces[0], ensure_ascii=False, indent=2))

    print("\nAvailable top-level fields:")
    for field in provinces[0]:
        print(f"  - {field}")


if __name__ == "__main__":
    main()