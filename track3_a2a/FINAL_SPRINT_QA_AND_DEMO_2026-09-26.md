# Track 3 final-sprint QA and judge demo

Date: 26 September 2026 (pre-rehearsal QA for the 27–28 September gate). Scope: shadow dashboard only. This file is a reproducible rehearsal checklist, not a new scientific protocol or external-validation result.

## Local QA result

Run against the dashboard branch with RDKit 2025.09.6, the development-only AB Ridge artifact, DeepSeek unconfigured, and autonomous refresh disabled. The browser used an isolated local state/job directory; the project's frozen evidence and external outcomes were not modified.

| Check | Observed result |
| --- | --- |
| Cached run | Three cited PubMed metadata records; two demo molecules; review queue 0; no model promotion. |
| Source links | Source cards link to the recorded PubMed URLs; a searched packet record (`BDB-50318250`) opens its PMC link and displays its XML SHA-256, unresolved fields, and frozen quarantine reasons. |
| Identity | A repeated caffeine SMILES is marked `duplicate_identity`; `not-a-smiles` is marked `invalid_smiles` and cannot enter the queue. |
| Explicit live without key | Run fails visibly with “cached fallback is disabled”; the previous completed result is hidden from the failed run. No cached run is misrepresented as live. |
| Auto failure | Unit tests cover malformed DeepSeek and unreadable Europe PMC responses; both fall back to an explicitly labelled cached demo with queue 0. |
| LLM citation boundary | Unit test confirms an invented source ID is discarded, a foreign citation URL is replaced by the retrieved source URL, and abstract/metadata-only extraction remains quarantined even if the model proposes admission. |
| Scorer provenance | Runtime reports `RDKit: available` and `AB Ridge: development only`; point estimates are labelled exploratory with no validated interval or rank. Artifact/source-hash drift disables scoring in the regression suite. |
| Human audit | A local `quarantine` disposition produced nine hash-linked events, including the named review action. The chain recomputed correctly; queue remained 0. |
| Responsive layout | Browser checks at 390 × 844 and 1440 × 900 found no horizontal overflow in Evidence inbox or Discovery lab. Mobile menu navigation returned to the selected view top. |

Regression command (from this checkout):

```bash
../ECMO-Research-Project/.venv-track3/bin/python -m unittest tests.test_track3_dashboard tests.test_track3_discovery_workflow tests.test_track3_discovery_jobs tests.test_track3_shadow_scorer tests.test_shadow_evidence_sprint -q
```

Expected: **43 tests pass**. The browser QA above was also performed locally; tests alone do not prove the live Render instance has the same code or environment.

## Five-minute deterministic judge demo

1. Open the deployed dashboard and show **Overview**: frozen external cohort **0/60**, zero served models, and shadow-only status. State that the failed external floor bars an external-performance claim.
2. Open **Evidence inbox**. Search `BDB-50318250` under “Records needing review,” expand it, and show the PMC citation, XML hash, missing categorical fields, and frozen quarantine. Do **not** describe this record as admitted or as a measured A2A hit.
3. Open **Discovery lab**. Confirm the capability badges. Select **Deterministic cached demo**; leave the molecule box empty; run. Expect three cached citations, two standardized demo inputs, development-only point estimates when RDKit/Ridge are installed, and **0** screen-eligible records. The empty box causes the two *explicitly simulated* inputs to appear.
4. Expand **Show all workflow gates**. Explain the chain: contracts → literature → extraction → evidence quality → identity → queue → promotion firewall. The LLM organizes evidence; it does not infer potency or override the deterministic gates.
5. For a failure demonstration, select **Live DeepSeek · no fallback** only if the deployed instance is intentionally unconfigured. Expect a failed job, not a silently substituted live result. If a live key is configured, skip this step and explain that any live output remains quarantined and source-bound.
6. Show **Review queue** and **Methods & audit**. The queue is unordered composition only; docking and MD cannot admit or promote a record. Finish on the governance banner, not a molecule-level rank.

Optional input-gate demo: enter `Caffeine A | Cn1c(=O)c2c(ncn2C)n(C)c1=O`, repeat it as `Caffeine duplicate`, and add `Invalid | not-a-smiles` on separate lines. Run in demo mode. The second identity must be duplicate and the invalid string blocked; the queue stays 0. Do not compare the two exploratory point estimates as a certified rank.

## Screenshot freeze checklist for the live rehearsal

Capture these from the **deployed** dashboard after the exact commit is deployed, with the commit SHA and UTC capture time in the submission notes:

1. Overview: 0/60 external floor and zero served models.
2. Evidence inbox: `BDB-50318250` detail expanded with citation, unresolved fields, and quarantine.
3. Discovery lab: capability badges plus the completed cached run and 0-record queue.
4. Discovery lab: expanded workflow gates and the human disposition state.
5. Mobile (390 px width): Discovery lab header/form and Evidence inbox detail, without horizontal clipping.

Local browser screenshots were inspected during QA but are not a substitute for a screenshot freeze of the live deployment. Do not take screenshots with private API keys, login credentials, or external sealed outcomes visible.

## 29 September release rehearsal gate

- Confirm the deployed commit matches the tagged candidate and `/api/discovery/status` reports RDKit available and AB Ridge development-only. If either is unavailable, show the fail-closed state rather than claiming a working scorer.
- Run the deterministic demo; verify the cited sources, the 0 queue, and the promotion lock. Check the Evidence inbox packet search and mobile width.
- If DeepSeek is unavailable or times out, describe the cached fallback as cached; explicit live mode must fail without fallback.
- Cross-check every number spoken to judges against the frozen dashboard artifact. The teammate-PDF aggregate charts remain visibly provisional and separate from the frozen queue.
- Only then capture the live screenshots above, record the commit SHA, and prepare the Sep 30 submission. No new docking/MD production is needed to fill UI gaps.

Known limits: this QA did not call a real DeepSeek service, did not open every external publication page, and did not establish external model validity. The external cohort remains at zero admitted molecules and the one-time outcome join remains prohibited.
