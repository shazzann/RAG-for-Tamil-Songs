CONCEPT_DICTIONARY = {
    "eyes": [
        "eyes", "eye", "kan", "kann", "கண்", "கண்ணே",
        "vizhi", "விழி", "paarvai", "பார்வை",
        "nayanam", "நயனம்", "gaze", "look"
    ],
    "love": [
        "love", "kadhal", "kaadhal", "காதல்",
        "anbu", "அன்பு", "romance", "romantic"
    ],
    "sadness": [
        "sad", "sogam", "சோகம்", "துயரம்",
        "lonely", "loneliness", "தனிமை",
        "pirivu", "பிரிவு", "missing", "longing",
        "heartbreak", "pain"
    ],
    "rain": [
        "rain", "mazhai", "மழை", "drizzle", "cloud"
    ],
    "mother": [
        "mother", "amma", "அம்மா", "thai", "தாய்"
    ]
}


def expand_query(query: str):
    """
    Expand query with Tamil/Tanglish/English concept synonyms.
    """
    query_lower = query.lower()
    expanded_terms = set()

    for concept, terms in CONCEPT_DICTIONARY.items():
        for term in terms:
            if term.lower() in query_lower:
                expanded_terms.update(terms)

    if not expanded_terms:
        return query

    expanded_query = query + " " + " ".join(sorted(expanded_terms))

    return expanded_query