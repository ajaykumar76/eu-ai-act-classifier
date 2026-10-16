# An Evidence-Based AI Risk Register for My Own Local Security Tools

A risk register for the AI tools I built in earlier projects (SIEM triage, policy mapping, prompt-injection testing, ML intrusion detection). Each risk is mapped to the [OWASP Top 10 for LLM Applications (2025)](https://genai.owasp.org/llm-top-10/) and the [NIST AI Risk Management Framework](https://www.nist.gov/itl/ai-risk-management-framework). Where I measured a failure rate, the likelihood comes from that measurement instead of a guess, and the uncertainty is shown.

![Inherent vs residual risk heatmap](reports/heatmap.png)

## Key findings

1. **Mitigations moved the register a long way, but not everywhere.** Before mitigations: 5 Critical, 2 High, 6 Medium. After: 1 Critical, 3 High, 5 Medium, 4 Low.
2. **The biggest remaining risk is an unmitigated one.** The ML intrusion detector scoring F1 0.9993 on a random split but 0.54 on attack days it had not seen (R10) is Critical and still open. Prompt injection leaking a protected secret (R01) is next, High at 12 residual.
3. **"We saw zero failures" is weaker than it looks.** R03 (the small model under-triaging malicious alerts) drops from 25 to 5 after a safety floor, because 0 of 9 test attacks were missed. But 9 trials cannot rule out a failure rate near 30%, so the conservative score stays at 20. The same applies to R05 and R06 (0 failures in 10 and 5 trials).
4. **The top of the ranking is stable and the middle is not.** Across 5,000 simulations that vary impact and likelihood within my own uncertainty, R10 and R01 are in the top 3 in 75% and 66% of runs. Risks ranked 3rd to 8th change places often. R03 reaches the top 3 in 50% of runs even though its base score ranks 9th, which is another small-sample effect.
5. **Two risks are fully open with no mitigation implemented:** R10 (generalization to unseen attacks) and R12 (unverified models and dependencies).

## Top risks after mitigation

| Rank | ID | Risk | Residual score | Conservative | In top 3 |
|---|---|---|---|---|---|
| 1 | R10 | ML detector fails on attack types it has not seen | 16 Critical | 16 | 75% |
| 2 | R01 | Prompt injection leaks a protected secret | 12 High | 20 | 66% |
| 3 | R02 | Instruction hidden in log text steers the triage model | 10 High | 10 | 23% |
| 3 | R08 | Real compliance gap reported as covered | 10 High | 10 | 23% |
| 5 | R07 | Retrieval misses the correct control or technique | 9 Medium | 12 | 15% |

The full register with evidence, mitigations and framework mappings is in `data/risks.json` and `reports/register_scored.csv`.

## Method

**Scoring.** Score = likelihood (1-5) x impact (1-5). Ratings: 15 and above Critical, 10-14 High, 5-9 Medium, below 5 Low.

**Likelihood from evidence.** For risks where I measured failures in at least 5 trials, the observed failure rate is mapped to a band:

| Failure rate | Likelihood |
|---|---|
| under 1% | 1 Rare |
| 1% to under 5% | 2 Unlikely |
| 5% to under 15% | 3 Possible |
| 15% to under 35% | 4 Likely |
| 35% and above | 5 Very likely |

Two values are reported: the **point** value (observed rate) and a **conservative** value (upper end of the 95% Wilson confidence interval). With fewer than 5 trials, a rate is treated as an anecdote and the likelihood is set manually and labeled "anecdotal" or "judgment".

**Impact** is my own judgment on a 1-5 scale, with a one-line rationale per risk.

**Sensitivity test.** The register is re-scored 5,000 times. Impact moves by -1, 0 or +1 at random. Measured likelihoods are drawn from a Beta distribution built from the observed failures and trials. Judgment likelihoods move by -1, 0 or +1. The output is each risk's median rank, 90% rank range and how often it lands in the top 3.

## Framework coverage

OWASP LLM Top 10 categories assessed: LLM01 (R01, R02), LLM02 (R13), LLM03 (R12), LLM08 (R07), LLM09 (R03, R04, R05, R06, R08), LLM10 (R11). R09 and R10 concern a classic ML model, so they are mapped to NIST AI RMF only.

Not assessed as separate risks, with reasons in `data/risks.json`: LLM04 (no model training), LLM05 (output is never executed), LLM06 (the agent cannot execute actions by design). LLM07 (system prompt leakage) overlaps with R01 and was not assessed separately.

## Limitations

- **This is a self-assessment of lab tools, not an enterprise risk assessment.** The systems are small, run locally and handle no real data.
- **Impact scores and all "judgment" likelihoods are my opinion.** The sensitivity test shows how much the ranking depends on that, but it does not remove it.
- **Likelihood means "failure rate when the attack or fault is attempted"**, not the probability that an incident happens. Real likelihood would also need how often attacks occur.
- **The evidence is small and partly synthetic.** Most measured rates come from test sets of 8 to 250 items that I wrote myself, and some fixes were tuned on the same data they were tested on. Several residual numbers are therefore optimistic.
- **Likelihood bands and the plus-or-minus-one perturbation are my choices.** Different thresholds would shift some scores.
- **NIST AI RMF subcategory IDs should be checked against the official Playbook** before this is used in any formal setting.

## How to run

Requires Python 3.10+. No model or internet access is needed.

```bash
python -m venv venv
# Windows: venv\Scripts\activate    Linux/Mac: source venv/bin/activate
pip install -r requirements.txt
python src/01_validate.py
python src/02_score.py
python src/03_sensitivity.py
```

| Script | What it does |
|---|---|
| `src/01_validate.py` | Checks the register for missing fields, bad scales and unknown framework IDs |
| `src/02_score.py` | Scores risks, writes `reports/register_scored.csv` and `reports/heatmap.png` |
| `src/03_sensitivity.py` | Re-scores 5,000 times and writes `reports/sensitivity.json` |
| `src/risk_lib.py` | Shared scoring helpers |

To use it for your own systems, edit `data/risks.json`.

## Related projects

The failure rates used here come from my other repositories: prompt-injection-defense, wazuh-triage-agent, grc-policy-mapper, soc-assistant, adversarial-ids and cic-ids2017-honest-eval (github.com/ajaykumar76).

## References

- OWASP Top 10 for LLM Applications 2025
- NIST AI Risk Management Framework 1.0 (NIST AI 100-1)
