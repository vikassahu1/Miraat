# Miraat/backend/app/privacy/redaction.py

import re
import spacy

# --- Load spaCy model once ---
try:
    nlp = spacy.load("en_core_web_sm")
    print("spaCy model 'en_core_web_sm' loaded successfully for PII redaction.")
except OSError:
    print("spaCy model not found. Please run 'poetry run python -m spacy download en_core_web_sm'")
    nlp = None

# --- Regex patterns ---
PII_PATTERNS = {
    "EMAIL": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
    # Phone: includes +, 7–15 digits, avoids credit card false matches
    "PHONE": re.compile(r"(?:\+?\d[\d\s().-]{7,15})"),
    # Credit card: 13–16 digits, allow spaces or dashes
    "CREDITCARD": re.compile(r"\b(?:\d[ -]*?){13,16}\b"),
}

# --- Luhn Algorithm for credit card validation ---
def luhn_check(card_number: str) -> bool:
    digits = re.sub(r"\D", "", card_number)  # strip spaces/dashes
    if not (13 <= len(digits) <= 16):
        return False

    total = 0
    reverse_digits = digits[::-1]

    for i, d in enumerate(reverse_digits):
        n = int(d)
        if i % 2 == 1:  # double every 2nd digit
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return total % 10 == 0

# --- Masking helpers so spaCy ignores placeholders ---
def _mask_placeholders(text: str) -> str:
    return (
        text.replace("[EMAIL]", "EMAILTOKEN")
            .replace("[PHONE]", "PHONETOKEN")
            .replace("[CREDITCARD]", "CCTOKEN")
    )

def _unmask_placeholders(text: str) -> str:
    return (
        text.replace("EMAILTOKEN", "[EMAIL]")
            .replace("PHONETOKEN", "[PHONE]")
            .replace("CCTOKEN", "[CREDITCARD]")
    )

# --- Main function ---
def redact_pii(text: str) -> str:
    if not nlp:
        return text

    redacted_text = text

    # --- 1. Regex redaction ---
    redacted_text = PII_PATTERNS["EMAIL"].sub("[EMAIL]", redacted_text)
    redacted_text = PII_PATTERNS["PHONE"].sub("[PHONE]", redacted_text)

    for match in PII_PATTERNS["CREDITCARD"].finditer(redacted_text):
        cc_num = match.group()
        if luhn_check(cc_num):
            redacted_text = redacted_text.replace(cc_num, "[CREDITCARD]")

    # --- 2. Mask placeholders so spaCy ignores them ---
    masked_text = _mask_placeholders(redacted_text)

    # --- 3. spaCy entity redaction ---
    doc = nlp(masked_text)
    for ent in reversed(doc.ents):
        if ent.label_ in ["PERSON", "GPE", "ORG", "LOC"]:
            masked_text = (
                masked_text[:ent.start_char]
                + f"[{ent.label_}]"
                + masked_text[ent.end_char:]
            )

    # --- 4. Unmask placeholders back ---
    return _unmask_placeholders(masked_text)


# --- Example usage ---
if __name__ == "__main__":
    sample_text = (
        "My name is John Doe. You can reach me at 7021872240 or +91 922232 1234. "
        "My email is 203efd@gmail.com. I live in New York and work at OpenAI. "
        "My credit card number is 1234-5678-9012-3456."
    )
    redacted = redact_pii(sample_text)
    print("Original Text:\n", sample_text)
    print("\nRedacted Text:\n", redacted)
