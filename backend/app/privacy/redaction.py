import re
import spacy
from core_logic.Accessories.exception import CustomException
from core_logic.Accessories.logger import logging

# --- Load spaCy model once ---
try:
    nlp = spacy.load("en_core_web_sm")
    # print("spaCy model 'en_core_web_sm' loaded successfully for PII redaction.")
except OSError:
    print("spaCy model not found. Please run 'poetry run python -m spacy download en_core_web_sm'")
    nlp = None

# --- Regex patterns ---
PII_PATTERNS = {
    # 16 digits with or without separators
    "CREDITCARD": re.compile(r"\b(?:\d{4}[- ]?){3}\d{4}\b|\b\d{16}\b"),
    "EMAIL": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
    # ndian and US formats
    "PHONE": re.compile(r"(?:\+?\d{1,3}[ -]?\d{3}[ -]?\d{3}[ -]?\d{4})|(?:\d{10})|(?:\+\d{2}[ -]?\d{6}[ -]?\d{4})"),
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
    # Use unique, non-alphabetic tokens that spaCy will never split or match as entities
    return (
        text.replace("[EMAIL]", "§§EMAIL§§")
            .replace("[PHONE]", "§§PHONE§§")
            .replace("[CREDITCARD]", "§§CREDITCARD§§")
    )

def _unmask_placeholders(text: str) -> str:
    return (
        text.replace("§§EMAIL§§", "[EMAIL]")
            .replace("§§PHONE§§", "[PHONE]")
            .replace("§§CREDITCARD§§", "[CREDITCARD]")
    )


def redact_pii(text: str) -> str:
    if not nlp:
        return text

    # Step 1: Find all regex PII spans (credit card, email, phone) in original text
    regex_spans = []
    for label, pattern in [
        ("CREDITCARD", PII_PATTERNS["CREDITCARD"]),
        ("EMAIL", PII_PATTERNS["EMAIL"]),
        ("PHONE", PII_PATTERNS["PHONE"]),
    ]:
        for match in pattern.finditer(text):
            start, end = match.start(), match.end()
            if label == "CREDITCARD":
                cc_num = match.group()
                if not ("-" in cc_num or " " in cc_num or len(cc_num) == 16):
                    continue
                if not luhn_check(cc_num):
                    continue
            regex_spans.append((start, end, f"[{label}]"))

    # Step 2: Mask regex PII in original text (non-overlapping)
    regex_spans.sort()
    merged = []
    for start, end, repl in regex_spans:
        if merged and start < merged[-1][1]:
            continue
        merged.append((start, end, repl))
    result = []
    last = 0
    for start, end, repl in merged:
        result.append(text[last:start])
        result.append(repl)
        last = end
    result.append(text[last:])
    redacted_text = ''.join(result)

    # Step 3: Mask placeholders for spaCy
    masked_text = _mask_placeholders(redacted_text)

    # Step 4: Preprocess for NER
    def preprocess_for_ner(text):
        text = re.sub(r'([a-z])\s+([A-Z])', r'\1. \2', text)
        text = re.sub(r'(?i)(my name is|i am|i\'m|called|named)\s+([a-z]+)',
                     lambda m: f"{m.group(1)} {m.group(2).capitalize()}", text)
        text = re.sub(r'(^|[.!?]\s+)([a-z])', lambda m: m.group(1) + m.group(2).upper(), text)
        return text
    masked_text_for_ner = preprocess_for_ner(masked_text)

    # Step 5: Run spaCy NER
    protected_tokens = {"§§EMAIL§§", "§§PHONE§§", "§§CREDITCARD§§"}
    doc = nlp(masked_text_for_ner)

    # Find all placeholder spans in masked_text
    placeholder_spans = []
    for token in protected_tokens:
        for match in re.finditer(re.escape(token), masked_text):
            placeholder_spans.append((match.start(), match.end()))
    # Utility to check if a span overlaps any placeholder
    def overlaps_placeholder(start, end):
        for p_start, p_end in placeholder_spans:
            if start < p_end and end > p_start:
                return True
        return False

    # Step 6: Find NER entity spans (PERSON, ORG, GPE, LOC) in masked text, skipping placeholders
    entity_spans = []
    for ent in doc.ents:
        if overlaps_placeholder(ent.start_char, ent.end_char):
            continue
        text_at_entity = masked_text[ent.start_char:ent.end_char]
        # If this looks like a name after "my name is" but was labeled as ORG, change to PERSON
        if ent.label_ == "ORG" and re.search(r'(?i)(name is|am|called|i\'m) ' + re.escape(text_at_entity), masked_text):
            entity_label = "PERSON"
        else:
            entity_label = ent.label_
        if entity_label in ["PERSON", "GPE", "ORG", "LOC"]:
            entity_spans.append((ent.start_char, ent.end_char, f"[{entity_label}]"))

    # Step 7: Remove overlaps among entities
    entity_spans.sort()
    filtered = []
    for start, end, repl in entity_spans:
        if filtered and start < filtered[-1][1]:
            continue
        filtered.append((start, end, repl))

    # Step 8: Apply NER entity replacements in masked_text (single pass)
    result = []
    last = 0
    for start, end, repl in filtered:
        result.append(masked_text[last:start])
        result.append(repl)
        last = end
    result.append(masked_text[last:])
    masked_text = ''.join(result)

    # Step 9: Fallback for "my name is X" patterns not caught by spaCy (only if not already redacted)
    def fallback_name_replacer(match):
        name = match.group(1)
        # Only replace if not already redacted
        if f"[PERSON]" in name or f"[{name}]" in masked_text:
            return match.group(0)
        pat = re.compile(rf'\[{name}\]')
        if pat.search(masked_text):
            return match.group(0)
        return match.group(0).replace(name, "[PERSON]")
    # Only match 'my name is' (not 'called' or 'named' or 'i am' or 'i\'m')
    name_pattern = r'(?i)my name is ([A-Z][a-z]{2,})\b'
    masked_text = re.sub(name_pattern, fallback_name_replacer, masked_text)

    # Step 10: Unmask placeholders
    final_text = _unmask_placeholders(masked_text)
    # Step 11: Clean up spacing and punctuation
    final_text = re.sub(r'(\[\w+\])([A-Za-z])', r'\1 \2', final_text)
    final_text = re.sub(r'\s+', ' ', final_text).strip()
    return final_text


# --- Example usage ---
if __name__ == "__main__":
    sample_text = (
        "Hi my name is Vinay Chopra my number is 8910238908 , I live in mumbai, i am facing depression issues can u help"
        "Hi my name is Vikas. My number is 8910238908. "
        "I live in Mumbai. I am facing Depression issues, can you help? and i have a disease called Diabetes."
        "My email is vikas@example.com and my credit card is 4111-1111-1111-1111. "
        "I work at Acme Corp in New York. Please keep this information confidential."
    )
    redacted = redact_pii(sample_text)
    print("Original Text:\n", sample_text)
    print("\nRedacted Text:\n", redacted)
