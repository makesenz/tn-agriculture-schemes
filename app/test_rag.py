
import re

from rag import ask_question


# ============================================================
# TEST CASES
# ============================================================

TEST_CASES = [
    {
        "name": "Maize seed subsidy amount",
        "question": (
            "How much subsidy is available for certified maize seeds?"
        ),
        "required": ["50%", "1200"],
        "required_source": "tamilnadu.pdf",
        "required_source_page": "page 1",
        "forbidden": [],
    },
    {
        "name": "Tamil seed subsidy and oilseeds eligibility",
        "question": "விவசாயிகளுக்கு விதை மானியம் எவ்வளவு கிடைக்கும்?",
        "required": [
            "50%",
            "1200",
            "மக்காச்சோளம்",
            "எண்ணெய் வித்துக்கள்",
        ],
        "required_source": "tamilnadu.pdf",
        "required_source_page": "page 1",
        "forbidden": [],
        "check_oilseeds_eligibility": True,
    },
    {
        "name": "Seed subsidy documents",
        "question": (
            "What documents are required to apply for seed subsidy?"
        ),
        "required": [],
        "required_source": None,
        "required_source_page": None,
        "forbidden": [
            "submit aadhaar",
            "soil test report is required",
            "bank passbook is required",
            "land proof is required",
        ],
        "must_acknowledge_missing_info": True,
        "expect_no_sources": True,
    },
    {
        "name": "Seed subsidy deadline",
        "question": (
            "What is the last date to apply for seed subsidy?"
        ),
        "required": [],
        "required_source": None,
        "required_source_page": None,
        "forbidden": [],
        "must_acknowledge_missing_info": True,
        "expect_no_sources": True,
    },
]


# ============================================================
# PHRASES INDICATING MISSING EVIDENCE
# ============================================================


MISSING_INFO_PHRASES = [
    # English
    "does not provide information",
    "does not provide any information",
    "does not mention",
    "does not specify",
    "not specified in the available sources",
    "not mentioned in the available sources",
    "available sources do not specify",
    "not available in the retrieved context",
    "retrieved context does not contain",
    "the provided context does not contain",
    "provided context does not contain information",
    "does not contain information",
    "unable to find",
    "cannot determine",
    "the source does not state",
    "not stated in the source",
    "information is not available",
    "no information was found",
    "not provided in the available context",
    "cannot provide a clear answer",
    "the requested information is not available",

    # Tamil
    "குறிப்பிடப்படவில்லை",
    "குறிப்பிடவில்லை",
    "தகவல் இல்லை",
    "தகவல் கிடைக்கவில்லை",
    "கண்டறிய முடியவில்லை",
    "தகவல் வழங்கப்படவில்லை",
    "ஆதாரங்களில் இல்லை",
    "ஆதாரங்களில் குறிப்பிடப்படவில்லை",
    "இந்தக் குறிப்பிட்ட உள்ளடக்கத்தில் இல்லை",
    "இந்த குறிப்பிட்ட உள்ளடக்கத்தில் இல்லை",
    "தெளிவான பதில் வழங்க முடியவில்லை",
    "தேவையான ஆவணங்கள் குறித்து தெளிவான பதில் வழங்க முடியவில்லை",
]



# ============================================================
# NORMALIZATION HELPERS
# ============================================================

def normalize(text: str) -> str:
    """Normalize whitespace and case for reliable text checks."""
    return re.sub(
        r"\s+",
        " ",
        str(text or ""),
    ).strip().casefold()


def get_answer(result: dict) -> str:
    """Extract answer text safely."""
    return str(result.get("answer", "") or "")


def get_sources(result: dict) -> list:
    """Extract sources safely."""
    sources = result.get("sources", [])

    if not isinstance(sources, list):
        return []

    return sources


def get_source_text(sources: list) -> str:
    """Convert source metadata into searchable text."""
    parts = []

    for source in sources:
        if isinstance(source, dict):
            for key in (
                "source",
                "citation",
                "file",
                "page",
                "filename",
            ):
                value = source.get(key)

                if value is not None:
                    parts.append(str(value))

        elif isinstance(source, str):
            parts.append(source)

    return normalize(" ".join(parts))


def has_missing_info_message(answer: str) -> bool:
    """Check whether the answer acknowledges missing evidence."""
    normalized_answer = normalize(answer)

    return any(
        normalize(phrase) in normalized_answer
        for phrase in MISSING_INFO_PHRASES
    )


# ============================================================
# OILSEEDS ELIGIBILITY VALIDATION
# ============================================================

