from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageOps


ROOT = Path(__file__).resolve().parents[1]


def render(source: str, outputs: list[tuple[str, int]], *, quality: int = 92, lossless: bool = False) -> list[dict]:
    source_path = ROOT / source
    with Image.open(source_path) as opened:
        image = ImageOps.exif_transpose(opened)
        icc_profile = image.info.get("icc_profile")
        results = []
        for destination, target_width in outputs:
            if target_width >= image.width:
                raise ValueError(f"Refusing to upscale {source} from {image.width}px to {target_width}px")

            target_height = round(image.height * target_width / image.width)
            resized = image.resize((target_width, target_height), Image.Resampling.LANCZOS)
            destination_path = ROOT / destination
            destination_path.parent.mkdir(parents=True, exist_ok=True)
            save_options = {
                "format": "WEBP",
                "method": 6,
                "exact": True,
                "lossless": lossless,
            }
            if not lossless:
                save_options["quality"] = quality
            if icc_profile:
                save_options["icc_profile"] = icc_profile
            resized.save(destination_path, **save_options)
            results.append(
                {
                    "source": source,
                    "source_width": image.width,
                    "source_height": image.height,
                    "source_bytes": source_path.stat().st_size,
                    "destination": destination,
                    "width": target_width,
                    "height": target_height,
                    "bytes": destination_path.stat().st_size,
                    "lossless": lossless,
                    "quality": None if lossless else quality,
                }
            )
        return results


jobs: list[tuple[str, list[tuple[str, int]], int, bool]] = []

jobs.append(
    (
        "assets/hero/hero-main.png",
        [(f"assets/hero/hero-main-{width}.webp", width) for width in (480, 800, 1200)],
        92,
        False,
    )
)

for sku in ("CS21", "CS22", "CS23", "CS35", "CS25", "CS30", "CS31", "CS28"):
    jobs.append(
        (
            f"assets/products/{sku}/{sku}(1).png",
            [(f"assets/products/{sku}/{sku}-1-{width}.webp", width) for width in (192, 384)],
            94,
            False,
        )
    )

for sku in ("CS100", "CS101", "CS11", "CS110", "CS12", "CS14", "CS21", "CS22", "CS23", "CS24", "CS25", "CS26", "CS27", "CS28", "CS29", "CS30", "CS31", "CS33", "CS34", "CS35"):
    jobs.append(
        (
            f"assets/products/{sku}/1.png",
            [(f"assets/products/{sku}/1-{width}.webp", width) for width in (320, 640)],
            92,
            False,
        )
    )

jobs.append(
    (
        "assets/logo/comfycare-logo.png",
        [(f"assets/logo/comfycare-logo-{width}.webp", width) for width in (64, 128)],
        100,
        True,
    )
)

for name in ("medical-standard", "effectiveness", "comfort", "official"):
    jobs.append(
        (
            f"assets/icons/hero/hero-icon-{name}.png",
            [(f"assets/icons/hero/hero-icon-{name}-{width}.webp", width) for width in (64, 128)],
            100,
            True,
        )
    )

for name in ("byt", "fda", "iso13485", "iso9001"):
    jobs.append(
        (
            f"assets/certifications/{name}.png",
            [(f"assets/certifications/{name}-{width}.webp", width) for width in (128, 256)],
            94,
            False,
        )
    )

jobs.append(
    (
        "assets/certifications/ccpit.webp",
        [(f"assets/certifications/ccpit-{width}.webp", width) for width in (128, 256)],
        94,
        False,
    )
)

jobs.append(
    (
        "assets/sections/why-choose/doctor.png",
        [(f"assets/sections/why-choose/doctor-{width}.webp", width) for width in (320, 640)],
        92,
        False,
    )
)

for index in range(1, 6):  # review 06 đã gỡ 22/10/2026 (lời khách hứa khỏi bệnh)
    name = f"review-shopee-{index:02d}"
    jobs.append(
        (
            f"assets/reviews/{name}.png",
            [(f"assets/reviews/{name}-{width}.webp", width) for width in (480, 800)],
            92,
            False,
        )
    )

jobs.append(
    (
        "assets/size-guide/measure-leg.png",
        [(f"assets/size-guide/measure-leg-{width}.webp", width) for width in (480, 800)],
        92,
        False,
    )
)

for name in ("how-to-wear-illustration",) + tuple(f"how-to-wear-step-{index:02d}" for index in range(1, 7)):
    jobs.append(
        (
            f"assets/guides/usage/{name}.png",
            [(f"assets/guides/usage/{name}-{width}.webp", width) for width in (480, 800)],
            92,
            False,
        )
    )

for source, stem in (
    ("assets/FDA.jpg", "assets/FDA"),
    ("assets/Iso 13485.png", "assets/Iso 13485"),
    ("assets/Iso 9001.png", "assets/Iso 9001"),
    ("assets/Hợp pháp lãnh sự.png", "assets/Hợp pháp lãnh sự"),
):
    jobs.append(
        (
            source,
            [(f"{stem}-{width}.webp", width) for width in (480, 800)],
            94,
            False,
        )
    )

for source_name, destination_name in (
    ("icon facebook.png", "icon-facebook"),
    ("icon zalo.png", "icon-zalo"),
    ("icon shopee.png", "icon-shopee"),
    ("icon tiktok.png", "icon-tiktok"),
):
    jobs.append(
        (
            f"assets/icons/{source_name}",
            [(f"assets/icons/{destination_name}-64.webp", 64)],
            100,
            True,
        )
    )

manifest: list[dict] = []
for source, outputs, quality, lossless in jobs:
    manifest.extend(render(source, outputs, quality=quality, lossless=lossless))

manifest_path = ROOT / "outputs/responsive-images/responsive-image-manifest.json"
manifest_path.parent.mkdir(parents=True, exist_ok=True)
manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

print(
    json.dumps(
        {
            "generated": len(manifest),
            "generated_bytes": sum(item["bytes"] for item in manifest),
            "unique_sources": len({item["source"] for item in manifest}),
            "manifest": str(manifest_path),
        },
        ensure_ascii=False,
    )
)
