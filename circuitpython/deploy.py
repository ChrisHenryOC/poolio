#!/usr/bin/env python3
"""
Deploy CircuitPython code and libraries to device.

This script manages deployment of:
- Adafruit CircuitPython libraries from the bundle
- Project source code (shared/, node-specific code)
- Device test framework (optional)

Usage:
    python circuitpython/deploy.py --target pool-node
    python circuitpython/deploy.py --target valve-node --source
    python circuitpython/deploy.py --target test --device /Volumes/CIRCUITPY
"""

import argparse
import glob
import os
import shutil
import sys
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

# Bundle configuration
BUNDLE_VERSION = "9.x"
BUNDLE_DATE = "20241224"  # Update this when downloading newer bundle
BUNDLE_URL_TEMPLATE = (
    "https://github.com/adafruit/Adafruit_CircuitPython_Bundle/releases/download/"
    "{date}/adafruit-circuitpython-bundle-{version}-mpy-{date}.zip"
)

# Default paths
DEFAULT_DEVICE_PATH_MACOS = "/Volumes/CIRCUITPY"
DEFAULT_DEVICE_PATH_LINUX = "/media/{user}/CIRCUITPY"
SCRIPT_DIR = Path(__file__).parent
BUNDLE_DIR = SCRIPT_DIR / "bundle"
REQUIREMENTS_DIR = SCRIPT_DIR / "requirements"
PROJECT_ROOT = SCRIPT_DIR.parent


def find_device():
    """Auto-detect CIRCUITPY device mount point."""
    # macOS
    if os.path.exists(DEFAULT_DEVICE_PATH_MACOS):
        return Path(DEFAULT_DEVICE_PATH_MACOS)

    # Linux - try common mount points
    user = os.environ.get("USER", "")
    linux_path = DEFAULT_DEVICE_PATH_LINUX.format(user=user)
    if os.path.exists(linux_path):
        return Path(linux_path)

    # Try glob for Linux
    for path in glob.glob("/media/*/CIRCUITPY"):
        return Path(path)
    for path in glob.glob("/run/media/*/CIRCUITPY"):
        return Path(path)

    return None


def download_bundle(bundle_dir):
    """Download the Adafruit CircuitPython bundle if not present."""
    bundle_dir = Path(bundle_dir)
    bundle_name = f"adafruit-circuitpython-bundle-{BUNDLE_VERSION}-mpy-{BUNDLE_DATE}"
    extracted_dir = bundle_dir / bundle_name

    if extracted_dir.exists():
        print(f"Bundle already exists: {extracted_dir}")
        return extracted_dir

    bundle_dir.mkdir(parents=True, exist_ok=True)

    url = BUNDLE_URL_TEMPLATE.format(version=BUNDLE_VERSION, date=BUNDLE_DATE)
    zip_path = bundle_dir / f"{bundle_name}.zip"

    print(f"Downloading bundle from {url}...")
    try:
        urllib.request.urlretrieve(url, zip_path)
    except (urllib.error.URLError, urllib.error.HTTPError, OSError) as e:
        print(f"ERROR: Failed to download bundle: {e}")
        print(f"\nYou can manually download from:\n  {url}")
        print(f"\nAnd extract to:\n  {bundle_dir}")
        sys.exit(1)

    print(f"Extracting to {bundle_dir}...")
    with zipfile.ZipFile(zip_path, "r") as zf:
        # Validate each member path before extraction to prevent path traversal
        bundle_dir_resolved = bundle_dir.resolve()
        for member in zf.namelist():
            member_path = (bundle_dir / member).resolve()
            if not str(member_path).startswith(str(bundle_dir_resolved)):
                raise ValueError(f"Zip member escapes target directory: {member}")
        zf.extractall(bundle_dir)

    # Clean up zip file
    zip_path.unlink()

    print(f"Bundle ready: {extracted_dir}")
    return extracted_dir


def load_requirements(target):
    """Load library requirements for a target (base + target-specific)."""
    libraries = set()

    # Always load base requirements
    base_file = REQUIREMENTS_DIR / "base.txt"
    if base_file.exists():
        libraries.update(parse_requirements_file(base_file))

    # Load target-specific requirements
    target_file = REQUIREMENTS_DIR / f"{target}.txt"
    if target_file.exists():
        libraries.update(parse_requirements_file(target_file))
    else:
        print(f"WARNING: No requirements file for target '{target}'")

    return sorted(libraries)


def parse_requirements_file(filepath):
    """Parse a requirements file, ignoring comments and blank lines."""
    libraries = []
    with open(filepath) as f:
        for line in f:
            line = line.strip()
            # Skip comments and blank lines
            if not line or line.startswith("#"):
                continue
            libraries.append(line)
    return libraries


def find_library_in_bundle(bundle_lib_dir, library_name):
    """Find a library in the bundle (handles both .mpy files and directories)."""
    # Check for single .mpy file
    mpy_file = bundle_lib_dir / f"{library_name}.mpy"
    if mpy_file.exists():
        return mpy_file

    # Check for directory (package)
    lib_dir = bundle_lib_dir / library_name
    if lib_dir.is_dir():
        return lib_dir

    return None


