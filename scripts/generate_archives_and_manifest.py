import sys
import hashlib
import yaml
import json
from pathlib import Path
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

TEMPLATES_DIR = Path("templates")
MANIFEST_SCHEMA_VERSION = "1.0"
MANIFEST_FILE = TEMPLATES_DIR / "manifest.json"
MANIFEST_MD_FILE = TEMPLATES_DIR / "README.md"

FIXED_DT = (1980, 1, 1, 0, 0, 0)        # ZIP min timestamp
FILE_MODE = 0o100644                    # regular file with 0644 perms
DIR_MODE = 0o040755                     # dir with 0755 perms

def zip_template_folder(folder: Path, output_zip: Path) -> (str, list):
    output_zip.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output_zip, "w", compression=ZIP_DEFLATED) as zipf:
        top = folder.name + "/"
        zi = ZipInfo(top, FIXED_DT)
        zi.create_system = 3  # Unix
        zi.external_attr = (DIR_MODE << 16)
        zi.extra = b""
        zi.comment = b""
        zipf.writestr(zi, b"")
        files = []

        for file in folder.rglob("*"):
            if file.is_file():
                rel = file.relative_to(folder.parent).as_posix()
                files.append(rel)
                data = file.read_bytes()
                zi = ZipInfo(f"{folder.name}/{rel}")
                zi.create_system = 3
                zi.external_attr = (FILE_MODE << 16)
                zi.extra = b""
                zi.comment = b""
                zi.compress_type = ZIP_DEFLATED
                zipf.writestr(zi, data)

    return compute_sha256(output_zip), files

def compute_sha256(file_path: Path) -> str:
    sha256 = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def iter_files(base: Path):
    for p in sorted(base.rglob("*")):
        if p.is_file():
            yield p

def directory_hash(dir_path: Path) -> tuple[str, list[str]]:
    h = hashlib.sha256()
    dir_files_list = []
    for p in iter_files(dir_path):
        rel = p.relative_to(dir_path).as_posix()
        dir_files_list.append(str(rel))
        # hash path + normalized type/perms + file bytes
        h.update(b"PATH\x00" + rel.encode("utf-8"))
        h.update(b"MODE\x00" + str(FILE_MODE).encode())
        with p.open("rb") as f:
            while True:
                chunk = f.read(1024 * 1024)
                if not chunk:
                    break
                h.update(chunk)
    return h.hexdigest(), dir_files_list

def generate_md_file(manifest_data):
    md_content = [
        f"# {manifest_data.get('name')}  ",
        f"{manifest_data.get('description')}",
        "",
        "| ID   | Name  | Description | Tags  | Version | Author | Folder Checksum |",
        "| :--- | :---: |    :---:    | :---: |  :---:  | :---:  | :---            |",
    ]
    templates = sorted(manifest_data.get("templates"), key=lambda x: x["id"])
    for template in templates:
        md_content.append(f"| [{template.get('id')}]({manifest_data.get('templates_path')}/{template.get('id')}) | {template.get('name')} | {template.get('description')} | {', '.join(template.get('tags'))} | {template.get('version')} | {template.get('author')} | {template.get('folder_checksum')[:7]} |")
    md_content.append("")
    md_content.append(f"Manifest file: [manifest.json]({manifest_data.get('templates_path')}/manifest.json)")

    with open(MANIFEST_MD_FILE, "w") as file:
        for line in md_content:
            file.write(f"{line}\n")

    print(f"Generated {MANIFEST_MD_FILE}")

def save_manifest(m: dict):
    MANIFEST_FILE.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_FILE.write_text(json.dumps(m, indent=2, sort_keys=True))

def load_manifest() -> (dict, bool):
    need_to_save = False
    main_fields_dict = {
        "name": "prich Templates",
        "repository": "https://github.com/oleks-dev/prich-templates",
        "description": "Templates Available for Installation from prich-templates GitHub Repository",
        "templates_path": "https://github.com/oleks-dev/prich-templates/tree/main/templates",
        "schema_version": MANIFEST_SCHEMA_VERSION,
    }
    if MANIFEST_FILE.exists():
        manifest = json.loads(MANIFEST_FILE.read_text())
        # remove old keys
        loaded_manifest_keys = list(manifest.keys())
        for k in loaded_manifest_keys:
            if k != 'templates':
                if k not in main_fields_dict:
                    manifest.pop(k)
                    if not need_to_save:
                        need_to_save = True
        # remove add changes
        for k,v in main_fields_dict.items():
            if manifest.get(k) != v:
                manifest[k] = v
                if not need_to_save:
                    need_to_save = True
    else:
        manifest = main_fields_dict
        manifest["templates"] = []
        need_to_save = True
    return manifest, need_to_save

def get_template_from_manifest(manifest, template_id):
    for template in manifest.get("templates") or []:
        if template.get("id") == template_id:
            return template
    return {}


def main(force: bool = False):
    manifest, need_to_save_manifest = load_manifest()
    updated = 0

    print("Generating distributive archives of templates with manifest")
    for subfolder in sorted(TEMPLATES_DIR.iterdir()):
        if not subfolder.is_dir():
            continue

        template_id = subfolder.name
        manifest_item = get_template_from_manifest(manifest, str(template_id))
        current_hash, templates_files = directory_hash(subfolder)
        prev_hash = manifest_item.get("folder_checksum")

        if current_hash != prev_hash or force:
            try:
                folder_checksum = current_hash

                updated += 1

                with open(TEMPLATES_DIR / template_id / f"{template_id}.yaml") as template_file:
                    template = template_file.read()
                template = yaml.safe_load(template)

                manifest_item = get_template_from_manifest(manifest, template_id)
                changed_template = {
                        "id": template_id,
                        "name": template.get("name"),
                        "description": template.get("description"),
                        "tags": template.get("tags"),
                        "author": template.get("author"),
                        "version": template.get("version"),
                        "schema_version": template.get("schema_version"),
                        "folder_checksum": folder_checksum,
                        "files": templates_files
                    }
                if manifest_item:
                    manifest['templates'].remove(manifest_item)
                manifest['templates'].append(changed_template)
                print(f"- Updated {template_id}")
            except Exception as e:
                print(f"- Failed to prepare {template_id}: {e}")
        else:
            print(f"- Skip {template_id} (no changes)")

    if need_to_save_manifest or updated > 0:
        if need_to_save_manifest:
            print("Manifest fields change detected")
        print(f"Save manifest file: {MANIFEST_FILE}")
        save_manifest(manifest)
        print(f"Save manifest readme file: {MANIFEST_MD_FILE}")
        generate_md_file(manifest)
        print(f"Generated {updated} template archives, updated {MANIFEST_FILE} and {MANIFEST_MD_FILE}")
    else:
        print("Nothing to do")

if __name__ == "__main__":
    main(force='--force' in sys.argv)