def validate_oilseeds_eligibility(answer: str) -> list:
    """
    Validate the essential oilseeds eligibility conditions.

    The source condition is that farmers must produce and supply
    Foundation and certified-class seeds to the department.
    """

    errors = []
    normalized_answer = normalize(answer)

    # Foundation seed terminology: English or Tamil.
    foundation_present = any(
        phrase in normalized_answer
        for phrase in [
            "foundation",
            "அடிப்படை விதை",
        ]
    )

    # Certified-class seed terminology: English or Tamil.
    certified_present = any(
        phrase in normalized_answer
        for phrase in [
            "certified",
            "சான்றளிக்கப்பட்ட",
        ]
    )

    # Department terminology: English or Tamil.
    department_present = any(
        phrase in normalized_answer
        for phrase in [
            "department",
            "துறைக்கு",
            "திணைக்களத்திற்கு",
            "வேளாண்மைத் துறைக்கு",
            "வேளாண் துறைக்கு",
        ]
    )

    # Production must be preserved, not just supplying seeds.
    production_present = any(
        phrase in normalized_answer
        for phrase in [
            "produce",
            "producing",
            "produced",
            "உற்பத்தி",
        ]
    )

    # Supply/delivery must also be preserved.
    supply_present = any(
        phrase in normalized_answer
        for phrase in [
            "supply",
            "supplied",
            "supplying",
            "provide",
            "வழங்க",
            "வழங்கும்",
            "அளிக்க",
        ]
    )

    if not foundation_present:
        errors.append(
            "Oilseeds eligibility must mention Foundation seeds "
            "in English or Tamil."
        )

    if not certified_present:
        errors.append(
            "Oilseeds eligibility must mention certified-class seeds "
            "in English or Tamil."
        )

    if not department_present:
        errors.append(
            "Oilseeds eligibility must mention the department."
        )

    if not production_present:
        errors.append(
            "Oilseeds eligibility must preserve the requirement "
            "to produce the seeds."
        )

    if not supply_present:
        errors.append(
            "Oilseeds eligibility must preserve the requirement "
            "to supply the seeds."
        )

    return errors


# ============================================================
# TEST RUNNER
# ============================================================

def run_test(test_case: dict) -> bool:
    print("\n" + "=" * 65)
    print(f"TEST: {test_case['name']}")
    print("=" * 65)

    try:
        result = ask_question(test_case["question"])

        if not isinstance(result, dict):
            print("\nRESULT: FAIL")
            print("Expected ask_question() to return a dictionary.")
            return False

        raw_answer = get_answer(result)
        answer = normalize(raw_answer)
        sources = get_sources(result)
        source_text = get_source_text(sources)

        print("Question:", test_case["question"])
        print("Answer:", raw_answer)

        displayed_sources = []

        for source in sources:
            if isinstance(source, dict):
                displayed_sources.append(
                    source.get("citation")
                    or source.get("source")
                    or source.get("filename")
                    or str(source)
                )
            else:
                displayed_sources.append(str(source))

        print("Sources:", displayed_sources)

        errors = []

        # ----------------------------------------------------
        # 1. Validate response
        # ----------------------------------------------------

        if not answer:
            errors.append("The answer is empty.")

        # ----------------------------------------------------
        # 2. Validate required facts
        # ----------------------------------------------------

        for fact in test_case.get("required", []):
            if normalize(fact) not in answer:
                errors.append(
                    f"Missing expected fact: {fact}"
                )

        # ----------------------------------------------------
        # 3. Validate expected source
        # ----------------------------------------------------

        required_source = test_case.get("required_source")

        if (
            required_source
            and normalize(required_source) not in source_text
        ):
            errors.append(
                f"Expected source not found: {required_source}"
            )

        # ----------------------------------------------------
        # 4. Validate source page
        # ----------------------------------------------------

        required_page = test_case.get("required_source_page")

        if (
            required_page
            and normalize(required_page) not in source_text
        ):
            errors.append(
                f"Expected page citation not found: {required_page}"
            )

        # ----------------------------------------------------
        # 5. Check unsupported claims
        # ----------------------------------------------------

        for phrase in test_case.get("forbidden", []):
            if normalize(phrase) in answer:
                errors.append(
                    f"Potential unsupported claim: {phrase}"
                )

        # ----------------------------------------------------
        # 6. Validate missing-evidence responses
        # ----------------------------------------------------

        if test_case.get("must_acknowledge_missing_info"):
            if not has_missing_info_message(raw_answer):
                errors.append(
                    "The answer must clearly state that the requested "
                    "information is not available in the retrieved evidence."
                )

        # ----------------------------------------------------
        # 7. Check expected absence of sources
        # ----------------------------------------------------

        if test_case.get("expect_no_sources") and sources:
            errors.append(
                "Expected no supporting sources, but sources were returned: "
                f"{displayed_sources}"
            )

        # ----------------------------------------------------
        # 8. Validate crop-specific oilseeds eligibility
        # ----------------------------------------------------

        if test_case.get("check_oilseeds_eligibility"):
            errors.extend(
                validate_oilseeds_eligibility(raw_answer)
            )

        # ----------------------------------------------------
        # 9. Print result
        # ----------------------------------------------------

        if errors:
            print("\nRESULT: FAIL")

            for error in errors:
                print("-", error)

            return False

        print("\nRESULT: PASS")
        return True

    except Exception as exc:
        print("\nRESULT: ERROR")
        print(f"{type(exc).__name__}: {exc}")
        return False


# ============================================================
# MAIN
# ============================================================

def main():
    passed = 0
    failed = 0

    for test_case in TEST_CASES:
        if run_test(test_case):
            passed += 1
        else:
            failed += 1

    total = passed + failed

    print("\n" + "=" * 65)
    print("REGRESSION TEST SUMMARY")
    print("=" * 65)
    print(f"Total:  {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")

    if failed:
        print("\nSome tests failed. Review the messages above.")
        raise SystemExit(1)

    print("\nAll regression tests passed.")


if __name__ == "__main__":
    main()
