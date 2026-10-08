# HeartGuard Lifestyle Text Analyzer / NLP Module (Phase 6)

## 1. Purpose

The Lifestyle Text Analyzer processes a patient's self-reported, free-text lifestyle description and converts it into a quantified, transparent cardiovascular lifestyle risk score between 0 and 100. It bridges subjective clinical notes and daily habits with rule-based, interpretable cardiovascular signals.

## 2. Input Format

The analyzer accepts raw, unstructured text up to 5,000 characters in length. It can handle both conversational multi-sentence narratives and brief keyword lists.

**Example Input:**
> *"I smoke about 10 cigarettes a day, eat a lot of oily food, work a desk job, sleep 5 hours, drink occasionally and have no regular exercise."*

## 3. NLTK Preprocessing & Normalization

The preprocessing pipeline ensures consistent, safe text normalization without destroying multi-word medical idioms:

1. **Unicode Standardization:** Normalizes accents and ligatures using `unicodedata.normalize("NFKD")`.
2. **Case Normalization:** Converts text to lowercase for consistent dictionary matching.
3. **Punctuation Filtering:** Preserves alphanumeric characters, hyphens (e.g. *high-fat*), apostrophes (e.g. *don't*), and numerical decimals (e.g. *5.5 hours*), converting extraneous punctuation to single spaces.
4. **Whitespace Collapse:** Collapses tabs, repeated spaces, and newlines into single spaces.

## 4. Tokenization

- **Primary Tokenizer:** Uses NLTK's `word_tokenize` powered by the `punkt` and `punkt_tab` data models.
- **Resource Management:** Safe initialization via `ensure_nltk_resources()`, which checks local caches once and avoids redundant network lookups.
- **Offline Fallback:** If NLTK models or internet connectivity are unavailable, it falls back seamlessly to word-boundary regex tokenization (`r"\b[\w'-]+\b"`), ensuring uninterrupted operation.

## 5. Risk Lexicon

The analyzer operates on a centralized, predefined cardiovascular risk lexicon (`src/nlp/risk_lexicon.py`) comprising 6 categories:

| Category | Display Name | Configured Points | Severity | Direction |
|---|---|---|---|---|
| `smoking` | Smoking | +25 | High | `increases_lifestyle_risk` |
| `physical_inactivity` | Physical Inactivity | +15 | High | `increases_lifestyle_risk` |
| `unhealthy_diet` | Unhealthy Diet | +18 | Moderate | `increases_lifestyle_risk` |
| `poor_sleep` | Poor Sleep | +12 | Moderate | `increases_lifestyle_risk` |
| `family_history` | Family History | +20 | High | `increases_lifestyle_risk` |
| `alcohol_use` | Alcohol Use | +10 | Low | `increases_lifestyle_risk` |

## 6. Keyword and Phrase Matching

Matching operates over normalized text using word boundaries (`\b`):
- **Multi-Word Phrase Priority:** Phrases are sorted longest-first (e.g., matching *"no regular exercise"* or *"family history of heart attack"* before individual words).
- **Evidence Extraction:** Extracts matching character spans and surrounding textual context for transparent user inspection.
- **Duplicate Prevention:** Even if a patient mentions smoking or cigarettes multiple times across a paragraph, points for the category are applied exactly once.

## 7. Contextual Disambiguation

1. **Alcohol vs. Non-Alcoholic Beverages:**
   - The ambiguous verb *"drink"* is checked against an exclusion list (`NON_ALCOHOLIC_DRINKS`) containing water, tea, coffee, milk, and juices.
   - *"I drink 3 liters of water"* → **Not detected**.
   - *"I drink beer on weekends"* → **Detected (+10 pts)**.
2. **Sleep Duration Quantification:**
   - Bare *"sleep"* does not trigger risk.
   - Regex matches quantified duration: `< 6` hours (e.g. *"sleep 5 hours"*, *"only 4.5 hours of sleep"*) triggers Poor Sleep (+12 pts).
   - Sleep `≥ 6` hours (e.g. *"sleep 8 hours"*) is recognized as adequate and not penalized.
3. **Physical Exercise Positive Counters:**
   - Mentions of regular workouts (*"exercise every morning"*, *"work out 5 days a week"*) prevent false positive inactivity flags.

## 8. Negation Handling

The rule-based negation detector inspects a token window preceding any matched keyword or phrase:
- Negation terms: `no`, `not`, `never`, `don't`, `doesn't`, `didn't`, `without`, `avoid`, `quit`, `stopped`.
- Clause-aware segmentation ensures that negations in prior clauses separated by commas, semicolons, or conjunctions (*"but"*) do not incorrectly negate subsequent clauses.
- **Examples:**
  - *"I do not smoke."* → Smoking NOT detected.
  - *"I don't drink alcohol."* → Alcohol NOT detected.
  - *"I avoid fast food."* → Unhealthy diet NOT detected.

## 9. Risk Scoring

$$\text{Raw Score} = \sum_{c \in \text{Detected Categories}} \text{Risk Points}(c)$$
$$\text{Lifestyle Risk Score} = \min(\text{Raw Score}, 100)$$

The score is mathematically bounded between 0 and 100.

## 10. Risk Categories

| Score Range | Category | Clinical Interpretation |
|---|---|---|
| **0 – 29** | `LOW` | Minimal predefined lifestyle risk signals detected |
| **30 – 59** | `MODERATE` | Moderate lifestyle risk signals detected |
| **60 – 84** | `HIGH` | Multiple significant lifestyle risk factors detected |
| **85 – 100** | `CRITICAL` | Severe accumulation of adverse lifestyle behaviors |

*Note: These are rule-based project indicators, not medical diagnostic thresholds.*

## 11. Limitations

1. **Rule-Based Lexicon:** Synonyms or phrasing outside the configured lexicon may not be recognized.
2. **Context Window:** Complex grammar, double negatives, or indirect expressions may lead to misinterpretations.
3. **Self-Report Bias:** Relies entirely on the accuracy and completeness of patient self-descriptions.
4. **Non-Diagnostic:** The score is a project-defined heuristic and is not a clinically validated cardiovascular risk score.

## 12. Example Output

```json
{
  "raw_text": "I smoke about 10 cigarettes a day, eat oily food, and sleep 5 hours.",
  "normalized_text": "i smoke about 10 cigarettes a day eat oily food and sleep 5 hours",
  "tokens": ["i", "smoke", "about", "10", "cigarettes", "a", "day", "eat", "oily", "food", "and", "sleep", "5", "hours"],
  "lifestyle_score": 55,
  "risk_category": "MODERATE",
  "detected_risk_factors": [
    {
      "category": "smoking",
      "display_name": "Smoking",
      "risk_points": 25,
      "severity": "High",
      "matched_terms": ["smoke", "cigarettes"],
      "evidence": "i smoke about 10 cigarettes a day",
      "direction": "increases_lifestyle_risk"
    },
    {
      "category": "unhealthy_diet",
      "display_name": "Unhealthy Diet",
      "risk_points": 18,
      "severity": "Moderate",
      "matched_terms": ["oily food"],
      "evidence": "eat oily food and",
      "direction": "increases_lifestyle_risk"
    },
    {
      "category": "poor_sleep",
      "display_name": "Poor Sleep",
      "risk_points": 12,
      "severity": "Moderate",
      "matched_terms": ["sleep 5 hours"],
      "evidence": "and sleep 5 hours",
      "direction": "increases_lifestyle_risk"
    }
  ],
  "total_detected_factors": 3,
  "top_risk_factors": [
    {
      "category": "smoking",
      "display_name": "Smoking",
      "risk_points": 25,
      "severity": "High"
    },
    {
      "category": "unhealthy_diet",
      "display_name": "Unhealthy Diet",
      "risk_points": 18,
      "severity": "Moderate"
    },
    {
      "category": "poor_sleep",
      "display_name": "Poor Sleep",
      "risk_points": 12,
      "severity": "Moderate"
    }
  ],
  "summary": "HeartGuard detected smoking, unhealthy diet, and poor sleep in the provided lifestyle description. These findings produced a lifestyle risk score of 55/100 (MODERATE).",
  "disclaimer": "HeartGuard is an academic/research prototype and is not a medical diagnostic system. The Lifestyle Risk Score is a rule-based project indicator and should not be interpreted as a clinically validated cardiovascular risk score."
}
```
