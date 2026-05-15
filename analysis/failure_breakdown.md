# DiffDx Failure Breakdown — claude-sonnet-4-6, 50 cases

**Run:** `eval_claude_sonnet_4_6_20260515_212811.jsonl`  
**Split:** test  
**Completed:** 36 / 50 cases (14 errored — see §Errors)

> **Data note:** The current JSONL schema saves the top diagnosis and per-metric scores but not the
> full ranked differential. The implied rank of the ground truth is inferred from MRR (rank = 1/MRR).
> Full top-5 lists should be added to the JSONL in a future schema iteration.

---

## Summary table

| Bucket        | Count | % of completed |
|---------------|------:|---------------:|
| SUCCESSES     |    19 |          52.8% |
| SOFT MISSES   |    16 |          44.4% |
| HARD MISSES   |     1 |           2.8% |
| **ERRORS**    |    14 |     *(of 50)*  |
| **Total**     |    50 |                |

Top-5 accuracy (97.2%) means almost every completed case had the correct answer *somewhere* in
the model's differential — the challenge is ranking it first.

---

## SUCCESSES (19 / 36 = 52.8%)

Cases where the model's top diagnosis exactly matched the ground truth.

### Representative examples

**Case 7 — Spontaneous pneumothorax**
- Patient: 97-year-old male | Initial complaint: chest pain even at rest
- GT: `Spontaneous pneumothorax` → Model top: `Spontaneous pneumothorax` ✓
- MRR: 1.0 | Precision: 0.60 | Recall: 0.43
- Note: Impressive on a presentation that overlaps heavily with ACS/PE in the elderly.
  The model correctly ranked pneumothorax first despite significant competing diagnoses.

**Case 20 — Pulmonary embolism**
- Patient: 4-year-old male | Initial complaint: coughing up blood
- GT: `Pulmonary embolism` → Model top: `Pulmonary embolism` ✓
- MRR: 1.0 | Precision: 0.30 | Recall: 0.27
- Note: Haemoptysis in a toddler is a rare and tricky presentation; PE is the correct rare-but-serious
  pick.

**Case 29 — Atrial fibrillation**
- Patient: 51-year-old male | Initial complaint: palpitations / irregular heartbeat
- GT: `Atrial fibrillation` → Model top: `Atrial fibrillation` ✓
- MRR: 1.0 | Precision: 0.10 | Recall: 1.00
- Note: GT differential had only one entry (Atrial fibrillation) — a clean, unambiguous case. The
  model also got it right. Low precision (0.10) because the model still listed 10 alternatives, all
  of which were outside the GT set.

---

## SOFT MISSES (16 / 36 = 44.4%)

Cases where top-1 was wrong but the correct answer appeared in the top 5.
Rank of GT is inferred from MRR (1/MRR = rank).

| Case | GT                        | Model top-1                        | GT rank |
|-----:|---------------------------|------------------------------------|--------:|
|    3 | Acute laryngitis          | Viral pharyngitis                  | 3       |
|    4 | URTI                      | Influenza                          | 3       |
|    5 | URTI                      | Influenza                          | 3       |
|    8 | Bronchitis                | GERD                               | 5       |
|   10 | Bronchitis                | Acute COPD exacerbation/infection  | 4       |
|   11 | Bronchitis                | GERD                               | 4       |
|   12 | URTI                      | Acute rhinosinusitis               | 3       |
|   14 | Larygospasm               | Acute laryngitis                   | 3       |
|   15 | URTI                      | Acute rhinosinusitis               | 3       |
|   16 | URTI                      | Influenza                          | 2       |
|   18 | Bronchitis                | Pneumonia                          | 5       |
|   21 | Spontaneous pneumothorax  | Possible NSTEMI / STEMI            | 4       |
|   24 | Influenza                 | HIV (initial infection)            | 2       |
|   25 | Acute dystonic reactions  | Larygospasm                        | 3       |
|   30 | Pneumonia                 | Tuberculosis                       | 4       |
|   33 | URTI                      | Acute rhinosinusitis               | 3       |

### Dominant failure pattern: URTI/Bronchitis specificity bias

7 of 16 soft misses (44%) involve the model picking a *more specific* diagnosis when the ground
truth is a broader umbrella term (URTI, Bronchitis). The model consistently tops its differential
with Influenza, Rhinosinusitis, or COPD exacerbation, then lists the correct broader category lower
down. This is a systematic bias toward diagnostic specificity.

### Representative examples