def copy_library(src, dest_lib_dir):
    """Copy a library (file or directory) to the device."""
    dest_lib_dir = Path(dest_lib_dir)

    if src.is_file():
        dest = dest_lib_dir / src.name
        shutil.copy2(src, dest)
        print(f"  Copied: {src.name}")
    elif src.is_dir():
        dest = dest_lib_dir / src.name
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(src, dest)
        print(f"  Copied: {src.name}/ (directory)")


def deploy_libraries(bundle_dir, device_path, libraries):
    """Deploy libraries from bundle to device."""
    bundle_lib_dir = bundle_dir / "lib"
    device_lib_dir = device_path / "lib"

    if not bundle_lib_dir.exists():
        print(f"ERROR: Bundle lib directory not found: {bundle_lib_dir}")
        sys.exit(1)

    device_lib_dir.mkdir(exist_ok=True)

    print(f"\nDeploying {len(libraries)} libraries to {device_lib_dir}...")

    missing = []
    for library in libraries:
        src = find_library_in_bundle(bundle_lib_dir, library)
        if src:
            copy_library(src, device_lib_dir)
        else:
            missing.append(library)

    if missing:
        print(f"\nWARNING: Libraries not found in bundle: {', '.join(missing)}")
        print("These may need to be installed separately or the names may be incorrect.")


def deploy_source(device_path, include_tests=False):
    """Deploy project source code to device."""
    device_lib_dir = device_path / "lib"
    device_lib_dir.mkdir(exist_ok=True)

    # Deploy shared library
    shared_src = PROJECT_ROOT / "src" / "shared"
    shared_dest = device_lib_dir / "shared"

    if shared_src.exists():
        print("\nDeploying source code...")
        if shared_dest.exists():
            shutil.rmtree(shared_dest)
        shutil.copytree(
            shared_src,
            shared_dest,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyi"),
        )
        print("  Copied: shared/")

    # Deploy tests if requested
    if include_tests:
        tests_src = PROJECT_ROOT / "tests" / "device"
        tests_dest = device_lib_dir / "tests" / "device"

        if tests_src.exists():
            if tests_dest.exists():
                shutil.rmtree(tests_dest)
            tests_dest.parent.mkdir(exist_ok=True)
            shutil.copytree(
                tests_src,
                tests_dest,
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
            )
            print("  Copied: tests/device/")


def list_targets():
    """List available deployment targets."""
    print("Available targets:")
    for req_file in sorted(REQUIREMENTS_DIR.glob("*.txt")):
        if req_file.stem != "base":
            print(f"  {req_file.stem}")


def main():
    parser = argparse.ArgumentParser(
        description="Deploy CircuitPython code and libraries to device",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --target pool-node              Deploy pool node libraries
  %(prog)s --target test --source          Deploy test libs + source code
  %(prog)s --target valve-node --source    Deploy valve node with source
  %(prog)s --list-targets                  Show available targets
  %(prog)s --download-only                 Just download the bundle
        """,
    )

    parser.add_argument(
        "--target",
        "-t",
        help="Deployment target (pool-node, valve-node, display-node, test)",
    )
    parser.add_argument(
        "--device",
        "-d",
        help="Device mount path (default: auto-detect CIRCUITPY)",
    )
    parser.add_argument(
        "--bundle",
        "-b",
        help=f"Bundle directory (default: {BUNDLE_DIR})",
    )
    parser.add_argument(
        "--source",
        "-s",
        action="store_true",
        help="Also deploy project source code (src/shared/)",
    )
    parser.add_argument(
        "--tests",
        action="store_true",
        help="Also deploy device tests (tests/device/)",
    )
    parser.add_argument(
        "--list-targets",
        "-l",
        action="store_true",
        help="List available deployment targets",
    )
    parser.add_argument(
        "--download-only",
        action="store_true",
        help="Only download the bundle, don't deploy",
    )

    args = parser.parse_args()

    # Handle list targets
    if args.list_targets:
        list_targets()
        return 0

    # Ensure bundle is downloaded
    bundle_dir = Path(args.bundle) if args.bundle else BUNDLE_DIR
    bundle_path = download_bundle(bundle_dir)

    if args.download_only:
        print("\nBundle downloaded. Use --target to deploy.")
        return 0

    # Require target for deployment
    if not args.target:
        parser.error("--target is required for deployment (use --list-targets to see options)")

    # Find device
    device_path = Path(args.device) if args.device else find_device()
    if not device_path or not device_path.exists():
        print("ERROR: CIRCUITPY device not found.")
        print("Connect a CircuitPython device or specify --device path.")
        sys.exit(1)

    print(f"Device: {device_path}")
    print(f"Target: {args.target}")

    # Load and deploy libraries
    libraries = load_requirements(args.target)
    if libraries:
        deploy_libraries(bundle_path, device_path, libraries)

    # Deploy source code if requested
    if args.source or args.tests:
        deploy_source(device_path, include_tests=args.tests)

    print("\nDeployment complete!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
