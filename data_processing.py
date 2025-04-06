import re


def normalize(text):
    """Normalize a string: lowercase, remove non-alphanumerics."""
    return re.sub(r'[^a-zA-Z0-9]', '', str(text)).lower()

tag_to_discipline = {
    "STEM": [
        "Engineering",
        "Physical Sciences",
        "Physical Sciences/Math",
        "Life Sciences",
        "Architecture",
        "Other Health Science",
        "Education"
    ],
    "HEALTH": [
        "Other Health Science",
        "Social Sciences",
        "Public Health"
    ],
    "ARTS": ["Arts & Humanities"],
    "SOCIAL SCIENCE": ["Social Sciences", "Public Admin"],
    "BUSINESS": ["Business"],
    "HUMANITIES": ["Arts & Humanities"],
    "RELIGIOUS": ["Arts & Humanities"],
    "GENERAL": ["Other/Interdisciplinary"],
    "LEADERSHIP": ["Other/Interdisciplinary"],
    "MULTICULTURAL": ["Arts & Humanities"],
    "LANGUAGE": ["Arts & Humanities"]
}

def assign_major_discipline(major_str):
    """
    Assigns a broad discipline to a major string using keywords and heuristics.
    """
    norm_major = normalize(major_str)

    # Engineering-related
    if any(keyword in norm_major for keyword in [
        "computerscience", "computerengineering", "computer", "cyber", "security",
        "robotic", "ai", "artificialintelligence", "electrical", "radio",
        "aerospace", "mechanical", "civil", "engineering"
    ]):
        return "Engineering"

    # Life sciences
    if any(keyword in norm_major for keyword in [
        "biology", "biological", "biochem", "molecular", "neuro", "ecology", "life"
    ]):
        return "Life Sciences"

    # Physical sciences
    if any(keyword in norm_major for keyword in [
        "physics", "chemistry", "chemical", "geology", "astronomy", "earth"
    ]):
        return "Physical Sciences/Math"

    # Math and Computer Science
    if "math" in norm_major or "statistics" in norm_major:
        return "Physical Sciences/Math"
    if "computerscience" in norm_major:
        return "Computer Science"

    # Health and Medicine
    if any(keyword in norm_major for keyword in [
        "nursing", "pharmacy", "publichealth", "epidemiology", "medicine", "clinical"
    ]):
        return "Public Health"
    if "health" in norm_major:
        return "Other Health Science"

    # Business
    if any(keyword in norm_major for keyword in [
        "business", "finance", "accounting", "management", "marketing", "economics"
    ]):
        return "Business"

    # Arts & Humanities
    if any(keyword in norm_major for keyword in [
        "art", "history", "literature", "music", "theater", "philosophy",
        "religion", "dance", "language", "writing", "creative"
    ]):
        return "Arts & Humanities"

    # Social sciences
    if any(keyword in norm_major for keyword in [
        "sociology", "psychology", "political", "anthropology", "education",
        "teaching", "law", "legal", "geography", "criminology"
    ]):
        return "Social Sciences"

    # Architecture
    if "architecture" in norm_major:
        return "Architecture"

    # Education
    if "education" in norm_major:
        return "Education"

    return "Other/Interdisciplinary"
