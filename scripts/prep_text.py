"""
Text preprocessor for TTS.
Converts a written digest into speech-friendly text so the TTS engine
doesn't stumble on version numbers, abbreviations, or dense formatting.
"""

import re


def prep_for_speech(text: str) -> str:
    """
    Transform digest text into natural-sounding speech text.
    Run this BEFORE sending to TTS.
    """
    text = strip_formatting(text)
    text = expand_version_numbers(text)
    text = expand_numbers_and_money(text)
    text = expand_abbreviations(text)
    text = add_section_pauses(text)
    text = clean_up_whitespace(text)
    return text


def strip_formatting(text: str) -> str:
    """Remove email/markdown formatting that sounds weird when read aloud."""
    # Remove section divider lines (=== or ---)
    text = re.sub(r'^[=\-]{3,}.*$', '', text, flags=re.MULTILINE)
    # Remove bullet point dashes at start of lines, keep the content
    text = re.sub(r'^[\s]*[-•]\s+', '', text, flags=re.MULTILINE)
    # Remove markdown bold/italic
    text = re.sub(r'\*{1,2}(.*?)\*{1,2}', r'\1', text)
    # Replace em dashes with a comma pause (TTS glitches on — and –)
    text = re.sub(r'\s*[—–]\s*', ', ', text)
    # Remove URLs and "Sources" section entirely
    text = re.sub(r'https?://\S+', '', text)
    text = re.sub(r'(?i)^sources.*', '', text, flags=re.MULTILINE | re.DOTALL)
    # Remove emoji
    text = re.sub(r'[☀️🎙️🔥💡🚀]', '', text)
    return text


def expand_version_numbers(text: str) -> str:
    """
    Turn version numbers into speakable text.
    "Gemini 3.1 Pro" → "Gemini three point one Pro"
    "GPT-5.2" → "G P T five point two"
    "Llama 4" → "Llama four"
    """
    # Named model versions with decimals: "Gemini 3.1" → "Gemini three point one"
    def replace_version(match):
        prefix = match.group(1)
        major = int_to_word(match.group(2))
        minor = int_to_word(match.group(3))
        suffix = match.group(4) or ""
        return f"{prefix} {major} point {minor} {suffix}".strip()

    # Match patterns like "Name X.Y" where X and Y are digits
    text = re.sub(
        r'((?:Gemini|GPT|Grok|Claude|Llama|Flash|Opus|Sonnet|Haiku|Studio)[\s\-]*)(\d+)\.(\d+)(\s*\w*)',
        replace_version,
        text,
        flags=re.IGNORECASE,
    )

    # Standalone version patterns that weren't caught: "v3.1", "version 2.0"
    def replace_standalone_version(match):
        prefix = match.group(1)
        major = int_to_word(match.group(2))
        minor = int_to_word(match.group(3))
        return f"{prefix}{major} point {minor}"

    text = re.sub(r'(v(?:ersion)?\s*)(\d+)\.(\d+)', replace_standalone_version, text, flags=re.IGNORECASE)

    # Expand hyphenated model names: "GPT-5" → "G P T five"
    # But only for known acronym prefixes
    def expand_acronym_model(match):
        acronym = " ".join(match.group(1))  # "GPT" → "G P T"
        number = int_to_word(match.group(2))
        return f"{acronym} {number}"

    text = re.sub(r'\b(GPT|ARC|XAI)[\-\s](\d+)', expand_acronym_model, text)

    return text


def expand_numbers_and_money(text: str) -> str:
    """
    Make numbers and money speakable.
    "$852 billion" → "852 billion dollars"
    "77.1%" → "77 point 1 percent"
    "2,400%" → "twenty-four hundred percent"
    "10M" → "10 million"
    """
    # Dollar amounts: "$3 billion" → "3 billion dollars"
    text = re.sub(r'\$(\d[\d,]*\.?\d*)\s*(billion|million|trillion)', r'\1 \2 dollars', text, flags=re.IGNORECASE)
    text = re.sub(r'\$(\d[\d,]*\.?\d*)', r'\1 dollars', text)

    # Cents per million: "$0.25/million" → "25 cents per million"
    text = re.sub(r'(\d+)\s*cents?\s*per\s*million', r'\1 cents per million', text, flags=re.IGNORECASE)

    # Percentages with decimals: "77.1%" → "77 point 1 percent"
    def replace_percent(match):
        whole = match.group(1)
        decimal = match.group(2)
        if decimal:
            return f"{whole} point {decimal} percent"
        return f"{whole} percent"

    text = re.sub(r'(\d[\d,]*)\.?(\d+)?%', replace_percent, text)

    # Large numbers with commas: "7,300" → "7,300" (TTS handles these OK)
    # But "2,400%" was already handled above

    # Shorthand millions/billions: "10M" → "10 million", "400B" → "400 billion"
    text = re.sub(r'(\d+)M\b', r'\1 million', text)
    text = re.sub(r'(\d+)B\b', r'\1 billion', text)
    text = re.sub(r'(\d+)K\b', r'\1 thousand', text)
    text = re.sub(r'(\d+)T\b', r'\1 trillion', text)

    return text


