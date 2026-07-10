import ast
import py_compile
import xml.dom.minidom
from pathlib import Path

ADDON_DIR = Path(__file__).resolve().parent.parent / "customer_operations_dashboard"


def _python_files():
    return sorted(ADDON_DIR.rglob("*.py"))


def _xml_files():
    return sorted(ADDON_DIR.rglob("*.xml"))


def test_addon_directory_exists():
    assert ADDON_DIR.is_dir(), f"expected addon at {ADDON_DIR}"


def test_manifest_is_valid_dict_with_required_keys():
    manifest_path = ADDON_DIR / "__manifest__.py"
    assert manifest_path.is_file()
    manifest = ast.literal_eval(manifest_path.read_text())
    assert isinstance(manifest, dict)
    for key in ("name", "version", "depends", "data"):
        assert key in manifest, f"manifest missing required key: {key}"


def test_all_python_files_compile():
    files = _python_files()
    assert files, "expected at least one .py file in the addon"
    for f in files:
        py_compile.compile(str(f), doraise=True)


def test_all_xml_files_are_well_formed():
    for f in _xml_files():
        xml.dom.minidom.parse(str(f))
