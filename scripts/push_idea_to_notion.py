#!/usr/bin/env python3
"""
Push a new idea entry to the Acquisition Labs Ideas database in Notion.

Usage:
    pip install requests
    NOTION_API_KEY=ntn_xxx NOTION_PARENT_PAGE_ID=xxx python scripts/push_idea_to_notion.py

This script:
1. Searches your Notion workspace for "Ideas" databases
2. Identifies the Acquisition Labs Ideas database
3. Creates a new entry with the specified idea details

Environment variables:
    NOTION_API_KEY         - Your Notion integration token
    NOTION_PARENT_PAGE_ID  - The parent page ID for creating new databases (optional)
"""

import json
import os
import sys
import requests

NOTION_API_KEY = os.environ.get("NOTION_API_KEY")
PARENT_PAGE_ID = os.environ.get("NOTION_PARENT_PAGE_ID", "")
NOTION_VERSION = "2022-06-28"
BASE_URL = "https://api.notion.com/v1"

HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": NOTION_VERSION,
}


def search_ideas_databases():
    """Search for databases with 'Ideas' in the name."""
    print("Searching for 'Ideas' databases in your Notion workspace...")
    resp = requests.post(
        f"{BASE_URL}/search",
        headers=HEADERS,
        json={"query": "Ideas", "filter": {"property": "object", "value": "database"}},
    )
    resp.raise_for_status()
    results = resp.json().get("results", [])

    if not results:
        print("No 'Ideas' databases found.")
        return None

    print(f"Found {len(results)} database(s):")
    for i, db in enumerate(results):
        title = "".join(t.get("plain_text", "") for t in db.get("title", []))
        print(f"  [{i}] {title} (ID: {db['id']})")

    return results


def create_idea_entry(database_id):
    """Create the idea entry in the specified Notion database."""
    print(f"\nCreating idea entry in database {database_id}...")

    # Build properties — we try common property names.
    # Notion databases have specific property schemas, so we detect them first.
    db_resp = requests.get(f"{BASE_URL}/databases/{database_id}", headers=HEADERS)
    db_resp.raise_for_status()
    db_props = db_resp.json().get("properties", {})

    print(f"  Database properties: {list(db_props.keys())}")

    properties = {}

    # Title property (usually "Name" or "Idea")
    title_prop = None
    for name, prop in db_props.items():
        if prop["type"] == "title":
            title_prop = name
            break

    if title_prop:
        properties[title_prop] = {
            "title": [
                {
                    "text": {
                        "content": "SaaS data storage model is dying \u2014 future is sensor-oriented data generation"
                    }
                }
            ]
        }

    # Type property
    if "Type" in db_props:
        prop_type = db_props["Type"]["type"]
        if prop_type == "select":
            properties["Type"] = {"select": {"name": "Strategy"}}
        elif prop_type == "rich_text":
            properties["Type"] = {"rich_text": [{"text": {"content": "Strategy"}}]}

    # Potential Impact property
    if "Potential Impact" in db_props:
        prop_type = db_props["Potential Impact"]["type"]
        if prop_type == "select":
            properties["Potential Impact"] = {"select": {"name": "\U0001f525 Game Changer"}}
        elif prop_type == "rich_text":
            properties["Potential Impact"] = {
                "rich_text": [{"text": {"content": "\U0001f525 Game Changer"}}]
            }

    # Status property
    if "Status" in db_props:
        prop_type = db_props["Status"]["type"]
        if prop_type == "select":
            properties["Status"] = {"select": {"name": "Raw"}}
        elif prop_type == "status":
            properties["Status"] = {"status": {"name": "Raw"}}
        elif prop_type == "rich_text":
            properties["Status"] = {"rich_text": [{"text": {"content": "Raw"}}]}

    # Date property
    if "Date" in db_props:
        properties["Date"] = {"date": {"start": "2026-02-22"}}

    # Notes property
    notes_text = (
        "Traditional SaaS products that just store and organize data are becoming "
        "commoditized. The future is products that actively generate and sense data "
        "\u2014 real-time triggers, monitoring, intelligence gathering. Apply to "
        "Acquisition Labs: instead of being a CRM that stores leads, be a sensor "
        "that generates leads by monitoring permit filings, business signals, market "
        "changes. The product doesn\u2019t hold data, it creates data. This is the moat."
    )

    if "Notes" in db_props:
        prop_type = db_props["Notes"]["type"]
        if prop_type == "rich_text":
            properties["Notes"] = {"rich_text": [{"text": {"content": notes_text}}]}

    # Build the page creation payload
    payload = {
        "parent": {"database_id": database_id},
        "properties": properties,
    }

    # If Notes isn't a property, add it as page content (children blocks)
    children = None
    if "Notes" not in db_props:
        children = [
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"text": {"content": "Notes"}}]
                },
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"text": {"content": notes_text}}]
                },
            },
        ]
        payload["children"] = children

    resp = requests.post(f"{BASE_URL}/pages", headers=HEADERS, json=payload)
    resp.raise_for_status()

    page = resp.json()
    page_url = page.get("url", "")
    print(f"\n  Entry created successfully!")
    print(f"  URL: {page_url}")
    return page


