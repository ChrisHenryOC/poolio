#!/usr/bin/env python3
"""
Adafruit IO feed setup script for Poolio.

Creates the feed group and all feeds for a given environment.

Usage:
    python scripts/adafruit_io_setup.py --username USER --key KEY --environment nonprod
    python scripts/adafruit_io_setup.py --username USER --key KEY --environment prod

Environment variables can be used instead of command-line arguments:
    export AIO_USERNAME="your_username"
    export AIO_KEY="your_aio_key"
    python scripts/adafruit_io_setup.py --environment nonprod
"""

import argparse
import os
import sys

try:
    from Adafruit_IO import Client, RequestError
except ImportError:
    print("ERROR: Adafruit_IO library not installed.")
    print("Install with: pip install adafruit-io")
    sys.exit(1)


# Feed definitions: (name, description)
FEEDS = [
    ("gateway", "Central message bus for poolio system messages"),
    ("pooltemp", "Pool water temperature readings (Fahrenheit)"),
    ("outsidetemp", "Outside air temperature readings (Fahrenheit)"),
    ("insidetemp", "Inside temperature readings (Fahrenheit)"),
    ("poolnodebattery", "Pool node battery percentage (0-100)"),
    ("poolvalveruntime", "Daily valve runtime in minutes"),
    ("valvestarttime", "Scheduled fill window start time (HH:MM format)"),
    ("config", "Device configuration JSON"),
    ("config-pool-node", "Pool Node device configuration"),
    ("config-valve-node", "Valve Node device configuration"),
    ("config-display-node", "Display Node device configuration"),
    ("events", "System events and diagnostic messages"),
]


def get_group_name(environment: str) -> str:
    """Get the feed group name for an environment."""
    if environment == "prod":
        return "poolio"
    return f"poolio-{environment}"


def create_group(client: Client, group_name: str, description: str) -> bool:
    """Create a feed group if it doesn't exist."""
    try:
        # Check if group exists
        client.groups(group_name)
        print(f"  Group '{group_name}' already exists")
        return True
    except RequestError:
        pass

    try:
        client.create_group({"name": group_name, "description": description})
        print(f"  Created group '{group_name}'")
        return True
    except RequestError as e:
        print(f"  ERROR creating group '{group_name}': {e}")
        return False


def create_feed(client: Client, group_key: str, name: str, description: str) -> bool:
    """Create a feed within a group if it doesn't exist."""
    feed_key = f"{group_key}.{name}"
    try:
        # Check if feed exists
        client.feeds(feed_key)
        print(f"  Feed '{feed_key}' already exists")
        return True
    except RequestError:
        pass

    try:
        client.create_feed(
            {"name": name, "description": description},
            group_key=group_key,
        )
        print(f"  Created feed '{feed_key}'")
        return True
    except RequestError as e:
        print(f"  ERROR creating feed '{feed_key}': {e}")
        return False


def setup_feeds(username: str, key: str, environment: str) -> int:
    """Set up all feeds for an environment."""
    client = Client(username, key)
    group_name = get_group_name(environment)

    print(f"\nSetting up Adafruit IO feeds for environment: {environment}")
    print(f"Group: {group_name}")
    print("-" * 50)

    # Create group
    print("\nCreating feed group...")
    description = f"Poolio {environment} feeds"
    if not create_group(client, group_name, description):
        return 1

    # Create feeds
    print("\nCreating feeds...")
    errors = 0
    for name, desc in FEEDS:
        if not create_feed(client, group_name, name, desc):
            errors += 1

    # Summary
    print("-" * 50)
    if errors == 0:
        print(f"\nSuccess! Created {len(FEEDS)} feeds in '{group_name}'")
        print("\nFeed keys:")
        for name, _ in FEEDS:
            print(f"  {group_name}.{name}")
        return 0
    else:
        print(f"\nCompleted with {errors} error(s)")
        return 1


def verify_feeds(username: str, key: str, environment: str) -> int:
    """Verify all feeds exist and are accessible."""
    client = Client(username, key)
    group_name = get_group_name(environment)

    print(f"\nVerifying Adafruit IO feeds for environment: {environment}")
    print(f"Group: {group_name}")
    print("-" * 50)

    errors = 0

    # Check group
    try:
        client.groups(group_name)
        print(f"  Group '{group_name}' exists")
    except RequestError:
        print(f"  ERROR: Group '{group_name}' not found")
        return 1

    # Check feeds
    for name, _ in FEEDS:
        feed_key = f"{group_name}.{name}"
        try:
            client.feeds(feed_key)
            print(f"  Feed '{feed_key}' exists")
        except RequestError:
            print(f"  ERROR: Feed '{feed_key}' not found")
            errors += 1

    print("-" * 50)
    if errors == 0:
        print(f"\nAll {len(FEEDS)} feeds verified successfully!")
        return 0
    else:
        print(f"\n{errors} feed(s) missing")
        return 1


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Set up Adafruit IO feeds for Poolio",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Environment variables:
  AIO_USERNAME    Adafruit IO username
  AIO_KEY         Adafruit IO API key

Examples:
  %(prog)s --environment nonprod
  %(prog)s --username myuser --key mykey --environment prod
  %(prog)s --environment nonprod --verify
        """,
    )
    parser.add_argument(
        "--username",
        "-u",
        default=os.environ.get("AIO_USERNAME"),
        help="Adafruit IO username (or set AIO_USERNAME env var)",
    )
    parser.add_argument(
        "--key",
        "-k",
        default=os.environ.get("AIO_KEY"),
        help="Adafruit IO API key (or set AIO_KEY env var)",
    )
    parser.add_argument(
        "--environment",
        "-e",
        required=True,
        choices=["prod", "nonprod", "dev", "test"],
        help="Environment to set up",
    )
    parser.add_argument(
        "--verify",
        "-v",
        action="store_true",
        help="Verify feeds exist instead of creating them",
    )

    args = parser.parse_args()

    if not args.username:
        print("ERROR: Username required. Use --username or set AIO_USERNAME")
        return 1
    if not args.key:
        print("ERROR: API key required. Use --key or set AIO_KEY")
        return 1

    if args.verify:
        return verify_feeds(args.username, args.key, args.environment)
    else:
        return setup_feeds(args.username, args.key, args.environment)


if __name__ == "__main__":
    sys.exit(main())
