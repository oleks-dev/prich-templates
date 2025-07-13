import shutil
import zipfile
import hashlib
import yaml
import json
from pathlib import Path

TEMPLATES_DIR = Path("templates")
DIST_DIR = Path("dist")
TMP_DIR = Path("tmp")
INDEX_FILE = TEMPLATES_DIR / "index.json"


def zip_template_folder(folder: Path, output_zip: Path) -> str:
    with zipfile.ZipFile(output_zip, "w", compression=zipfile.ZIP_DEFLATED) as zipf:
        for file in folder.rglob("*"):
            if file.is_file():
                zipf.write(file, arcname=file.relative_to(folder.parent))
    return compute_sha256(output_zip)


def compute_sha256(file_path: Path) -> str:
    sha256 = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def main():
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    templates = []

    print("Generating distributive archives of templates with index")
    for subfolder in sorted(TEMPLATES_DIR.iterdir()):
        if not subfolder.is_dir():
            continue

        template_id = subfolder.name
        try:
            zip_name = f"{template_id}.zip"
            zip_path = DIST_DIR / zip_name
            zip_tmp_path = TMP_DIR / f"{zip_name}.tmp"

            checksum = zip_template_folder(subfolder, zip_tmp_path)

            shutil.move(zip_tmp_path, zip_path)

            with open(TEMPLATES_DIR / template_id / f"{template_id}.yaml") as template_file:
                template = template_file.read()
            template = yaml.safe_load(template)

            templates.append({
                "id": template_id,
                "name": template.get("name"),
                "description": template.get("description"),
                "version": template.get("version"),
                "version_schema": template.get("version_schema"),
                "archive": f"{DIST_DIR.name}/{zip_name}",
                "checksum": checksum
            })
            print(f"- Archived {template_id}: {zip_path}")
        except Exception as e:
            print(f"- Failed to prepare {template_id}: {e}")

    print(f"Save index file: {INDEX_FILE}")
    INDEX_FILE.parent.mkdir(parents=True, exist_ok=True)
    with INDEX_FILE.open("w") as f:
        f.write(json.dumps({
            "name": "prich templates",
            "templates": templates
        }, sort_keys=False, indent=2))

    print(f"Generated {len(templates)} template archives and updated {INDEX_FILE}")


if __name__ == "__main__":
    main()