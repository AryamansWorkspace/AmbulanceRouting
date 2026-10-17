
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline

# Synthetic examples only; not real emergency reports
DATA = {
    "road_accident": [
        "car crash at junction", "motorcycle hit by truck",
        "pedestrian struck by vehicle", "road traffic accident",
        "vehicles collided", "van struck a cyclist",
        "truck overturned", "driver lost control and crashed",
    ],
    "breathing_emergency": [
        "struggling to breathe", "difficulty breathing",
        "shortness of breath", "gasping for air",
        "cannot breathe properly", "patient is breathless",
        "cannot catch breath", "trouble getting enough air",
    ],
    "cardiac_emergency": [
        "severe chest pain", "possible heart attack",
        "suspected cardiac arrest", "chest pressure",
        "pain around the heart", "tightness in chest",
        "crushing chest pain", "sudden chest discomfort",
    ],
    "fire_burn": [
        "building is on fire", "burned in a fire",
        "burned by hot water", "flames in a house",
        "serious burn injury", "kitchen caught fire",
        "hot liquid caused burns", "fire at a factory",
    ],
    "fall_injury": [
        "fell down stairs", "fell from a building",
        "possible broken bone", "fracture after falling",
        "slipped and injured leg", "fell from a ladder",
        "hurt ankle after slipping", "injured in a fall",
    ],
    "other": [
        "needs emergency assistance", "feeling unwell",
        "unknown medical emergency", "needs urgent help",
        "emergency reported", "send help to this location",
        "unspecified emergency", "unknown incident",
    ],
}

RULES = {
    "road_accident": [
        "accident", "crash", "collided", "collision", "struck",
        "cyclist", "pedestrian", "overturned", "motorcycle",
    ],
    "breathing_emergency": [
        "breath", "gasping", "shortness of breath",
    ],
    "cardiac_emergency": [
        "chest pain", "chest pressure", "heart attack",
        "cardiac arrest", "tightness in chest",
    ],
    "fire_burn": [
        "fire", "flames", "burn", "hot liquid", "scald",
        "smoke",
    ],
    "fall_injury": [
        "fell", "fall", "slipped", "fracture", "broken bone",
    ],
    "other": ["unconscious", "unresponsive", "not responding"],
}

texts = [t for samples in DATA.values() for t in samples]
labels = [c for c, samples in DATA.items() for _ in samples]

model = make_pipeline(
    TfidfVectorizer(ngram_range=(1, 2)),
    LogisticRegression(max_iter=1000, random_state=42),
)
model.fit(texts, labels)


def categorize_emergency(description):
    if not isinstance(description, str) or not description.strip():
        raise ValueError("Enter an emergency description.")

    text = description.lower().strip()
    probabilities = model.predict_proba([text])[0]
    predicted = str(model.predict([text])[0])
    confidence = float(max(probabilities))

    matched = {
        category: [term for term in terms if term in text]
        for category, terms in RULES.items()
    }
    matched = {c: terms for c, terms in matched.items() if terms}
    detected = list(matched)

    if confidence < 0.40 and len(detected) == 1:
        category = detected[0]
        method = "rule_based_fallback"
    elif confidence < 0.40 and len(detected) > 1:
        category = "other"
        method = "rule_based_ambiguous"
    elif confidence < 0.40:
        category = predicted
        method = "tfidf_low_confidence"
    else:
        category = predicted
        method = "tfidf_logistic_regression"

    return {
        "category": category,
        "confidence": round(confidence, 3),
        "detected_categories": detected,
        "matched_terms": matched,
        "method": method,
        "is_medical_diagnosis": False,
    }


if __name__ == "__main__":
    examples = [
        "A motorcycle crashed into a car",
        "The person is struggling to breathe",
        "Someone has severe chest pain",
        "A worker was burned in a fire",
        "A person fell down the stairs",
        "An unknown emergency needs assistance",
    ]
    for example in examples:
        print(f"\n{example}\n{categorize_emergency(example)}")
 