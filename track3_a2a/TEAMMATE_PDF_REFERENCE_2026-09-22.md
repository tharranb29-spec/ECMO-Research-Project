# Teammate dashboard PDF: aggregate reference transcription

Source: `A2A_Track3_Dashboard_Content_Specification (1).pdf`, 13 pages, supplied by the team on 2026-09-22. SHA-256 of the reviewed PDF copy: `5308b8041c28657c9234b9a5a0f8b50b886ebe6146affa0b877a21f73fb9145f`.

This file records aggregate values for a separate, explicitly provisional dashboard view. The source PDF is not bundled or published. The underlying molecule records, model artifact, calculations, graph data, and claimed 954 verification assertions were not supplied and have not been independently reproduced. The PDF is not an external-validation result. None of these numbers enter the frozen dashboard contracts, live review queue, discovery workflow, model, or promotion logic.

| PDF page | Reported aggregate | Dashboard use |
| --- | --- | --- |
| 5 | Library 2,963; inside applicability domain 423; antagonist class 335 (149 scaffolds); screen-eligible 276 (120 scaffolds) | Separate screening-funnel graphic, marked provisional |
| 5 | Calibrated 90% interval half-width 1.2588; upper bound reaches pKi 8.0 when prediction is at least 6.7412 | Explain *non-exclusion*, never call a predicted hit |
| 7 | 2,770 / 55,945 pairs separable (4.95%); largest adjacent prediction gap 0.3230 versus required 2.5176 pKi | Explain why the set has no defensible ordinal positions |
| 7 | Separate 74-molecule development set: separability 4.2% at calibrated intervals; fourfold narrowing raises separability to 56.8% but lowers coverage from 0.8919 to 0.3649 | Interactive stress-test comparison, deliberately not merged with the 335-candidate pool |
| 9 | N=10 precision 0.9600, base 0.4808, EF 1.997; N=20 0.7950/0.4808/1.654; N=40 0.6200/0.4808/1.290 | Label as development resampling on a reference population, not prospective yield |
| 10 | Published potency values stripped for 155 of 276 delivered compounds; 310 values across 65 unique documents | PDF-only literature-coverage graphic; no records imported or outcomes unsealed |
| 12 | Strict Ki-only R² 0.5685 vs pooled 0.4768; PDF domain floor 0.50 vs plan 0.55; interval half-width 1.2588 vs plan 1.299 | Show unresolved D1/D2 and interval reconciliation |

The PDF's 276/120 set and the project's audited 240-held/0-eligible review queue are different evidence streams. The project's frozen model comparison has 78 development molecules and 2,048-bit fingerprints, whereas the PDF describes 74 development molecules and 1,024-bit fingerprints for its strict Ki-only branch. Their numbers must not be silently combined. The PDF's precision figures exclude the 276 delivered compounds and do not establish a per-molecule hit probability, a prospective hit rate, or external confirmation.

To promote any PDF-reported value beyond an attributed exploratory reference, obtain the candidate-level IDs/structures/scaffolds, source citations, endpoint and split manifests, frozen model/preprocessing/calibration artifacts, exact threshold decision, reproducible calculation scripts, and verification outputs. Then independently rerun and reconcile before changing the governed queue or scientific claims.
