import json
from server.gmail_server import search_emails, read_email, list_unread_emails


def print_json(data_str: str):
    """Helper to pretty-print JSON results."""
    try:
        parsed = json.loads(data_str)
        print(json.dumps(parsed, indent=2))
    except Exception:
        print(data_str)


def main():
    print("=" * 60)
    print("       Gmail MCP Server - Interactive Terminal Tester       ")
    print("=" * 60)

    while True:
        print("\nChoose a tool to test:")
        print("1. Search Emails (by keyword / query)")
        print("2. Read Full Email Body (by message ID)")
        print("3. List Unread Emails")
        print("4. Exit")

        choice = input("\nEnter choice (1-4): ").strip()

        if choice == "1":
            query = input("Enter search query (e.g. 'project', 'from:someone', or press Enter for all): ").strip()
            max_r = input("Max results (default 3): ").strip()
            max_r = int(max_r) if max_r.isdigit() else 3
            print(f"\nSearching emails with query: '{query}'...")
            res = search_emails(query=query, max_results=max_r)
            print_json(res)

        elif choice == "2":
            msg_id = input("Enter Message ID (e.g. 'msg_001'): ").strip()
            if not msg_id:
                print("Message ID cannot be empty.")
                continue
            print(f"\nReading email details for ID: '{msg_id}'...")
            res = read_email(message_id=msg_id)
            print_json(res)

        elif choice == "3":
            max_r = input("Max unread results (default 3): ").strip()
            max_r = int(max_r) if max_r.isdigit() else 3
            print("\nFetching unread emails...")
            res = list_unread_emails(max_results=max_r)
            print_json(res)

        elif choice in ("4", "exit", "q"):
            print("Exiting tester. Bye!")
            break
        else:
            print("Invalid choice, please select 1, 2, 3, or 4.")


if __name__ == "__main__":
    main()