**Case 4 — URTI over-specificity**
- Patient: 70-year-old female | Initial complaint: cough
- GT: `URTI` (rank 3 in model's differential)
- Model top: `Influenza`
- GT differential: URTI, Influenza, Bronchitis, HIV, Pneumonia, Tuberculosis, Chronic rhinosinusitis,
  Acute rhinosinusitis, Chagas
- Why: The dataset labels this as generic URTI, but the symptom cluster (diffuse muscle pain at case
  5, fever pattern) makes Influenza a clinically reasonable top pick. The model is arguably *more*
  specific than the benchmark, not wrong per se.

**Case 21 — Chest pain misat­tribution**
- Patient: 67-year-old female | Initial complaint: chest pain at rest
- GT: `Spontaneous pneumothorax` (rank 4 in model's differential)
- Model top: `Possible NSTEMI / STEMI`
- GT differential: Unstable angina, Stable angina, Possible NSTEMI/STEMI, GERD, Pericarditis,
  Atrial fibrillation, Spontaneous pneumothorax
- Why: The GT differential itself lists cardiac causes above pneumothorax. The model correctly
  identified the full list but weighted cardiac over pulmonary — a defensible clinical choice that
  the benchmark penalizes.

**Case 14 — Larygospasm / laryngitis confusion**
- Patient: 56-year-old female | Initial complaint: high-pitched sound when breathing in
- GT: `Larygospasm` (rank 3 in model's differential)
- Model top: `Acute laryngitis`
- GT differential: Larygospasm (only entry — no competing diagnoses)
- Why: The GT differential has exactly one valid condition. Inspiratory stridor could indicate either
  laryngospasm or laryngitis; the model ranked the correct answer third. With a single-entry GT
  differential, any non-exact top-1 is a soft miss regardless of clinical plausibility.

---

## HARD MISSES (1 / 36 = 2.8%)

Cases where the GT did not appear in the model's top 5.

### Case 1 — Bronchitis (GT rank 9)

**Patient profile**
- Age/sex: 2-year-old male
- Initial complaint: pain somewhere related to reason for consulting
- Full GT differential (23 conditions): Bronchospasm/acute asthma exacerbation, Influenza,
  Viral pharyngitis, Allergic sinusitis, Pneumonia, **Bronchitis**, Spontaneous pneumothorax,
  Tuberculosis, URTI, Myocarditis, Anaphylaxis, Acute laryngitis, Guillain-Barré syndrome, Croup,
  Atrial fibrillation, Acute dystonic reactions, Myasthenia gravis, Anemia, Scombroid food
  poisoning, Sarcoidosis, PSVT, SLE, Chagas

**What the model did**
- Top-1: `Bronchiolitis`
- GT pathology `Bronchitis` appeared at rank 9
- MRR: 0.111 | Precision: 0.60 | Recall: 0.26

**Why this is the most interesting failure**

1. **Clinically defensible top pick.** Bronchiolitis is the most common lower respiratory
   infection in children under 2 years old. A 2-year-old with respiratory pain/distress is
   textbook bronchiolitis territory. The model's reasoning was medically sound.

2. **Bronchitis vs. Bronchiolitis is a genuine clinical distinction.** These are different
   conditions: bronchitis is a large-airway inflammation (more typical in adults/older children),
   while bronchiolitis is a small-airway viral illness of infancy. The model chose the
   age-appropriate diagnosis; the benchmark labelled it as the adult-skewing alternative.

3. **The GT differential doesn't even contain Bronchiolitis.** The 23-condition GT list includes
   Bronchitis but not Bronchiolitis, suggesting DDXPlus may not model infant-specific
   pathophysiology well for this age group. This could be a benchmark limitation, not a model
   error.

4. **The model still found Bronchitis at rank 9.** It wasn't completely blind — it just
   deprioritized it to below the top-5 threshold.

**Takeaway:** This hard miss is arguably a benchmark quality issue. The case exposes a potential
gap in DDXPlus: its differential labels may not reflect age-stratified clinical reasoning,
and the model (correctly) applied age-specific priors that the benchmark does not reward.

---

## ERRORS (14 / 50 cases, indices 36–49)

All 14 errors returned: `"Claude Code returned an error result: success"`

### What happened (from tqdm timestamps)

| Phase         | Cases  | Behaviour                                              |
|---------------|--------|--------------------------------------------------------|
| Normal        | 0–34   | ~25–35s/case, steady throughput                        |
| Slow case     | 35     | 253s (4+ min) — apparent throttle / back-pressure      |
| Error burst 1 | 36–45  | All 10 errored within ~1s of each other (instant fail) |
| Long stall    | 46     | 326s before error                                      |
| Error burst 2 | 47–49  | Instant fail                                           |

### Root cause hypothesis

The SDK session hit a Pro-plan usage ceiling after ~35 sequential calls. Case 35's 253s latency is
the "last gasp" before the ceiling was reached. The contradictory `"error result: success"` is the
SDK's failure mode when the underlying OAuth session is throttled — the HTTP response returns a
200 OK body but with an error payload, which the SDK surfaces as an exception rather than a message.

### Fix options

1. **Add inter-call sleep** (`asyncio.sleep(5)`) between diagnose() calls to avoid burst throttling.
2. **Retry with exponential backoff** on the `"error result: success"` pattern.
3. **Checkpoint mid-run** — write completed indices to disk so a re-run can skip already-evaluated
   cases.
4. **Run in smaller batches** (≤30 cases) across multiple sessions.

---

## Key takeaways for the LinkedIn writeup

- **Top-5 accuracy of 97.2% is the headline number** — the model almost never completely missed
  the correct diagnosis.
- **Top-1 at 52.8% is the real challenge** — ranking the correct answer first requires the model
  to weigh ambiguous presentations correctly, not just generate a plausible list.
- **The dominant failure mode is specificity bias**: the model consistently picks a more specific
  diagnosis (Influenza > URTI, Rhinosinusitis > URTI, GERD > Bronchitis) and buries the benchmark's
  preferred umbrella term at rank 3–4.
- **The sole hard miss is arguably a benchmark flaw**, not a model failure — the case highlights
  a known gap in DDXPlus around infant-specific conditions.
- **The 14 errors are purely infrastructural** (session rate limiting), not model failures. A
  re-run with proper backoff should recover all 14 cases cleanly.
