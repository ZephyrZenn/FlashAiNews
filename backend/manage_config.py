#!/usr/bin/env python3
"""
Configuration management script for NewsCollector.

This script provides command-line tools for managing the application configuration,
including validation, backup, restore, and creation of default configurations.
"""

import argparse
import os
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "app"))

import toml
from app.config import (
    ConfigValidationError,
    backup_config,
    create_default_config,
    get_config,
    get_config_path,
    get_config_summary,
    restore_config,
)


def validate_configuration():
    """Validate the current configuration"""
    print("Validating configuration...")

    try:
        config = get_config()
        print("✅ Configuration is valid!")

        # Show configuration summary
        config_path = get_config_path()
        with open(config_path, "r") as f:
            raw_config = toml.load(f)

        summary = get_config_summary(raw_config)
        print("\nConfiguration Summary:")
        print(f"  - Email enabled: {summary['email_enabled']}")
        print(f"  - Default model: {summary['default_model']}")
        print(f"  - Available models: {', '.join(summary['available_models'])}")
        print(f"  - Model count: {summary['model_count']}")

        return True

    except ConfigValidationError as e:
        print(f"❌ Configuration validation failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def show_configuration():
    """Show the current configuration (without sensitive data)"""
    try:
        config = get_config()
        print("Current Configuration:")
        print(f"  Default Model: {config.global_.default_model}")
        print(f"  Email Enabled: {config.global_.email_enabled}")
        print(f"  Available Models: {list(config.models.keys())}")

        if config.email:
            print(f"  Email Sender: {config.email.sender}")
            print(f"  Email Receiver: {config.email.receiver}")

        return True

    except Exception as e:
        print(f"❌ Error showing configuration: {e}")
        return False


def create_default_configuration(output_path: str = None):
    """Create a default configuration file"""
    if output_path is None:
        output_path = "config.toml"

    try:
        default_config = create_default_config()

        with open(output_path, "w") as f:
            toml.dump(default_config, f)

        print(f"✅ Default configuration created at: {output_path}")
        print("Please update the configuration with your actual settings.")
        return True

    except Exception as e:
        print(f"❌ Error creating default configuration: {e}")
        return False


def backup_current_configuration():
    """Create a backup of the current configuration"""
    try:
        config_path = get_config_path()
        backup_path = backup_config(config_path)

        if backup_path:
            print(f"✅ Configuration backed up to: {backup_path}")
            return True
        else:
            print("❌ Failed to create backup")
            return False

    except Exception as e:
        print(f"❌ Error creating backup: {e}")
        return False


def restore_configuration(backup_path: str):
    """Restore configuration from backup"""
    try:
        config_path = get_config_path()
        success = restore_config(backup_path, config_path)

        if success:
            print(f"✅ Configuration restored from: {backup_path}")
            return True
        else:
            print("❌ Failed to restore configuration")
            return False

    except Exception as e:
        print(f"❌ Error restoring configuration: {e}")
        return False


def list_backups():
    """List available configuration backups"""
    backup_dir = "backups"
    if not os.path.exists(backup_dir):
        print("No backup directory found")
        return

    backup_files = list(Path(backup_dir).glob("config_backup_*.toml"))

    if not backup_files:
        print("No backup files found")
        return

    print("Available backups:")
    for backup_file in sorted(backup_files, reverse=True):
        stat = backup_file.stat()
        print(f"  {backup_file.name} ({stat.st_size} bytes, {stat.st_mtime})")


def main():
    parser = argparse.ArgumentParser(description="NewsCollector Configuration Manager")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Validate command
    subparsers.add_parser("validate", help="Validate the current configuration")

    # Show command
    subparsers.add_parser("show", help="Show current configuration summary")

    # Create command
    create_parser = subparsers.add_parser("create", help="Create default configuration")
    create_parser.add_argument(
        "--output", "-o", help="Output file path (default: config.toml)"
    )

    # Backup command
    subparsers.add_parser("backup", help="Create backup of current configuration")

    # Restore command
    restore_parser = subparsers.add_parser(
        "restore", help="Restore configuration from backup"
    )
    restore_parser.add_argument("backup_path", help="Path to backup file")

    # List backups command
    subparsers.add_parser("list-backups", help="List available configuration backups")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    success = False

    if args.command == "validate":
        success = validate_configuration()
    elif args.command == "show":
        success = show_configuration()
    elif args.command == "create":
        success = create_default_configuration(args.output)
    elif args.command == "backup":
        success = backup_current_configuration()
    elif args.command == "restore":
        success = restore_configuration(args.backup_path)
    elif args.command == "list-backups":
        list_backups()
        success = True

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
