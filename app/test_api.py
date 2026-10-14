import requests

BASE_URL = "http://127.0.0.1:8000"


def test_health():
    response = requests.get(f"{BASE_URL}/health", timeout=10)
    assert response.status_code == 200
    print("PASS: Health endpoint")


def test_chat(question, expected_source=None, should_have_answer=True):
    response = requests.post(
        f"{BASE_URL}/api/chat",
        json={"question": question},
        timeout=120,
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert "answer" in data, "Missing answer field"
    assert "sources" in data, "Missing sources field"

    answer = data["answer"].strip()
    sources = data["sources"]

    if should_have_answer:
        assert answer, "Answer is empty"

    if expected_source:
        source_names = [
            item.get("source", "").lower()
            for item in sources
        ]
        assert any(
            expected_source.lower() in name
            for name in source_names
        ), f"Expected source {expected_source} not found"

    print(f"PASS: {question}")
    print("Sources:", [item.get("citation") for item in sources])


if __name__ == "__main__":
    test_health()

    test_chat(
        "How much subsidy is available for certified maize seeds?",
        expected_source="tamilnadu.pdf",
    )

    test_chat(
        "விவசாயிகளுக்கு விதை மானியம் எவ்வளவு கிடைக்கும்?",
        expected_source="tamilnadu.pdf",
    )

    test_chat(
        "What documents are required to apply for seed subsidy?",
        should_have_answer=True,
    )

    test_chat(
        "What is the last date to apply for seed subsidy?",
        should_have_answer=True,
    )

    print("\nAll API checks completed.")