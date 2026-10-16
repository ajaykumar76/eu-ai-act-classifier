# EU AI Act Risk-Tier Classifier (with guardrails and human review)

A small, locally run pipeline that takes a plain-English description of an AI system and proposes an
EU AI Act risk tier: **prohibited, high, limited, minimal or out of scope**. It retrieves the most
relevant provisions, asks a local LLM to choose a tier and cite them, then runs checks that route
doubtful answers to a human reviewer.

> **Not legal advice.** The provision summaries in `data/provisions.json` are my *paraphrases* of
> Regulation (EU) 2024/1689, not the official text. Verify against EUR-Lex before relying on anything.
> The labels were written by me (not a lawyer), and several cases are genuinely arguable.

The point of the project is **honest evaluation of a GRC-style AI assistant**, not a headline accuracy
number. The main result is about the checks, not the model.

## How it works

1. **Retrieve** the top-5 provisions for the description (sentence-transformers `all-MiniLM-L6-v2`, cosine similarity).
2. **Ask** a local LLM (Ollama `llama3.2`, JSON output) for a tier and citations, restricted to those candidates.
3. **Check** the answer. Any of these sends it to human review instead of auto-deciding:
   - a cited id is not in the candidate list (or none is cited)
   - the cited provisions do not support the chosen tier
   - the answer is *below* the tier of the top retrieved provision (the dangerous direction)
   - the answer is "prohibited" (a high-consequence verdict always gets human sign-off; this is a policy choice, not tuned)

Three systems are scored: **A** retrieval only, **B** LLM alone, **C** LLM + checks.

## Data

- `data/provisions.json`: paraphrased provisions (Art. 2 scope, Art. 5 prohibitions, Art. 6 / Annex I / Annex III high-risk, Art. 50 transparency, minimal-risk).
- `data/scenarios.json`: 41 hand-written scenarios, each with a gold tier and a difficulty label (clear or borderline).
  **30 dev** (used for tuning) and **11 test** (run once, at the end).

## Results

Dev was used to tune the prompt and checks. Test was run **once**, after the final version was fixed.

| Dev (n=30) | v1 | v2 | v3 (final) |
|---|---|---|---|
| LLM alone, accuracy | 22/30 (73%) | 14/30 (47%) | 20/30 (67%, CI 49-81%) |
| Citations valid | 60% (parser bug) | 97% | 93% |
| LLM cites a gold provision | 40% | 37% | 57% |
| Auto-decided | 13/30 | 24/30 | 14/30 (47%) |
| Accuracy on auto-decided | 85% | 54% | 79% |
| Rated too low among auto-decided | 0 | 0 | 0 |
| LLM errors caught by a flag | 6/8 | 5/16 | 7/10 |

| Test (n=11), final version | Result (95% Wilson CI) |
|---|---|
| A. Retrieval only, top-1 tier | 8/11 = 73% (43-90%) |
| B. LLM alone | 6/11 = 55% (28-79%) |
| B. Rated too low | 3 |
| B. Citations valid | 11/11 |
| C. Auto-decided (coverage) | 5/11 = 45% (21-72%) |
| C. Accuracy on auto-decided | 4/5 = 80% (38-96%) |
| C. Rated too low among auto-decided | **0** |
| C. LLM errors caught by a flag | 4/5 = 80% (38-96%) |

### What I take from this

- **The checks are the useful part.** Across v1, v2, v3 and the test run, nothing that was rated too low was ever decided automatically. On test, all 3 under-classified answers (a school emotion-inference system rated high instead of prohibited, and two transparency cases rated out of scope) went to review.
- **The LLM did not clearly beat plain retrieval on accuracy.** On dev the LLM was ahead (67-73% vs 63%); on test it was behind (55% vs 73%). With n=30 and n=11 the intervals overlap heavily, so I can't claim either is better. A 3B local model is not a reliable classifier of Article 5 conditions.
- **It is a triage aid, not an automatic classifier.** Only about 45% of cases are auto-decided; the rest need a person.
- **Tuning is fragile.** My first prompt change (v2) made things much worse: telling the model to prefer "prohibited" caused it to label 7 high-risk systems as prohibited, and a prompt example leaked into its answers. I kept v2 in the table on purpose.
- **Citation failures were partly my bug.** v1's low citation validity came from the model writing `id: X` instead of `X`. Fixing the format (not loosening the rule; ids must still come from the candidates) took validity to 93-100%.

## Known limitations

- **Small, author-written evaluation.** 41 scenarios, labels by a non-lawyer, 11 test cases. One test case is about 9 percentage points.
- **Paraphrased law.** Summaries may be incomplete or wrong in places. The Act's guidance and delegated acts will change how borderline cases are read.
- **Borderline labels are contestable.** For example, a tool that only sorts job applications into folders (S37) could reasonably be called high-risk under Annex III point 4; I labelled it minimal (narrow procedural task, Art. 6(3)) and kept the label rather than change it to match the model.
- **Only the dangerous direction is checked.** Over-classification (rating a harmless system too high) mostly passes without a flag. That costs extra compliance work, not a missed risk, but it is still an error.
- **One model, one embedding model, one seed of prompts.** Results will differ with other models.
- **Dev/test discipline.** I tuned across three rounds on dev only and ran test once. Even so, the final version was chosen after seeing dev results, and the test set is small.

## Run it

```powershell
pip install -r requirements.txt
ollama pull llama3.2
python src\01_classify_eval.py --split dev --no-llm            # retrieval only
python src\01_classify_eval.py --split dev --tag v3            # full dev run
python src\01_classify_eval.py --split test --tag final        # run once, at the end
```

Results are saved to `reports/results_<split>_<tag>.json`.

## Files

```
src/01_classify_eval.py   retrieval, LLM call, checks, three-system evaluation
data/provisions.json      paraphrased provisions
data/scenarios.json       41 labelled scenarios (dev/test split)
reports/                  saved results for each run
```
