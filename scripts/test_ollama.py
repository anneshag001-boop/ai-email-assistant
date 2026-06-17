"""Quick test to verify Ollama SLM classification is working.
Run: python scripts/test_ollama.py
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.ai.ollama_classifier import OllamaClassifier
from app.ai.classifier import EmailClassifier
from app.routing.router import route_email

test_cases = [
    {
        "name": "Business - Invoice",
        "subject": "Invoice #1234 - Payment Due",
        "body": "Dear customer, your invoice of $500 is due next week. Please make the payment.",
        "expected_category": "business",
    },
    {
        "name": "Private - Family",
        "subject": "Family dinner this Saturday",
        "body": "Hey! Mom is cooking dinner this Saturday. Can you come?",
        "expected_category": "private",
    },
    {
        "name": "Other Work - Bank OTP",
        "subject": "Your OTP for transaction",
        "body": "Your one-time password for HDFC Bank transaction is 784392. Valid for 5 minutes.",
        "expected_category": "other_work",
    },
    {
        "name": "Others - Social Media",
        "subject": "John liked your photo on Instagram",
        "body": "John Smith liked your photo. See what else is happening on Instagram.",
        "expected_category": "others",
    },
    {
        "name": "Spam - Lottery",
        "subject": "CONGRATULATIONS! You won $1,000,000",
        "body": "You are the lucky winner! Click here to claim your prize now. Limited time offer!",
        "expected_category": "spam",
    },
]

def test_ollama_health():
    print("\n[1] Checking Ollama health...")
    oc = OllamaClassifier()
    ok = oc.check_health()
    if ok:
        print("    OK - Ollama is running\n")
    else:
        print("    FAILED - Ollama is not reachable. Start it with: ollama serve\n")
    return ok

def test_classifications():
    print("[2] Testing email classification via Ollama...")
    classifier = EmailClassifier()
    all_ok = True
    for tc in test_cases:
        cat, conf = classifier.classify(tc["subject"], tc["body"])
        status = "PASS" if cat == tc["expected_category"] else "MISMATCH"
        if status != "PASS":
            all_ok = False
        print(f"    [{status}] {tc['name']}")
        print(f"           Subject: {tc['subject']}")
        print(f"           Expected: {tc['expected_category']} | Got: {cat} (conf: {conf:.2f})")
        # Show routing result
        routing = route_email("spam" if cat == "spam" else "not_spam", cat, conf, 0.0)
        print(f"           Routes to: {routing['routed_folder']} | Action: {routing['routed_action']}\n")
    return all_ok

def test_rule_fallback():
    print("[3] Testing rule-based fallback (Ollama bypass)...")
    import app.core.settings as settings_mod
    original = settings_mod.settings.ollama_enabled
    settings_mod.settings.ollama_enabled = False
    classifier = EmailClassifier()
    cat, conf = classifier.classify("Invoice for project", "Please find attached invoice")
    settings_mod.settings.ollama_enabled = original
    if cat == "business":
        print("    PASS - Fallback rules working correctly\n")
        return True
    else:
        print(f"    FAIL - Expected 'business', got '{cat}'\n")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Ollama SLM Classification Test Suite")
    print("=" * 60)

    health = test_ollama_health()
    if health:
        test_classifications()
    else:
        print("Skipping classification tests - Ollama not reachable")
        print("Test fallback rules instead...\n")

    test_rule_fallback()

    print("=" * 60)
    print("Done. Open http://localhost:8000/dashboard to see the UI.")
    print("=" * 60)
