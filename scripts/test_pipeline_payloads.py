import json
import requests

# Base local server target URL
TARGET_URL = "http://127.0.0.1:8000/api/ingest/email"

TEST_SUITE = [
    {
        "provider": "imap",
        "message_id": "test-uuid-001-business",
        "sender": "accounting@corporateclient.com",
        "recipients": ["user@internal.com"],
        "subject": "Pending Invoice and Project Contract Proposal",
        "body": "Hello team, attached is the revised proposal and line-item invoice for review. Let us get this contract signed by Friday afternoon.",
        "received_at": "2026-06-15T10:00:00Z"
    },
    {
        "provider": "gmail",
        "message_id": "test-uuid-002-important",
        "sender": "executive.director@company.com",
        "recipients": ["user@internal.com"],
        "subject": "CRITICAL: Production Outage - Action Required Immediately ASAP",
        "body": "The internal system is throwing fatal errors. This is a critical deadline situation. Fix this execution cycle immediately or system down.",
        "received_at": "2026-06-15T10:05:00Z"
    },
    {
        "provider": "outlook",
        "message_id": "test-uuid-003-spam",
        "sender": "win-rewards@sketchy-deals-portal.net",
        "recipients": ["user@internal.com"],
        "subject": "!!! FREE CASH REWARDS CLICK HERE BUY NOW !!!",
        "body": "CONGRATULATIONS user! Click here right now to claim a completely free cash reward prize pool payout. Limited promotional offer buy now.",
        "received_at": "2026-06-15T10:10:00Z"
    },
    {
        "provider": "imap",
        "message_id": "test-uuid-004-private",
        "sender": "mom-personal-mail@familydomain.org",
        "recipients": ["user@internal.com"],
        "subject": "Sunday family dinner plans and birthday invitation",
        "body": "Hey honey, just checking in to see if you are coming over for family dinner this upcoming Sunday afternoon. Let me know if you can bring dessert!",
        "received_at": "2026-06-15T10:15:00Z"
    },
    {
        "provider": "gmail",
        "message_id": "test-uuid-005-ambiguous",
        "sender": "random-newsletter@updates.com",
        "recipients": ["user@internal.com"],
        "subject": "Global weekly technical updates digest review",
        "body": "This is a basic informational log file dispatch regarding changing patterns across international macro-infrastructure configurations.",
        "received_at": "2026-06-15T10:20:00Z"
    }
]

def execute_simulation():
    print("🚀 Starting Pipeline Evaluation Simulation...\n" + "="*60)
    
    for index, payload in enumerate(TEST_SUITE, start=1):
        print(f"Sending Email Sample #{index} | ID: {payload['message_id']}")
        try:
            response = requests.post(TARGET_URL, json=payload, timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(" ✅ Processing Status: SUCCESS")
                print(f"   - Predicted Category: {data.get('category_label', 'N/A')}")
                print(f"   - Confidence Level:  {data.get('category_confidence', 0.0):.2f}")
                print(f"   - Target Folder Box:  {data.get('routed_folder', 'N/A')}")
                print(f"   - Calculated Priority: {data.get('priority_score', 0.0):.1f}")
            else:
                print(f" ❌ Pipeline Failure: Server responded with code {response.status_code}")
                print(f"   - Response Body: {response.text}")
        except Exception as error:
            print(f" ❌ Connection Error: Application target unreachable. Reason: {error}")
        print("-" * 60)

if __name__ == "__main__":
    execute_simulation()