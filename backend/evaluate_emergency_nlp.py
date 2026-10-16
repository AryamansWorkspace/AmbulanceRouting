
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.metrics import accuracy_score, classification_report

from backend.emergency_nlp import DATA

# Prepare synthetic examples and their labels
texts, labels = [], []
for category, examples in DATA.items():
    texts.extend(examples)
    labels.extend([category] * len(examples))

# Keep each category represented in both sets
X_train, X_test, y_train, y_test = train_test_split(
    texts, labels, test_size=0.25,
    random_state=42, stratify=labels
)

# Train on the training split only
model = make_pipeline(
    TfidfVectorizer(ngram_range=(1, 2)),
    LogisticRegression(max_iter=1000, random_state=42),
)
model.fit(X_train, y_train)

# Evaluate on held-out examples
predictions = model.predict(X_test)

print(f"Training examples: {len(X_train)}")
print(f"Test examples: {len(X_test)}")
print(f"Accuracy: {accuracy_score(y_test, predictions):.3f}")
print("\nClassification report:")
print(classification_report(
    y_test, predictions, zero_division=0
))
