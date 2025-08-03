#!/usr/bin/env python3
"""
Test script to analyze dependency resolution between requirements files.
"""

import re
from typing import Dict, Set


def parse_requirements_file(file_path: str) -> Dict[str, str]:
    """Parse a requirements file and return package -> version mapping."""
    requirements = {}
    
    try:
        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    # Parse package name and version
                    if any(op in line for op in ['==', '>=', '<=', '>', '<', '~=', '!=']):
                        for op in ['==', '>=', '<=', '!=', '~=', '>', '<']:
                            if op in line:
                                package, version = line.split(op, 1)
                                requirements[package.strip().lower()] = f"{op}{version.strip()}"
                                break
                    else:
                        # No version specifier - will get latest
                        requirements[line.lower()] = "latest"
    except FileNotFoundError:
        print(f"File not found: {file_path}")
    
    return requirements


def find_overlaps(main_reqs: Dict[str, str], collection_reqs: Dict[str, str]) -> Dict[str, Dict]:
    """Find overlapping packages and their version specifications."""
    overlaps = {}
    
    for package in set(main_reqs.keys()) & set(collection_reqs.keys()):
        overlaps[package] = {
            'main': main_reqs[package],
            'collections': collection_reqs[package],
            'compatible': analyze_compatibility(main_reqs[package], collection_reqs[package])
        }
    
    return overlaps


def analyze_compatibility(main_spec: str, collection_spec: str) -> str:
    """Analyze if two version specifications are compatible."""
    if main_spec == "latest" and collection_spec != "latest":
        return "⚠️  MAIN UNPINNED - Will use collection constraint"
    elif main_spec != "latest" and collection_spec == "latest":
        return "✅ MAIN PINNED - Will use main requirement"
    elif main_spec.startswith("==") and collection_spec.startswith(">="):
        # Extract versions for comparison
        main_ver = main_spec[2:]
        collection_ver = collection_spec[2:]
        return f"✅ COMPATIBLE - {main_spec} satisfies {collection_spec}"
    elif main_spec == collection_spec:
        return "✅ IDENTICAL"
    else:
        return f"❓ NEEDS_ANALYSIS - {main_spec} vs {collection_spec}"


def main():
    print("🔍 Analyzing Dependency Resolution Between Requirements Files")
    print("=" * 70)
    
    # Parse both files
    main_reqs = parse_requirements_file("requirements.txt")
    collection_reqs = parse_requirements_file("requirements-collections.txt")
    
    print(f"\n📊 Statistics:")
    print(f"   • Main requirements.txt: {len(main_reqs)} packages")
    print(f"   • Collection requirements: {len(collection_reqs)} packages")
    
    # Find overlaps
    overlaps = find_overlaps(main_reqs, collection_reqs)
    print(f"   • Overlapping packages: {len(overlaps)}")
    
    if overlaps:
        print(f"\n🔄 Overlapping Packages Analysis:")
        print("-" * 50)
        for package, specs in overlaps.items():
            print(f"📦 {package}")
            print(f"   Main: {specs['main']}")
            print(f"   Collections: {specs['collections']}")
            print(f"   Resolution: {specs['compatible']}")
            print()
    
    # Find packages only in collections
    collection_only = set(collection_reqs.keys()) - set(main_reqs.keys())
    if collection_only:
        print(f"➕ New Dependencies from Collections ({len(collection_only)}):")
        print("-" * 50)
        for package in sorted(collection_only):
            print(f"   📦 {package} {collection_reqs[package]}")
    
    # Find unpinned packages in main
    unpinned = {pkg: spec for pkg, spec in main_reqs.items() if spec == "latest"}
    if unpinned:
        print(f"\n⚠️  Unpinned Packages in Main Requirements ({len(unpinned)}):")
        print("-" * 50)
        for package in sorted(unpinned.keys()):
            print(f"   📦 {package} (will get latest version)")


if __name__ == "__main__":
    main()