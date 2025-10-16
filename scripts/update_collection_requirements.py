#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Collection Requirements Updater.

This script automatically discovers and updates collection dependencies by:
1. Finding all requirements.txt files in the collections directory
2. Parsing and merging dependencies with version conflict resolution
3. Updating the requirements-collections.txt file

Usage:
    python scripts/update_collection_requirements.py
    python scripts/update_collection_requirements.py --dry-run
    python scripts/update_collection_requirements.py --output custom-requirements.txt
"""

import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import click
from packaging import specifiers


class RequirementParser:
    """Parse and manage Python requirements with version constraints."""

    def __init__(self):
        """Initialize the requirement parser with empty state."""
        self.requirements: Dict[str, Dict] = {}
        self.conflicts: List[Tuple[str, str, str]] = []

    def parse_requirement_line(self, line: str) -> Tuple[str, str, str]:
        """Parse a requirement line into package name, version spec, and extras.

        Returns:
            Tuple of (package_name, version_spec, extras)
        """
        line = line.strip()
        if not line or line.startswith("#"):
            return "", "", ""

        # Handle extras like package[extra1,extra2]
        extras_match = re.match(r"([^[]+)\[([^\]]+)\](.*)$", line)
        if extras_match:
            package_name = extras_match.group(1).strip()
            extras = f"[{extras_match.group(2)}]"
            version_spec = extras_match.group(3).strip()
        else:
            # Handle standard requirements
            version_operators = [">=", "<=", "==", "!=", ">", "<", "~="]
            package_name = line
            version_spec = ""
            extras = ""

            for op in version_operators:
                if op in line:
                    package_name, version_spec = line.split(op, 1)
                    package_name = package_name.strip()
                    version_spec = op + version_spec.strip()
                    break

        return package_name.lower(), version_spec, extras

    def add_requirement(
        self, package: str, version_spec: str, extras: str, source: str
    ):
        """Add a requirement with conflict detection."""
        if not package:
            return

        package_key = package.lower()

        if package_key not in self.requirements:
            self.requirements[package_key] = {
                "name": package,
                "versions": [],
                "extras": set(),
                "sources": [],
            }

        self.requirements[package_key]["versions"].append(version_spec)
        if extras:
            self.requirements[package_key]["extras"].add(extras)
        self.requirements[package_key]["sources"].append(source)

    def resolve_version_conflicts(self) -> Dict[str, str]:
        """Resolve version conflicts using the most restrictive compatible version."""
        resolved = {}

        for package_key, req_data in self.requirements.items():
            package_name = req_data["name"]
            versions = [v for v in req_data["versions"] if v]
            extras = req_data["extras"]

            if not versions:
                # No version specified, use package name only
                resolved[package_key] = package_name + (
                    "".join(extras) if extras else ""
                )
                continue

            try:
                # Try to find compatible version
                spec_set = specifiers.SpecifierSet(",".join(versions))
                resolved[package_key] = (
                    package_name + str(spec_set) + ("".join(extras) if extras else "")
                )
            except Exception as e:
                # If we can't resolve, use the most recent requirement
                click.echo(
                    f"⚠️  Version conflict for {package_name}: {versions}", err=True
                )
                click.echo(f"   Using most restrictive: {versions[-1]}", err=True)
                self.conflicts.append((package_name, str(versions), str(e)))
                resolved[package_key] = (
                    package_name + versions[-1] + ("".join(extras) if extras else "")
                )

        return resolved


def find_collection_requirements(collections_dir: Path) -> List[Path]:
    """Find all requirements.txt files in collections directory."""
    requirements_files = []

    if not collections_dir.exists():
        click.echo(f"❌ Collections directory not found: {collections_dir}", err=True)
        return requirements_files

    for req_file in collections_dir.rglob("requirements.txt"):
        # Skip test requirements unless specifically requested
        if any(test_dir in req_file.parts for test_dir in ["tests", "test"]):
            continue
        requirements_files.append(req_file)

    return sorted(requirements_files)


def generate_requirements_content(
    resolved_requirements: Dict[str, str],
    conflicts: List[Tuple[str, str, str]],
    source_mapping: Dict[str, List[str]],
) -> str:
    """Generate the content for requirements-collections.txt file."""
    content = [
        "# requirements-collections.txt",
        "# Auto-generated collection dependencies",
        "# This file contains Python dependencies required by Ansible collections",
        "# Generated by: scripts/update_collection_requirements.py",
        "",
    ]

    if conflicts:
        content.extend(
            [
                "# ⚠️  VERSION CONFLICTS DETECTED:",
                "# The following packages had conflicting version requirements:",
            ]
        )
        for package, versions, error in conflicts:
            content.append(f"# - {package}: {versions}")
        content.append("")

    # Group requirements by collection type
    groups = {
        "Kubernetes": ["kubernetes", "jsonpatch"],
        "AWS": ["boto3", "botocore"],
        "Google Cloud": ["google-auth", "google-cloud-storage"],
        "VMware": ["pyvmomi", "vmware-vcenter", "vmware-vapi-common-client"],
        "HashiCorp Vault": ["hvac", "azure-identity", "psycopg"],
        "Ansible Utils": ["jsonschema", "textfsm", "ttp", "xmltodict", "netaddr"],
        "AWX": ["pytz", "awxkit"],
        "General": ["requests", "requests-oauthlib", "urllib3", "aiohttp"],
    }

    for group_name, group_packages in groups.items():
        group_requirements = []
        for package_key in group_packages:
            if package_key in resolved_requirements:
                req_line = resolved_requirements[package_key]
                sources = source_mapping.get(package_key, [])
                if sources:
                    req_line += f"  # from: {', '.join(sources[:2])}"
                    if len(sources) > 2:
                        req_line += f" (+{len(sources) - 2} more)"
                group_requirements.append(req_line)

        if group_requirements:
            content.append(f"# {group_name} Collection Dependencies")
            content.extend(group_requirements)
            content.append("")

    # Add any remaining requirements not in predefined groups
    remaining = []
    for package_key, req_line in resolved_requirements.items():
        if not any(package_key in group_packages for group_packages in groups.values()):
            sources = source_mapping.get(package_key, [])
            if sources:
                req_line += f"  # from: {', '.join(sources[:2])}"
                if len(sources) > 2:
                    req_line += f" (+{len(sources) - 2} more)"
            remaining.append(req_line)

    if remaining:
        content.append("# Other Collection Dependencies")
        content.extend(sorted(remaining))
        content.append("")

    return "\n".join(content)


@click.command()
@click.option(
    "--collections-dir",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default="collections",
    help="Path to collections directory",
)
@click.option(
    "--output",
    type=click.Path(path_type=Path),
    default="requirements-collections.txt",
    help="Output requirements file",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be written without creating files",
)
@click.option(
    "--include-test-deps",
    is_flag=True,
    help="Include test dependencies from collections",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Show verbose output",
)
def main(
    collections_dir: Path,
    output: Path,
    dry_run: bool,
    include_test_deps: bool,
    verbose: bool,
):
    """Update collection requirements file based on discovered dependencies."""
    click.echo("🔍 Discovering collection requirements...")

    # Find all requirements files
    req_files = find_collection_requirements(collections_dir)

    if include_test_deps:
        # Also include test requirements
        test_req_files = []
        for req_file in collections_dir.rglob("requirements.txt"):
            if any(test_dir in req_file.parts for test_dir in ["tests", "test"]):
                test_req_files.append(req_file)
        req_files.extend(test_req_files)

    if not req_files:
        click.echo("❌ No requirements.txt files found in collections directory")
        return 1

    click.echo(f"📋 Found {len(req_files)} requirements files")

    if verbose:
        for req_file in req_files:
            click.echo(f"   • {req_file.relative_to(collections_dir)}")

    # Parse all requirements
    parser = RequirementParser()
    source_mapping = {}

    for req_file in req_files:
        try:
            with open(req_file, "r", encoding="utf-8") as f:
                lines = f.readlines()

            collection_name = str(req_file.relative_to(collections_dir)).split("/")[1:3]
            collection_name = (
                ".".join(collection_name)
                if len(collection_name) >= 2
                else str(req_file.parent.name)
            )

            for line_num, line in enumerate(lines, 1):
                package, version_spec, extras = parser.parse_requirement_line(line)
                if package:
                    parser.add_requirement(
                        package, version_spec, extras, collection_name
                    )

                    # Track source mapping for comments
                    if package not in source_mapping:
                        source_mapping[package] = []
                    if collection_name not in source_mapping[package]:
                        source_mapping[package].append(collection_name)

                    if verbose:
                        click.echo(
                            f"   📦 {package}{version_spec}{extras} from {collection_name}"
                        )

        except Exception as e:
            click.echo(f"⚠️  Error reading {req_file}: {e}", err=True)

    # Resolve conflicts and generate output
    click.echo("🔧 Resolving version conflicts...")
    resolved = parser.resolve_version_conflicts()

    if parser.conflicts:
        click.echo(f"⚠️  {len(parser.conflicts)} version conflicts detected")

    # Generate requirements content
    content = generate_requirements_content(resolved, parser.conflicts, source_mapping)

    # Output results
    if dry_run:
        click.echo("\n📄 Generated requirements-collections.txt content:")
        click.echo("=" * 60)
        click.echo(content)
        click.echo("=" * 60)
        click.echo(f"\n✅ Would write {len(resolved)} requirements to {output}")
    else:
        try:
            with open(output, "w", encoding="utf-8") as f:
                f.write(content)
            click.echo(
                f"✅ Successfully updated {output} with {len(resolved)} requirements"
            )

            if parser.conflicts:
                click.echo("\n⚠️  Please review version conflicts noted in the file")

        except Exception as e:
            click.echo(f"❌ Error writing {output}: {e}", err=True)
            return 1

    click.echo("\n📊 Summary:")
    click.echo(f"   • Processed {len(req_files)} requirements files")
    click.echo(f"   • Found {len(resolved)} unique packages")
    click.echo(f"   • Detected {len(parser.conflicts)} version conflicts")

    return 0


if __name__ == "__main__":
    sys.exit(main())
