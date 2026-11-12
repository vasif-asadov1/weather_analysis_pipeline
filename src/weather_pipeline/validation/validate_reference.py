import json
from pathlib import Path


RAW_PATH = Path(
    "data/raw/reference/turkiyeapi/provinces.json"
)

REQUIRED_FIELDS = (
    "id",
    "name",
    "population",
    "area",
    "altitude",
    "region",
    "coordinates",
)

EXPECTED_REGIONS = {
    "Akdeniz",
    "Doğu Anadolu",
    "Ege",
    "Güneydoğu Anadolu",
    "İç Anadolu",
    "Karadeniz",
    "Marmara",
}


def main() -> None:
    with RAW_PATH.open("r", encoding="utf-8") as file:
        provinces = json.load(file)

    if not isinstance(provinces, list):
        raise ValueError("Expected a JSON list.")

    errors = []

    ids = []
    names = []
    regions = set()

    missing_fields = {
        field: 0 for field in REQUIRED_FIELDS
    }

    for index, province in enumerate(provinces):
        if not isinstance(province, dict):
            errors.append(f"Record {index}: not an object")
            continue

        for field in REQUIRED_FIELDS:
            if field not in province:
                missing_fields[field] += 1

        province_id = province.get("id")
        name = province.get("name")

        if type(province_id) is not int:
            errors.append(f"Record {index}: invalid ID")
        else:
            ids.append(province_id)

        if not isinstance(name, str) or not name.strip():
            errors.append(f"Record {index}: invalid name")
        else:
            names.append(name)

        region = province.get("region", {})
        region_name = (
            region.get("tr")
            if isinstance(region, dict)
            else None
        )

        if not isinstance(region_name, str):
            errors.append(f"Record {index}: invalid region")
        else:
            regions.add(region_name)

        coordinates = province.get("coordinates", {})

        if not isinstance(coordinates, dict):
            errors.append(f"Record {index}: invalid coordinates")
        else:
            latitude = coordinates.get("latitude")
            longitude = coordinates.get("longitude")

            if (
                type(latitude) not in (int, float)
                or not 35 <= latitude <= 43
            ):
                errors.append(
                    f"Record {index}: invalid latitude"
                )

            if (
                type(longitude) not in (int, float)
                or not 25 <= longitude <= 46
            ):
                errors.append(
                    f"Record {index}: invalid longitude"
                )

        population = province.get("population")

        if (
            type(population) is not int
            or population < 0
        ):
            errors.append(
                f"Record {index}: invalid population"
            )

        area = province.get("area", {})

        if (
            not isinstance(area, dict)
            or type(area.get("value")) not in (int, float)
            or area["value"] <= 0
            or area.get("unit") != "km2"
        ):
            errors.append(f"Record {index}: invalid area")

        altitude = province.get("altitude", {})

        if (
            not isinstance(altitude, dict)
            or type(altitude.get("value")) not in (int, float)
            or altitude.get("unit") != "m"
        ):
            errors.append(f"Record {index}: invalid altitude")

    if len(provinces) != 81:
        errors.append(
            f"Expected 81 provinces, found {len(provinces)}"
        )

    if len(ids) != len(set(ids)):
        errors.append("Duplicate province IDs found")

    if len(names) != len(set(names)):
        errors.append("Duplicate province names found")

    if set(ids) != set(range(1, 82)):
        errors.append("Province IDs are not exactly 1–81")

    if regions != EXPECTED_REGIONS:
        errors.append("Geographic region set mismatch")

    print("=" * 50)
    print("TÜRKIYEAPI REFERENCE VALIDATION")
    print("=" * 50)

    print(f"Total records: {len(provinces)}")
    print(f"Unique IDs: {len(set(ids))}")
    print(f"Unique names: {len(set(names))}")
    print(f"Geographic regions: {len(regions)}")

    print("\nMissing top-level fields:")
    for field, count in missing_fields.items():
        print(f"  {field:<15} {count}")

    print("\nRegions:")
    for region in sorted(regions):
        print(f"  {region}")

    print("\nValidation result:")

    if errors:
        print(f"FAILED — {len(errors)} issue(s)")
        for error in errors:
            print(f"  - {error}")
        raise SystemExit(1)

    print("PASSED — all checks successful")


if __name__ == "__main__":
    main()