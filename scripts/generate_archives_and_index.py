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
INDEX_MD_FILE = TEMPLATES_DIR / "index.md"


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

def generate_md_file(index_data):
    md_content = [
        f"# {index_data.get('name')}  ",
        "",
        "| ID   | Name  | Description | Tags  | Version | Author | Archive |",
        "| :--- | :---: |    :---:    | :---: |  :---:  | :---:  | :---    |"
    ]
    templates = sorted(index_data.get("templates"), key=lambda x: x["id"])
    for template in templates:
        md_content.append(f"| {template.get('id')} | {template.get('name')} | {template.get('description')} | {', '.join(template.get('tags'))} | {template.get('version')} | {template.get('author')} | [{template.get('archive').split('/')[1]}](https://raw.githubusercontent.com/oleks-dev/prich-templates/main/{template.get('archive')})")

    with open(INDEX_MD_FILE, "w") as file:
        for line in md_content:
            file.write(f"{line}\n")

    print(f"Generated {INDEX_MD_FILE}")

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
                "tags": template.get("tags"),
                "author": template.get("author"),
                "version": template.get("version"),
                "schema_version": template.get("schema_version"),
                "archive": f"{DIST_DIR.name}/{zip_name}",
                "checksum": checksum
            })
            print(f"- Archived {template_id}: {zip_path}")
        except Exception as e:
            print(f"- Failed to prepare {template_id}: {e}")

    print(f"Save index file: {INDEX_FILE}")
    INDEX_FILE.parent.mkdir(parents=True, exist_ok=True)
    index_file_content = {
        "name": "Prich Templates Available for Installation from prich-templates GitHub Repository",
        "templates": templates
    }
    with INDEX_FILE.open("w") as f:
        f.write(json.dumps(index_file_content, sort_keys=False, indent=2))

    print(f"Generated {len(templates)} template archives and updated {INDEX_FILE}")

    generate_md_file(index_file_content)

if __name__ == "__main__":
    main()