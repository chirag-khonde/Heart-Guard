# HeartGuard Lifestyle Risk Lexicon Reference

This document provides the complete reference for the HeartGuard predefined cardiovascular lifestyle risk categories, point weights, severity classifications, and keyword triggers.

Primary triggers originate directly from the HeartGuard project specification; additional variations were introduced to handle colloquial patient descriptions while maintaining strict clinical interpretability.

---

## 1. Smoking

- **Risk Points:** `+25`
- **Severity Level:** `High`
- **Direction:** `increases_lifestyle_risk`

### Documented Primary Triggers (Project Specification)
- `smoke`
- `smoking`
- `cigarette`
- `cigarettes`
- `tobacco`
- `nicotine`

### Additional Textual Variations
- `cigar`
- `cigars`
- `vape`
- `vaping`
- `vapes`
- `chain smoker`
- `chain smoking`

### Negation Patterns
- `do not smoke`, `don't smoke`, `never smoke`, `never smoked`, `not smoking`, `no smoking`, `quit smoking`, `stopped smoking`, `without smoking`

---

## 2. Physical Inactivity

- **Risk Points:** `+15`
- **Severity Level:** `High`
- **Direction:** `increases_lifestyle_risk`

### Documented Primary Triggers (Project Specification)
- `no exercise`
- `sedentary`
- `desk job`

### Additional Textual Variations
- `inactive`
- `inactivity`
- `little exercise`
- `no physical activity`
- `rarely exercise`
- `never exercise`
- `mostly sitting`
- `not exercising`
- `no regular exercise`
- `lack of exercise`
- `no workout`
- `couch potato`
- `barely exercise`
- `hardly exercise`

### Positive Exercise Counters (Exclusions)
- `exercise regularly`, `regular exercise`, `daily exercise`, `work out every`, `exercise 5 days`, `active lifestyle`, `physically active`
*(Unless explicitly negated, e.g., "no regular exercise")*

---

## 3. Unhealthy Diet

- **Risk Points:** `+18`
- **Severity Level:** `Moderate`
- **Direction:** `increases_lifestyle_risk`

### Documented Primary Triggers (Project Specification)
- `oily food`
- `junk`
- `fast food`
- `fried`

### Additional Textual Variations
- `fried food`
- `unhealthy food`
- `processed food`
- `high fat food`
- `too much junk food`
- `junk food`
- `fatty food`
- `sugary food`
- `deep fried`
- `oily foods`
- `fast foods`
- `fried foods`

### Negation & Healthy Diet Counters
- `avoid junk food`, `avoid fast food`, `avoid oily food`, `healthy diet`, `clean eating`, `balanced diet`, `eat healthy`

---

## 4. Poor Sleep

- **Risk Points:** `+12`
- **Severity Level:** `Moderate`
- **Direction:** `increases_lifestyle_risk`

### Documented Primary Triggers (Project Specification)
- `sleep 5 hours`
- `insomnia`
- `poor sleep`

### Additional Textual Variations
- `sleeping 5 hours`
- `only 5 hours sleep`
- `less sleep`
- `lack of sleep`
- `sleep deprivation`
- `sleepless`
- `broken sleep`
- `trouble sleeping`
- `cannot sleep`
- `cant sleep`
- `sleep disorder`
- `poor quality sleep`
- `disturbed sleep`

### Numeric Sleep Hour Rule
- Matches expressions: `<hours> hours of sleep` or `sleep <hours> hours`.
- **Duration < 6.0 hours:** Triggers `Poor Sleep (+12 pts)`
- **Duration ≥ 6.0 hours:** Adequate sleep duration, does **NOT** trigger risk.

---

## 5. Family History

- **Risk Points:** `+20`
- **Severity Level:** `High`
- **Direction:** `increases_lifestyle_risk`

### Documented Primary Triggers (Project Specification)
- `family history`
- `heart attack`
- `cardiac`

### Additional Textual Variations
- `family history of heart disease`
- `family history of heart attack`
- `father had heart attack`
- `mother had heart attack`
- `parent had cardiac disease`
- `parents had heart disease`
- `history of heart disease`
- `family history of cardiac`
- `dad had heart attack`
- `mom had heart attack`
- `cardiac history`

### Negation Patterns
- `no family history`, `no cardiac history`, `no heart attack in family`

---

## 6. Alcohol Use

- **Risk Points:** `+10`
- **Severity Level:** `Low`
- **Direction:** `increases_lifestyle_risk`

### Documented Primary Triggers (Project Specification)
- `drink`
- `alcohol`
- `beer`
- `wine`

### Additional Textual Variations
- `liquor`
- `spirits`
- `whiskey`
- `vodka`
- `cocktails`
- `alcoholic`
- `heavy drinking`
- `binge drinking`
- `drink alcohol`
- `drink beer`
- `drink wine`
- `drink heavily`
- `drink occasionally`

### Contextual Disambiguation Exclusions
- The verb `drink` does **NOT** trigger alcohol use when followed by non-alcoholic items:
  - `water`, `milk`, `tea`, `coffee`, `juice`, `soda`, `smoothie`, `electrolyte`
- Examples:
  - *"I drink 3 liters of water."* → **NOT detected**
  - *"I drink 2 cups of coffee."* → **NOT detected**
  - *"I drink occasionally."* → **Detected (+10 pts)**

---

## Summary of Points & Maximum Cap

| Factor | Points | Severity |
|---|---|---|
| Smoking | 25 | High |
| Family History | 20 | High |
| Unhealthy Diet | 18 | Moderate |
| Physical Inactivity | 15 | High |
| Poor Sleep | 12 | Moderate |
| Alcohol Use | 10 | Low |
| **Sum of All Factors** | **100** | — |
| **Maximum Capped Score** | **100** | — |