def create_standalone_database_and_entry():
    """Fallback: create an Ideas database under the parent page, then add the entry."""
    print("\nNo existing Ideas database found. Creating one under the parent page...")

    payload = {
        "parent": {"page_id": PARENT_PAGE_ID},
        "title": [{"text": {"content": "Acquisition Labs Ideas"}}],
        "properties": {
            "Idea": {"title": {}},
            "Type": {"select": {"options": [{"name": "Strategy", "color": "blue"}]}},
            "Potential Impact": {
                "select": {
                    "options": [
                        {"name": "\U0001f525 Game Changer", "color": "red"},
                        {"name": "\u26a1 High", "color": "orange"},
                        {"name": "\U0001f44d Medium", "color": "yellow"},
                        {"name": "\U0001f914 Low", "color": "gray"},
                    ]
                }
            },
            "Status": {
                "select": {
                    "options": [
                        {"name": "Raw", "color": "gray"},
                        {"name": "Exploring", "color": "blue"},
                        {"name": "In Progress", "color": "yellow"},
                        {"name": "Done", "color": "green"},
                        {"name": "Parked", "color": "orange"},
                    ]
                }
            },
            "Date": {"date": {}},
            "Notes": {"rich_text": {}},
        },
    }

    resp = requests.post(f"{BASE_URL}/databases", headers=HEADERS, json=payload)
    resp.raise_for_status()
    db = resp.json()
    db_id = db["id"]
    print(f"  Created database: Acquisition Labs Ideas (ID: {db_id})")

    return create_idea_entry(db_id)


def main():
    if not NOTION_API_KEY:
        print("Error: NOTION_API_KEY environment variable is required.")
        print("Usage: NOTION_API_KEY=ntn_xxx python scripts/push_idea_to_notion.py")
        sys.exit(1)

    try:
        databases = search_ideas_databases()

        if databases:
            # Look for an "Acquisition Labs Ideas" or similar database
            target_db = None
            for db in databases:
                title = "".join(t.get("plain_text", "") for t in db.get("title", []))
                if "acquisition" in title.lower() or "ideas" in title.lower():
                    target_db = db
                    break

            if target_db is None:
                target_db = databases[0]

            title = "".join(t.get("plain_text", "") for t in target_db.get("title", []))
            print(f"\nUsing database: {title}")
            create_idea_entry(target_db["id"])
        else:
            create_standalone_database_and_entry()

        print("\nDone!")

    except requests.exceptions.HTTPError as e:
        print(f"\nNotion API error: {e}")
        print(f"Response: {e.response.text}")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
