import json
from server.gmail_server import search_emails, read_email, list_unread_emails
from server.github_server import (
    search_repositories,
    list_issues,
    get_issue,
    list_pull_requests,
    get_file_content,
)


def print_json(data_str: str):
    """Helper to pretty-print JSON results."""
    try:
        parsed = json.loads(data_str)
        print(json.dumps(parsed, indent=2))
    except Exception:
        print(data_str)


def main():
    print("=" * 65)
    print("      MCP Server Interactive Terminal Tester (Gmail & GitHub)      ")
    print("=" * 65)

    while True:
        print("\n--- Gmail Tools ---")
        print("1. Search Emails (by query)")
        print("2. Read Full Email Body (by ID)")
        print("3. List Unread Emails")
        print("\n--- GitHub Tools ---")
        print("4. Search Repositories")
        print("5. List Repository Issues")
        print("6. Get Issue / PR Details")
        print("7. List Repository Pull Requests")
        print("8. Get File Content from Repository")
        print("\n0. Exit")

        choice = input("\nEnter choice (0-8): ").strip()

        if choice == "1":
            query = input("Enter search query (or press Enter for all): ").strip()
            max_r = input("Max results (default 3): ").strip()
            max_r = int(max_r) if max_r.isdigit() else 3
            print(f"\nSearching emails with query: '{query}'...")
            print_json(search_emails(query=query, max_results=max_r))

        elif choice == "2":
            msg_id = input("Enter Message ID (e.g. 'msg_001'): ").strip()
            if not msg_id:
                print("Message ID cannot be empty.")
                continue
            print(f"\nReading email details for ID: '{msg_id}'...")
            print_json(read_email(message_id=msg_id))

        elif choice == "3":
            max_r = input("Max unread results (default 3): ").strip()
            max_r = int(max_r) if max_r.isdigit() else 3
            print("\nFetching unread emails...")
            print_json(list_unread_emails(max_results=max_r))

        elif choice == "4":
            query = input("Enter repo search query (e.g. 'Major_1'): ").strip()
            max_r = input("Max results (default 3): ").strip()
            max_r = int(max_r) if max_r.isdigit() else 3
            print(f"\nSearching repositories for: '{query}'...")
            print_json(search_repositories(query=query, max_results=max_r))

        elif choice == "5":
            owner = input("Enter Owner/Org (default: 'Luqmansyed75'): ").strip() or "Luqmansyed75"
            repo = input("Enter Repo Name (default: 'Major_1'): ").strip() or "Major_1"
            state = input("Enter state ('open', 'closed', 'all', default: 'open'): ").strip() or "open"
            print(f"\nListing issues for '{owner}/{repo}'...")
            print_json(list_issues(owner=owner, repo=repo, state=state))

        elif choice == "6":
            owner = input("Enter Owner/Org (default: 'Luqmansyed75'): ").strip() or "Luqmansyed75"
            repo = input("Enter Repo Name (default: 'Major_1'): ").strip() or "Major_1"
            num = input("Enter Issue Number (e.g. 1): ").strip()
            if not num.isdigit():
                print("Invalid issue number.")
                continue
            print(f"\nFetching issue #{num} from '{owner}/{repo}'...")
            print_json(get_issue(owner=owner, repo=repo, issue_number=int(num)))

        elif choice == "7":
            owner = input("Enter Owner/Org (default: 'Luqmansyed75'): ").strip() or "Luqmansyed75"
            repo = input("Enter Repo Name (default: 'Major_1'): ").strip() or "Major_1"
            print(f"\nListing pull requests for '{owner}/{repo}'...")
            print_json(list_pull_requests(owner=owner, repo=repo))

        elif choice == "8":
            owner = input("Enter Owner/Org (default: 'Luqmansyed75'): ").strip() or "Luqmansyed75"
            repo = input("Enter Repo Name (default: 'Major_1'): ").strip() or "Major_1"
            path = input("Enter File Path (e.g. 'README.md'): ").strip() or "README.md"
            print(f"\nReading '{path}' from '{owner}/{repo}'...")
            print_json(get_file_content(owner=owner, repo=repo, path=path))

        elif choice in ("0", "exit", "q"):
            print("Exiting tester. Bye!")
            break
        else:
            print("Invalid choice, please select an option from the menu.")


if __name__ == "__main__":
    main()