def expand_abbreviations(text: str) -> str:
    """Expand common abbreviations that TTS might mangle."""
    replacements = {
        r'\bQ1\b': 'Q 1',
        r'\bQ2\b': 'Q 2',
        r'\bQ3\b': 'Q 3',
        r'\bQ4\b': 'Q 4',
        r'\bAI\b': 'A I',
        r'\bAPI\b': 'A P I',
        r'\bAPIs\b': 'A P Is',
        r'\bLLMs?\b': 'L L Ms' if 's' else 'L L M',
        r'\bLLMs\b': 'L L Ms',
        r'\bLLM\b': 'L L M',
        r'\bTTS\b': 'T T S',
        r'\bNPCs?\b': 'N P Cs',
        r'\bNPC\b': 'N P C',
        r'\bBCG\b': 'B C G',
        r'\bWIPO\b': 'W I P O',
        r'\bU\.S\.\b': 'U S',
        r'\bU\.S\.A\.\b': 'U S A',
        r'\bxAI\b': 'x A I',
        r'\bARC-AGI\b': 'arc A G I',
        r'\bGPQA\b': 'G P Q A',
        r'\bSSML\b': 'S S M L',
        r'\bRSS\b': 'R S S',
    }
    for pattern, replacement in replacements.items():
        text = re.sub(pattern, replacement, text)
    return text


def add_section_pauses(text: str) -> str:
    """
    Add natural pauses between sections using SSML-like breaks.
    Edge TTS respects "..." as a longer pause.
    """
    # Section headers → spoken transitions with pauses
    section_intros = {
        r'(?i)^TOP STORY:?\s*': '\n\n... Starting with the top story. ... \n\n',
        r'(?i)^LLMs?\s*(?:AND|&)\s*CODING TOOLS\s*$': '\n\n... Next up, L L Ms and coding tools. ... \n\n',
        r'(?i)^INDUSTRY\s*(?:AND|&)\s*BUSINESS\s*$': '\n\n... In industry and business news. ... \n\n',
        r'(?i)^GAMING\s*(?:AND|&)\s*AI\s*$': '\n\n... In gaming and A I. ... \n\n',
        r'(?i)^QUICK HITS\s*$': '\n\n... And some quick hits. ... \n\n',
        r'(?i)^ONE THING TO TRY TODAY\s*$': '\n\n... And finally, one thing to try today. ... \n\n',
        r'(?i)^YOUR DAILY AI DIGEST.*$': 'Good morning! Here is your daily A I digest. ... \n\n',
    }

    for pattern, replacement in section_intros.items():
        text = re.sub(pattern, replacement, text, flags=re.MULTILINE)

    # Add a brief pause between paragraphs (double newline → ellipsis)
    text = re.sub(r'\n\n+', '\n\n... \n\n', text)
    # But don't stack pauses
    text = re.sub(r'(\.\.\.\s*){2,}', '... ', text)

    return text


def clean_up_whitespace(text: str) -> str:
    """Final cleanup pass."""
    # Collapse multiple spaces
    text = re.sub(r' {2,}', ' ', text)
    # Collapse excessive newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    # Strip leading/trailing whitespace
    text = text.strip()
    return text


def int_to_word(num_str: str) -> str:
    """Convert small integers to words for natural speech."""
    words = {
        '0': 'zero', '1': 'one', '2': 'two', '3': 'three', '4': 'four',
        '5': 'five', '6': 'six', '7': 'seven', '8': 'eight', '9': 'nine',
        '10': 'ten', '11': 'eleven', '12': 'twelve', '13': 'thirteen',
        '14': 'fourteen', '15': 'fifteen', '16': 'sixteen', '17': 'seventeen',
        '18': 'eighteen', '19': 'nineteen', '20': 'twenty',
    }
    return words.get(num_str, num_str)


# --- CLI: preview what TTS will actually hear ---
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python prep_text.py <input_file> [output_file]")
        print("  If no output file given, prints to stdout so you can review it.")
        sys.exit(1)

    with open(sys.argv[1], "r") as f:
        raw = f.read()

    prepped = prep_for_speech(raw)

    if len(sys.argv) >= 3:
        with open(sys.argv[2], "w") as f:
            f.write(prepped)
        print(f"Speech-ready text written to {sys.argv[2]}")
    else:
        print(prepped)
