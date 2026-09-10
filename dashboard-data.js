window.ECMO_DASHBOARD_DATA = {
  "config": {
    "institution_name": "Zhejiang University International School of Medicine",
    "program_name": "AI-Driven ECMO Interface Research Project",
    "english_title": "AI-Driven Discovery of High-Affinity Ligands for Developing Bio-inspired ECMO Interfaces Capable of Immune Phenotypic Reprogramming",
    "chinese_title": "\u4eba\u5de5\u667a\u80fd\u9a71\u52a8\u7684\u9ad8\u4eb2\u548c\u529b\u914d\u4f53\u7b5b\u9009\u53ca\u5176\u4ecb\u5bfc\u7684ECMO\u4eff\u751f\u754c\u9762\u514d\u75ab\u91cd\u5851\u7814\u7a76",
    "short_title": "ECMO Ligand Ranking Dashboard",
    "branding_note": "Internal project dashboard for group review, candidate triage, and discussion support.",
    "logo_path": "assets/zju-ism-mark.svg"
  },
  "seed": {
    "models": {
      "SIRPa": {
        "target": "SIRPa",
        "weights": {
          "affinity_strength_score": 0.254708824320116,
          "specificity_score": 0.13269691413328458,
          "functional_immunomodulation_score": 0.23022402110011048,
          "surface_validation_score": 0.21753723624916155,
          "conjugation_feasibility_score": 0.08463987031559307,
          "hemocompatibility_proxy_score": 0.12864026167921436,
          "multivalency_or_clustering_score": 0.06428910706740609,
          "literature_confidence_score": 0.03217814748238371
        },
        "bias": -0.13953793572110645
      },
      "Siglec-9": {
        "target": "Siglec-9",
        "weights": {
          "affinity_strength_score": 0.26616100464879733,
          "specificity_score": 0.15030057723321946,
          "functional_immunomodulation_score": 0.2677794043498648,
          "surface_validation_score": 0.13860946260794435,
          "conjugation_feasibility_score": 0.09769491421795652,
          "hemocompatibility_proxy_score": 0.0870282695253188,
          "multivalency_or_clustering_score": 0.0889993512669093,
          "literature_confidence_score": 0.03494726250474451
        },
        "bias": -0.0393956478312162
      }
    },
    "metrics": {
      "SIRPa": 4.480099706564318,
      "Siglec-9": 8.364828687179712
    },
    "ranked": [
      {
        "id": "sirpa_cd47_wt",
        "candidate_name": "CD47 ectodomain WT",
        "target_receptor": "SIRPa",
        "modality": "protein",
        "predicted_score": 86.3,
        "recommendation": "advance",
        "explanation": "strong immunomodulation evidence, strong affinity evidence, surface-translation support.",
        "evidence_summary": "Strong mechanistic and biomaterial evidence: immobilized CD47 reduces inflammatory cell attachment and neutrophil activation on polymeric blood-contacting surfaces.",
        "source_urls": [
          "https://pmc.ncbi.nlm.nih.gov/articles/PMC4432284/",
          "https://pmc.ncbi.nlm.nih.gov/articles/PMC3108143/",
          "https://pmc.ncbi.nlm.nih.gov/articles/PMC4950361/"
        ]
      },
      {
        "id": "sirpa_self_21aa",
        "candidate_name": "Self peptide 21 aa",
        "target_receptor": "SIRPa",
        "modality": "peptide",
        "predicted_score": 82.2,
        "recommendation": "advance",
        "explanation": "strong immunomodulation evidence, strong affinity evidence, surface-translation support.",
        "evidence_summary": "Compact CD47-derived peptide with strong nanoparticle persistence and macrophage-avoidance evidence, making it attractive for engineered surfaces.",
        "source_urls": [
          "https://pmc.ncbi.nlm.nih.gov/articles/PMC3966479/"
        ]
      },
      {
        "id": "sirpa_cd47_n3612",
        "candidate_name": "CD47 variant N3612",
        "target_receptor": "SIRPa",
        "modality": "engineered_protein",
        "predicted_score": 76.1,
        "recommendation": "secondary",
        "explanation": "strong affinity evidence, strong immunomodulation evidence, surface-translation support.",
        "evidence_summary": "Very high-affinity engineered CD47 variant with clear binding gains, but much less direct biomaterial-surface validation than WT CD47.",
        "source_urls": [
          "https://pmc.ncbi.nlm.nih.gov/articles/PMC4432284/"
        ]
      },
      {
        "id": "sirpa_self_hairpin_10aa",
        "candidate_name": "Self hairpin 10 aa",
        "target_receptor": "SIRPa",
        "modality": "peptide",
        "predicted_score": 53.9,
        "recommendation": "hold",
        "explanation": "surface-translation support, strong affinity evidence, strong immunomodulation evidence.",
        "evidence_summary": "Smaller derivative around the active loop that retains some activity but is clearly weaker than the full Self peptide.",
        "source_urls": [
          "https://pmc.ncbi.nlm.nih.gov/articles/PMC3966479/"
        ]
      },
      {
        "id": "sirpa_self_ss_t107c",
        "candidate_name": "Self-SS T107C",
        "target_receptor": "SIRPa",
        "modality": "peptide_control",
        "predicted_score": 14.3,
        "recommendation": "reject",
        "explanation": "good hemocompatibility proxy, good conjugation feasibility, surface-translation support.",
        "evidence_summary": "Negative control variant showing loss of SIRPa binding and loss of useful inhibitory signaling.",
        "source_urls": [
          "https://pmc.ncbi.nlm.nih.gov/articles/PMC3966479/"
        ]
      },
      {
        "id": "sirpa_scrambled_self",
        "candidate_name": "Scrambled Self peptide",
        "target_receptor": "SIRPa",
        "modality": "peptide_control",
        "predicted_score": 11.1,
        "recommendation": "reject",
        "explanation": "good hemocompatibility proxy, good conjugation feasibility, surface-translation support.",
        "evidence_summary": "Scrambled negative control demonstrating the need for sequence-specific SIRPa engagement.",
        "source_urls": [
          "https://pmc.ncbi.nlm.nih.gov/articles/PMC3966479/"
        ]
      },
      {
        "id": "siglec9_ps9l",
        "candidate_name": "pS9L",
        "target_receptor": "Siglec-9",
        "modality": "glycopolypeptide",
        "predicted_score": 89.5,
        "recommendation": "advance",
        "explanation": "strong immunomodulation evidence, strong affinity evidence, good target specificity.",
        "evidence_summary": "Potent multivalent Siglec-9 agonist with strong functional evidence for suppressing NETosis via SHP-1-dependent signaling.",
        "source_urls": [
          "https://pmc.ncbi.nlm.nih.gov/articles/PMC8009098/"
        ]
      },
      {
        "id": "siglec9_mtts_neu5ac",
        "candidate_name": "MTTSNeu5Ac",
        "target_receptor": "Siglec-9",
        "modality": "glycomimetic",
        "predicted_score": 67.0,
        "recommendation": "secondary",
        "explanation": "strong affinity evidence, good target specificity, strong immunomodulation evidence.",
        "evidence_summary": "Best affinity among the monovalent Siglec-9 glycomimetics curated here, though still missing direct ECMO-surface validation.",
        "source_urls": [
          "https://pmc.ncbi.nlm.nih.gov/articles/PMC10877568/"
        ]
      },
      {
        "id": "siglec9_btc_neu5ac",
        "candidate_name": "BTCNeu5Ac",
        "target_receptor": "Siglec-9",
        "modality": "glycomimetic",
        "predicted_score": 62.6,
        "recommendation": "hold",
        "explanation": "strong affinity evidence, good target specificity, strong immunomodulation evidence.",
        "evidence_summary": "Synthetic Siglec-9 glycomimetic with clearly improved affinity over natural glycans and good receptor-binding evidence.",
        "source_urls": [
          "https://pmc.ncbi.nlm.nih.gov/articles/PMC10877568/"
        ]
      },
      {
        "id": "siglec9_6osulfo_slex",
        "candidate_name": "6-O-sulfo sLeX",
        "target_receptor": "Siglec-9",
        "modality": "glycan",
        "predicted_score": 52.4,
        "recommendation": "hold",
        "explanation": "strong affinity evidence, good target specificity, good conjugation feasibility.",
        "evidence_summary": "Improved natural glycan ligand for Siglec-9 with better affinity than sLeX but still limited direct functional remodeling evidence.",
        "source_urls": [
          "https://pmc.ncbi.nlm.nih.gov/articles/PMC10877568/"
        ]
      },
      {
        "id": "siglec9_ps9l_sol",
        "candidate_name": "pS9L-sol",
        "target_receptor": "Siglec-9",
        "modality": "glycopolypeptide",
        "predicted_score": 46.6,
        "recommendation": "reject",
        "explanation": "strong affinity evidence, good target specificity, good hemocompatibility proxy.",
        "evidence_summary": "Useful negative control showing that soluble presentation without cis-clustering is not sufficient for strong Siglec-9 agonism.",
        "source_urls": [
          "https://pmc.ncbi.nlm.nih.gov/articles/PMC8009098/"
        ]
      },
      {
        "id": "siglec9_slex",
        "candidate_name": "sLeX",
        "target_receptor": "Siglec-9",
        "modality": "glycan",
        "predicted_score": 43.2,
        "recommendation": "reject",
        "explanation": "good target specificity, good conjugation feasibility, strong affinity evidence.",
        "evidence_summary": "Natural Siglec-9 ligand with weak-to-moderate affinity and limited direct functional ECMO-surface evidence.",
        "source_urls": [
          "https://pmc.ncbi.nlm.nih.gov/articles/PMC10877568/"
        ]
      },
      {
        "id": "siglec9_plac",
        "candidate_name": "pLac",
        "target_receptor": "Siglec-9",
        "modality": "glycopolypeptide_control",
        "predicted_score": 16.7,
        "recommendation": "reject",
        "explanation": "good conjugation feasibility, good hemocompatibility proxy.",
        "evidence_summary": "Deliberate non-binding negative control for the Siglec-9 glycopolypeptide system.",
        "source_urls": [
          "https://pmc.ncbi.nlm.nih.gov/articles/PMC8009098/"
        ]
      }
    ]
  },
  "custom": {
    "models": {
      "SIRPa": {
        "target": "SIRPa",
        "weights": {
          "affinity_strength_score": 0.254708824320116,
          "specificity_score": 0.13269691413328458,
          "functional_immunomodulation_score": 0.23022402110011048,
          "surface_validation_score": 0.21753723624916155,
          "conjugation_feasibility_score": 0.08463987031559307,
          "hemocompatibility_proxy_score": 0.12864026167921436,
          "multivalency_or_clustering_score": 0.06428910706740609,
          "literature_confidence_score": 0.03217814748238371
        },
        "bias": -0.13953793572110645
      },
      "Siglec-9": {
        "target": "Siglec-9",
        "weights": {
          "affinity_strength_score": 0.26616100464879733,
          "specificity_score": 0.15030057723321946,
          "functional_immunomodulation_score": 0.2677794043498648,
          "surface_validation_score": 0.13860946260794435,
          "conjugation_feasibility_score": 0.09769491421795652,
          "hemocompatibility_proxy_score": 0.0870282695253188,
          "multivalency_or_clustering_score": 0.0889993512669093,
          "literature_confidence_score": 0.03494726250474451
        },
        "bias": -0.0393956478312162
      }
    },
    "metrics": {
      "SIRPa": 4.480099706564318,
      "Siglec-9": 8.364828687179712
    },
    "ranked": [
      {
        "id": "your_sirpa_candidate",
        "candidate_name": "Your SIRPa Candidate",
        "target_receptor": "SIRPa",
        "modality": "peptide",
        "predicted_score": 73.9,
        "recommendation": "secondary",
        "explanation": "strong affinity evidence, strong immunomodulation evidence, surface-translation support.",
        "evidence_summary": "Example row you can overwrite with your own candidate",
        "source_urls": []
      },
      {
        "id": "your_siglec-9_candidate",
        "candidate_name": "Your Siglec-9 Candidate",
        "target_receptor": "Siglec-9",
        "modality": "glycomimetic",
        "predicted_score": 66.9,
        "recommendation": "secondary",
        "explanation": "strong affinity evidence, good target specificity, strong immunomodulation evidence.",
        "evidence_summary": "Example row you can overwrite with your own candidate",
        "source_urls": []
      }
    ]
  },
  "autonomous": {
    "models": {
      "SIRPa": {
        "target": "SIRPa",
        "weights": {
          "affinity_strength_score": 0.254708824320116,
          "specificity_score": 0.13269691413328458,
          "functional_immunomodulation_score": 0.23022402110011048,
          "surface_validation_score": 0.21753723624916155,
          "conjugation_feasibility_score": 0.08463987031559307,
          "hemocompatibility_proxy_score": 0.12864026167921436,
          "multivalency_or_clustering_score": 0.06428910706740609,
          "literature_confidence_score": 0.03217814748238371
        },
        "bias": -0.13953793572110645
      },
      "Siglec-9": {
        "target": "Siglec-9",
        "weights": {
          "affinity_strength_score": 0.26616100464879733,
          "specificity_score": 0.15030057723321946,
          "functional_immunomodulation_score": 0.2677794043498648,
          "surface_validation_score": 0.13860946260794435,
          "conjugation_feasibility_score": 0.09769491421795652,
          "hemocompatibility_proxy_score": 0.0870282695253188,
          "multivalency_or_clustering_score": 0.0889993512669093,
          "literature_confidence_score": 0.03494726250474451
        },
        "bias": -0.0393956478312162
      }
    },
    "metrics": {
      "SIRPa": 4.480099706564318,
      "Siglec-9": 8.364828687179712
    },
    "ranked": [
      {
        "id": "auto_pd1_sirpa",
        "candidate_name": "PD1",
        "target_receptor": "SIRPa",
        "modality": "literature_lead",
        "predicted_score": 41.7,
        "recommendation": "reject",
        "explanation": "strong affinity evidence, strong immunomodulation evidence, good target specificity.",
        "evidence_summary": "Recent literature mention in article: Unveiling the immune microenvironment in sinonasal intestinal type adenocarcinoma: new arguments for immunotherapy. (new literature lead, heuristic extraction)",
        "source_urls": [
          "https://europepmc.org/article/MED/42689729"
        ],
        "translational_suitability_score": 41.7,
        "gnina": {
          "candidate_id": "auto_pd1_sirpa",
          "candidate_name": "PD1",
          "target_receptor": "SIRPa",
          "modality": "literature_lead",
          "dockability": "prototype_eligible",
          "dockability_reason": "Eligible for a visibly simulated end-to-end workflow demonstration.",
          "source_batch": "42689729",
          "execution_mode": "prototype",
          "simulated": true,
          "run_count": 5,
          "minimized_affinity_mean_kcal_mol": -8.376,
          "minimized_affinity_sd_kcal_mol": 0.132,
          "cnn_score_mean": 0.5109,
          "cnn_score_sd": 0.0231,
          "cnn_affinity_mean_pk": 6.587,
          "cnn_affinity_sd_pk": 0.06,
          "pose_quality_status": "pass",
          "pose_quality_threshold": 0.5,
          "runs": [
            {
              "seed": 42,
              "minimized_affinity_kcal_mol": -8.501,
              "cnn_score": 0.5279,
              "cnn_affinity_pk": 6.597,
              "pose_path": null,
              "execution_mode": "prototype",
              "simulated": true
            },
            {
              "seed": 43,
              "minimized_affinity_kcal_mol": -8.539,
              "cnn_score": 0.5024,
              "cnn_affinity_pk": 6.565,
              "pose_path": null,
              "execution_mode": "prototype",
              "simulated": true
            },
            {
              "seed": 44,
              "minimized_affinity_kcal_mol": -8.285,
              "cnn_score": 0.54,
              "cnn_affinity_pk": 6.603,
              "pose_path": null,
              "execution_mode": "prototype",
              "simulated": true
            },
            {
              "seed": 45,
              "minimized_affinity_kcal_mol": -8.27,
              "cnn_score": 0.5023,
              "cnn_affinity_pk": 6.668,
              "pose_path": null,
              "execution_mode": "prototype",
              "simulated": true
            },
            {
              "seed": 46,
              "minimized_affinity_kcal_mol": -8.286,
              "cnn_score": 0.4817,
              "cnn_affinity_pk": 6.504,
              "pose_path": null,
              "execution_mode": "prototype",
              "simulated": true
            }
          ],
          "functional_direction": "unknown",
          "structure_status": "awaiting_verified_structure",
          "structure_provenance": null,
          "structure_source_url": null,
          "structure_sha256": null,
          "candidate_role": null,
          "status": "completed",
          "comparative_affinity_rank": 1,
          "gnina_rank": 1,
          "uncertainty_group": 1,
          "tied_with_previous": false
        },
        "gnina_rank": 1,
        "ranking_basis": "gnina_b2_prototype",
        "lead_score": 60,
        "discovery_status": "new_literature_lead",
        "publication_date": "2026-09-03",
        "source_title": "Unveiling the immune microenvironment in sinonasal intestinal type adenocarcinoma: new arguments for immunotherapy.",
        "source_method": "heuristic",
        "is_new": false
      },
      {
        "id": "auto_plac_sirpa",
        "candidate_name": "pLac",
        "target_receptor": "SIRPa",
        "modality": "glycopolypeptide_control",
        "predicted_score": 37.7,
        "recommendation": "reject",
        "explanation": "strong affinity evidence, strong immunomodulation evidence, good target specificity.",
        "evidence_summary": "Recent literature mention in article: Pretransfusion testing interference profile of IMC-002: A novel anti-CD47 monoclonal antibody engineered for minimized red cell binding. (known reference, heuristic extraction)",
        "source_urls": [
          "https://europepmc.org/article/MED/42671022"
        ],
        "translational_suitability_score": 37.7,
        "gnina": {
          "candidate_id": "auto_plac_sirpa",
          "candidate_name": "pLac",
          "target_receptor": "SIRPa",
          "modality": "glycopolypeptide_control",
          "dockability": "unsupported_modality",
          "dockability_reason": "glycopolypeptide_control requires peptide or protein docking rather than GNINA.",
          "status": "unsupported_modality",
          "simulated": false
        },
        "gnina_rank": null,
        "ranking_basis": "gnina_not_scored",
        "lead_score": 55,
        "discovery_status": "known_reference",
        "publication_date": "2026-08-31",
        "source_title": "Pretransfusion testing interference profile of IMC-002: A novel anti-CD47 monoclonal antibody engineered for minimized red cell binding.",
        "source_method": "heuristic",
        "is_new": false
      },
      {
        "id": "auto_neu5ac_siglec9",
        "candidate_name": "Neu5Ac",
        "target_receptor": "Siglec-9",
        "modality": "sialoside",
        "predicted_score": 49.8,
        "recommendation": "reject",
        "explanation": "strong affinity evidence, strong immunomodulation evidence, good target specificity.",
        "evidence_summary": "Recent literature mention in article: Defined O-acetylated Neu5Ac substrates reveal position-specific preferences of gut bacterial sialidases. (new literature lead, heuristic extraction)",
        "source_urls": [
          "https://europepmc.org/article/MED/42708333"
        ],
        "translational_suitability_score": 49.8,
        "gnina": {
          "candidate_id": "auto_neu5ac_siglec9",
          "candidate_name": "Neu5Ac",
          "target_receptor": "Siglec-9",
          "modality": "sialoside",
          "dockability": "prototype_eligible",
          "dockability_reason": "Eligible for a visibly simulated end-to-end workflow demonstration.",
          "source_batch": "42708333",
          "execution_mode": "prototype",
          "simulated": true,
          "run_count": 5,
          "minimized_affinity_mean_kcal_mol": -5.986,
          "minimized_affinity_sd_kcal_mol": 0.117,
          "cnn_score_mean": 0.5126,
          "cnn_score_sd": 0.0243,
          "cnn_affinity_mean_pk": 4.9,
          "cnn_affinity_sd_pk": 0.06,
          "pose_quality_status": "pass",
          "pose_quality_threshold": 0.5,
          "runs": [
            {
              "seed": 42,
              "minimized_affinity_kcal_mol": -5.863,
              "cnn_score": 0.5208,
              "cnn_affinity_pk": 4.942,
              "pose_path": null,
              "execution_mode": "prototype",
              "simulated": true
            },
            {
              "seed": 43,
              "minimized_affinity_kcal_mol": -6.162,
              "cnn_score": 0.4876,
              "cnn_affinity_pk": 4.959,
              "pose_path": null,
              "execution_mode": "prototype",
              "simulated": true
            },
            {
              "seed": 44,
              "minimized_affinity_kcal_mol": -6.034,
              "cnn_score": 0.534,
              "cnn_affinity_pk": 4.808,
              "pose_path": null,
              "execution_mode": "prototype",
              "simulated": true
            },
            {
              "seed": 45,
              "minimized_affinity_kcal_mol": -5.915,
              "cnn_score": 0.4858,
              "cnn_affinity_pk": 4.915,
              "pose_path": null,
              "execution_mode": "prototype",
              "simulated": true
            },
            {
              "seed": 46,
              "minimized_affinity_kcal_mol": -5.957,
              "cnn_score": 0.5349,
              "cnn_affinity_pk": 4.874,
              "pose_path": null,
              "execution_mode": "prototype",
              "simulated": true
            }
          ],
          "functional_direction": "unknown",
          "structure_status": "verified_experimental_coordinates",
          "structure_provenance": "RCSB CCD SIA ideal coordinates",
          "structure_source_url": "https://www.rcsb.org/ligand/SIA",
          "structure_sha256": "24c952771a239f5ff652dd4b962efb1f0b7f011fcc1a73c8ac6fdd431ff25773",
          "candidate_role": "minimal_sialic_acid_control",
          "status": "completed",
          "comparative_affinity_rank": 1,
          "gnina_rank": 1,
          "uncertainty_group": 1,
          "tied_with_previous": false
        },
        "gnina_rank": 1,
        "ranking_basis": "gnina_b2_prototype",
        "lead_score": 60,
        "discovery_status": "new_literature_lead",
        "publication_date": "2026-09-08",
        "source_title": "Defined O-acetylated Neu5Ac substrates reveal position-specific preferences of gut bacterial sialidases.",
        "source_method": "heuristic",
        "is_new": true
      },
      {
        "id": "auto_delta_siglec9",
        "candidate_name": "Delta",
        "target_receptor": "Siglec-9",
        "modality": "protein",
        "predicted_score": 54.9,
        "recommendation": "hold",
        "explanation": "strong affinity evidence, strong immunomodulation evidence, good target specificity.",
        "evidence_summary": "Recent literature mention in article: SARS-CoV-2 nucleocapsid induces hyperinflammation and vascular leakage through the Toll-like receptor signaling axis in macrophages. (new literature lead, heuristic extraction)",
        "source_urls": [
          "https://europepmc.org/article/MED/42555728"
        ],
        "translational_suitability_score": 54.9,
        "gnina": {
          "candidate_id": "auto_delta_siglec9",
          "candidate_name": "Delta",
          "target_receptor": "Siglec-9",
          "modality": "protein",
          "dockability": "unsupported_modality",
          "dockability_reason": "protein requires peptide or protein docking rather than GNINA.",
          "status": "unsupported_modality",
          "simulated": false
        },
        "gnina_rank": null,
        "ranking_basis": "gnina_not_scored",
        "lead_score": 67,
        "discovery_status": "new_literature_lead",
        "publication_date": "2026-08-05",
        "source_title": "SARS-CoV-2 nucleocapsid induces hyperinflammation and vascular leakage through the Toll-like receptor signaling axis in macrophages.",
        "source_method": "heuristic",
        "is_new": true
      },
      {
        "id": "auto_n-expressing_siglec9",
        "candidate_name": "N-expressing",
        "target_receptor": "Siglec-9",
        "modality": "protein",
        "predicted_score": 54.9,
        "recommendation": "hold",
        "explanation": "strong affinity evidence, strong immunomodulation evidence, good target specificity.",
        "evidence_summary": "Recent literature mention in article: SARS-CoV-2 nucleocapsid induces hyperinflammation and vascular leakage through the Toll-like receptor signaling axis in macrophages. (new literature lead, heuristic extraction)",
        "source_urls": [
          "https://europepmc.org/article/MED/42555728"
        ],
        "translational_suitability_score": 54.9,
        "gnina": {
          "candidate_id": "auto_n-expressing_siglec9",
          "candidate_name": "N-expressing",
          "target_receptor": "Siglec-9",
          "modality": "protein",
          "dockability": "unsupported_modality",
          "dockability_reason": "protein requires peptide or protein docking rather than GNINA.",
          "status": "unsupported_modality",
          "simulated": false
        },
        "gnina_rank": null,
        "ranking_basis": "gnina_not_scored",
        "lead_score": 67,
        "discovery_status": "new_literature_lead",
        "publication_date": "2026-08-05",
        "source_title": "SARS-CoV-2 nucleocapsid induces hyperinflammation and vascular leakage through the Toll-like receptor signaling axis in macrophages.",
        "source_method": "heuristic",
        "is_new": true
      },
      {
        "id": "auto_sars-cov-2_siglec9",
        "candidate_name": "SARS-CoV-2",
        "target_receptor": "Siglec-9",
        "modality": "protein",
        "predicted_score": 54.9,
        "recommendation": "hold",
        "explanation": "strong affinity evidence, strong immunomodulation evidence, good target specificity.",
        "evidence_summary": "Recent literature mention in article: SARS-CoV-2 nucleocapsid induces hyperinflammation and vascular leakage through the Toll-like receptor signaling axis in macrophages. (new literature lead, heuristic extraction)",
        "source_urls": [
          "https://europepmc.org/article/MED/42555728"
        ],
        "translational_suitability_score": 54.9,
        "gnina": {
          "candidate_id": "auto_sars-cov-2_siglec9",
          "candidate_name": "SARS-CoV-2",
          "target_receptor": "Siglec-9",
          "modality": "protein",
          "dockability": "unsupported_modality",
          "dockability_reason": "protein requires peptide or protein docking rather than GNINA.",
          "status": "unsupported_modality",
          "simulated": false
        },
        "gnina_rank": null,
        "ranking_basis": "gnina_not_scored",
        "lead_score": 67,
        "discovery_status": "new_literature_lead",
        "publication_date": "2026-08-05",
        "source_title": "SARS-CoV-2 nucleocapsid induces hyperinflammation and vascular leakage through the Toll-like receptor signaling axis in macrophages.",
        "source_method": "heuristic",
        "is_new": true
      },
      {
        "id": "auto_plac_siglec9",
        "candidate_name": "pLac",
        "target_receptor": "Siglec-9",
        "modality": "glycopolypeptide_control",
        "predicted_score": 52.5,
        "recommendation": "hold",
        "explanation": "strong affinity evidence, strong immunomodulation evidence, good target specificity.",
        "evidence_summary": "Recent literature mention in article: Molecular innate immune programs of tumor-associated macrophages in immune checkpoint blockade resistance: a staged framework from suppressive circuitry to translational bottlenecks. (known reference, heuristic extraction)",
        "source_urls": [
          "https://europepmc.org/article/MED/42626172"
        ],
        "translational_suitability_score": 52.5,
        "gnina": {
          "candidate_id": "auto_plac_siglec9",
          "candidate_name": "pLac",
          "target_receptor": "Siglec-9",
          "modality": "glycopolypeptide_control",
          "dockability": "unsupported_modality",
          "dockability_reason": "glycopolypeptide_control requires peptide or protein docking rather than GNINA.",
          "status": "unsupported_modality",
          "simulated": false
        },
        "gnina_rank": null,
        "ranking_basis": "gnina_not_scored",
        "lead_score": 60,
        "discovery_status": "known_reference",
        "publication_date": "2026-08-06",
        "source_title": "Molecular innate immune programs of tumor-associated macrophages in immune checkpoint blockade resistance: a staged framework from suppressive circuitry to translational bottlenecks.",
        "source_method": "heuristic",
        "is_new": false
      }
    ],
    "docking_summary": {
      "last_updated": "2026-09-10T17:13:04.909223+00:00",
      "mode": "prototype",
      "simulated": true,
      "completed_count": 2,
      "candidate_count": 7,
      "protocol": {
        "gnina_version": "1.3.x",
        "run_count": 5,
        "seed_start": 42,
        "num_modes": 1,
        "cnn_scoring": "rescore",
        "cnn_score_min": 0.5,
        "tie_z": 1.96,
        "exhaustiveness": 8,
        "ranking_rule": "pose-quality gate, then mean minimized affinity; CNNscore breaks unresolved ties"
      }
    }
  },
  "autonomous_promoted": {
    "last_updated": "2026-09-10T17:13:04.910201+00:00",
    "criteria": {
      "min_score": 65.0,
      "recommendation_tiers": [
        "advance",
        "secondary"
      ],
      "max_candidates": 4,
      "max_per_target": 2,
      "exclude_seed_references": true,
      "allow_known_reference_as_labeled_gnina_benchmark": true,
      "gnina_pose_gate_when_available": true
    },
    "ranked": [
      {
        "id": "auto_pd1_sirpa",
        "candidate_name": "PD1",
        "target_receptor": "SIRPa",
        "modality": "literature_lead",
        "predicted_score": 41.7,
        "recommendation": "reject",
        "explanation": "strong affinity evidence, strong immunomodulation evidence, good target specificity.",
        "evidence_summary": "Recent literature mention in article: Unveiling the immune microenvironment in sinonasal intestinal type adenocarcinoma: new arguments for immunotherapy. (new literature lead, heuristic extraction)",
        "source_urls": [
          "https://europepmc.org/article/MED/42689729"
        ],
        "translational_suitability_score": 41.7,
        "gnina": {
          "candidate_id": "auto_pd1_sirpa",
          "candidate_name": "PD1",
          "target_receptor": "SIRPa",
          "modality": "literature_lead",
          "dockability": "prototype_eligible",
          "dockability_reason": "Eligible for a visibly simulated end-to-end workflow demonstration.",
          "source_batch": "42689729",
          "execution_mode": "prototype",
          "simulated": true,
          "run_count": 5,
          "minimized_affinity_mean_kcal_mol": -8.376,
          "minimized_affinity_sd_kcal_mol": 0.132,
          "cnn_score_mean": 0.5109,
          "cnn_score_sd": 0.0231,
          "cnn_affinity_mean_pk": 6.587,
          "cnn_affinity_sd_pk": 0.06,
          "pose_quality_status": "pass",
          "pose_quality_threshold": 0.5,
          "runs": [
            {
              "seed": 42,
              "minimized_affinity_kcal_mol": -8.501,
              "cnn_score": 0.5279,
              "cnn_affinity_pk": 6.597,
              "pose_path": null,
              "execution_mode": "prototype",
              "simulated": true
            },
            {
              "seed": 43,
              "minimized_affinity_kcal_mol": -8.539,
              "cnn_score": 0.5024,
              "cnn_affinity_pk": 6.565,
              "pose_path": null,
              "execution_mode": "prototype",
              "simulated": true
            },
            {
              "seed": 44,
              "minimized_affinity_kcal_mol": -8.285,
              "cnn_score": 0.54,
              "cnn_affinity_pk": 6.603,
              "pose_path": null,
              "execution_mode": "prototype",
              "simulated": true
            },
            {
              "seed": 45,
              "minimized_affinity_kcal_mol": -8.27,
              "cnn_score": 0.5023,
              "cnn_affinity_pk": 6.668,
              "pose_path": null,
              "execution_mode": "prototype",
              "simulated": true
            },
            {
              "seed": 46,
              "minimized_affinity_kcal_mol": -8.286,
              "cnn_score": 0.4817,
              "cnn_affinity_pk": 6.504,
              "pose_path": null,
              "execution_mode": "prototype",
              "simulated": true
            }
          ],
          "functional_direction": "unknown",
          "structure_status": "awaiting_verified_structure",
          "structure_provenance": null,
          "structure_source_url": null,
          "structure_sha256": null,
          "candidate_role": null,
          "status": "completed",
          "comparative_affinity_rank": 1,
          "gnina_rank": 1,
          "uncertainty_group": 1,
          "tied_with_previous": false
        },
        "gnina_rank": 1,
        "ranking_basis": "gnina_b2_prototype",
        "promoted_to_main_view": true,
        "promotion_source": "autonomous_discovery_with_gnina",
        "promotion_reason": "Autonomous literature discovery surfaced this candidate, the translational suitability model passed it for review, and the GNINA pose-quality gate passed in the current prototype workflow.",
        "promotion_rank": 1
      },
      {
        "id": "auto_neu5ac_siglec9",
        "candidate_name": "Neu5Ac",
        "target_receptor": "Siglec-9",
        "modality": "sialoside",
        "predicted_score": 49.8,
        "recommendation": "reject",
        "explanation": "strong affinity evidence, strong immunomodulation evidence, good target specificity.",
        "evidence_summary": "Recent literature mention in article: Defined O-acetylated Neu5Ac substrates reveal position-specific preferences of gut bacterial sialidases. (new literature lead, heuristic extraction)",
        "source_urls": [
          "https://europepmc.org/article/MED/42708333"
        ],
        "translational_suitability_score": 49.8,
        "gnina": {
          "candidate_id": "auto_neu5ac_siglec9",
          "candidate_name": "Neu5Ac",
          "target_receptor": "Siglec-9",
          "modality": "sialoside",
          "dockability": "prototype_eligible",
          "dockability_reason": "Eligible for a visibly simulated end-to-end workflow demonstration.",
          "source_batch": "42708333",
          "execution_mode": "prototype",
          "simulated": true,
          "run_count": 5,
          "minimized_affinity_mean_kcal_mol": -5.986,
          "minimized_affinity_sd_kcal_mol": 0.117,
          "cnn_score_mean": 0.5126,
          "cnn_score_sd": 0.0243,
          "cnn_affinity_mean_pk": 4.9,
          "cnn_affinity_sd_pk": 0.06,
          "pose_quality_status": "pass",
          "pose_quality_threshold": 0.5,
          "runs": [
            {
              "seed": 42,
              "minimized_affinity_kcal_mol": -5.863,
              "cnn_score": 0.5208,
              "cnn_affinity_pk": 4.942,
              "pose_path": null,
              "execution_mode": "prototype",
              "simulated": true
            },
            {
              "seed": 43,
              "minimized_affinity_kcal_mol": -6.162,
              "cnn_score": 0.4876,
              "cnn_affinity_pk": 4.959,
              "pose_path": null,
              "execution_mode": "prototype",
              "simulated": true
            },
            {
              "seed": 44,
              "minimized_affinity_kcal_mol": -6.034,
              "cnn_score": 0.534,
              "cnn_affinity_pk": 4.808,
              "pose_path": null,
              "execution_mode": "prototype",
              "simulated": true
            },
            {
              "seed": 45,
              "minimized_affinity_kcal_mol": -5.915,
              "cnn_score": 0.4858,
              "cnn_affinity_pk": 4.915,
              "pose_path": null,
              "execution_mode": "prototype",
              "simulated": true
            },
            {
              "seed": 46,
              "minimized_affinity_kcal_mol": -5.957,
              "cnn_score": 0.5349,
              "cnn_affinity_pk": 4.874,
              "pose_path": null,
              "execution_mode": "prototype",
              "simulated": true
            }
          ],
          "functional_direction": "unknown",
          "structure_status": "verified_experimental_coordinates",
          "structure_provenance": "RCSB CCD SIA ideal coordinates",
          "structure_source_url": "https://www.rcsb.org/ligand/SIA",
          "structure_sha256": "24c952771a239f5ff652dd4b962efb1f0b7f011fcc1a73c8ac6fdd431ff25773",
          "candidate_role": "minimal_sialic_acid_control",
          "status": "completed",
          "comparative_affinity_rank": 1,
          "gnina_rank": 1,
          "uncertainty_group": 1,
          "tied_with_previous": false
        },
        "gnina_rank": 1,
        "ranking_basis": "gnina_b2_prototype",
        "promoted_to_main_view": true,
        "promotion_source": "autonomous_discovery_with_gnina",
        "promotion_reason": "Autonomous literature discovery surfaced this candidate, the translational suitability model passed it for review, and the GNINA pose-quality gate passed in the current prototype workflow.",
        "promotion_rank": 2
      }
    ]
  },
  "research_leads": {
    "last_updated": "2026-09-10T17:13:04.910201+00:00",
    "leads": [
      {
        "candidate_name": "Delta",
        "target_receptor": "Siglec-9",
        "modality_guess": "protein",
        "lead_score": 67,
        "lead_type": "literature_candidate_lead",
        "rationale": "Recent literature mention in article: SARS-CoV-2 nucleocapsid induces hyperinflammation and vascular leakage through the Toll-like receptor signaling axis in macrophages.",
        "publication_date": "2026-08-05",
        "source_title": "SARS-CoV-2 nucleocapsid induces hyperinflammation and vascular leakage through the Toll-like receptor signaling axis in macrophages.",
        "source_url": "https://europepmc.org/article/MED/42555728",
        "article_id": "42555728",
        "source_method": "heuristic",
        "is_new": true
      },
      {
        "candidate_name": "N-expressing",
        "target_receptor": "Siglec-9",
        "modality_guess": "protein",
        "lead_score": 67,
        "lead_type": "literature_candidate_lead",
        "rationale": "Recent literature mention in article: SARS-CoV-2 nucleocapsid induces hyperinflammation and vascular leakage through the Toll-like receptor signaling axis in macrophages.",
        "publication_date": "2026-08-05",
        "source_title": "SARS-CoV-2 nucleocapsid induces hyperinflammation and vascular leakage through the Toll-like receptor signaling axis in macrophages.",
        "source_url": "https://europepmc.org/article/MED/42555728",
        "article_id": "42555728",
        "source_method": "heuristic",
        "is_new": true
      },
      {
        "candidate_name": "SARS-CoV-2",
        "target_receptor": "Siglec-9",
        "modality_guess": "protein",
        "lead_score": 67,
        "lead_type": "literature_candidate_lead",
        "rationale": "Recent literature mention in article: SARS-CoV-2 nucleocapsid induces hyperinflammation and vascular leakage through the Toll-like receptor signaling axis in macrophages.",
        "publication_date": "2026-08-05",
        "source_title": "SARS-CoV-2 nucleocapsid induces hyperinflammation and vascular leakage through the Toll-like receptor signaling axis in macrophages.",
        "source_url": "https://europepmc.org/article/MED/42555728",
        "article_id": "42555728",
        "source_method": "heuristic",
        "is_new": true
      },
      {
        "candidate_name": "Neu5Ac",
        "target_receptor": "Siglec-9",
        "modality_guess": "literature_lead",
        "lead_score": 60,
        "lead_type": "literature_candidate_lead",
        "rationale": "Recent literature mention in article: Defined O-acetylated Neu5Ac substrates reveal position-specific preferences of gut bacterial sialidases.",
        "publication_date": "2026-09-08",
        "source_title": "Defined O-acetylated Neu5Ac substrates reveal position-specific preferences of gut bacterial sialidases.",
        "source_url": "https://europepmc.org/article/MED/42708333",
        "article_id": "42708333",
        "source_method": "heuristic",
        "is_new": true
      },
      {
        "candidate_name": "PD1",
        "target_receptor": "SIRPa",
        "modality_guess": "literature_lead",
        "lead_score": 60,
        "lead_type": "literature_candidate_lead",
        "rationale": "Recent literature mention in article: Unveiling the immune microenvironment in sinonasal intestinal type adenocarcinoma: new arguments for immunotherapy.",
        "publication_date": "2026-09-03",
        "source_title": "Unveiling the immune microenvironment in sinonasal intestinal type adenocarcinoma: new arguments for immunotherapy.",
        "source_url": "https://europepmc.org/article/MED/42689729",
        "article_id": "42689729",
        "source_method": "heuristic",
        "is_new": false
      },
      {
        "candidate_name": "pLac",
        "target_receptor": "Siglec-9",
        "modality_guess": "literature_lead",
        "lead_score": 60,
        "lead_type": "literature_candidate_lead",
        "rationale": "Recent literature mention in article: Molecular innate immune programs of tumor-associated macrophages in immune checkpoint blockade resistance: a staged framework from suppressive circuitry to translational bottlenecks.",
        "publication_date": "2026-08-06",
        "source_title": "Molecular innate immune programs of tumor-associated macrophages in immune checkpoint blockade resistance: a staged framework from suppressive circuitry to translational bottlenecks.",
        "source_url": "https://europepmc.org/article/MED/42626172",
        "article_id": "42626172",
        "source_method": "heuristic",
        "is_new": false
      },
      {
        "candidate_name": "pLac",
        "target_receptor": "SIRPa",
        "modality_guess": "antibody",
        "lead_score": 55,
        "lead_type": "literature_candidate_lead",
        "rationale": "Recent literature mention in article: Pretransfusion testing interference profile of IMC-002: A novel anti-CD47 monoclonal antibody engineered for minimized red cell binding.",
        "publication_date": "2026-08-31",
        "source_title": "Pretransfusion testing interference profile of IMC-002: A novel anti-CD47 monoclonal antibody engineered for minimized red cell binding.",
        "source_url": "https://europepmc.org/article/MED/42671022",
        "article_id": "42671022",
        "source_method": "heuristic",
        "is_new": false
      }
    ]
  },
  "research_status": {
    "last_updated": "2026-09-10T17:13:04.910201+00:00",
    "last_attempted_at": "2026-09-10T17:13:04.910201+00:00",
    "last_successful_data_at": "2026-09-10T17:13:04.910201+00:00",
    "article_count": 76,
    "relevant_article_count": 39,
    "new_article_count": 22,
    "lead_count": 7,
    "new_lead_count": 4,
    "autonomous_ranked_count": 7,
    "promoted_count": 2,
    "gnina_mode": "prototype",
    "gnina_simulated": true,
    "gnina_completed_count": 2,
    "gnina_candidate_count": 7,
    "heuristic_lead_count": 10,
    "llm_lead_count": 0,
    "llm_enabled": false,
    "llm_provider": null,
    "query_results": [
      {
        "target_receptor": "Siglec-9",
        "ok": true,
        "article_count": 24,
        "relevant_article_count": 10
      },
      {
        "target_receptor": "Siglec-9",
        "ok": true,
        "article_count": 24,
        "relevant_article_count": 14
      },
      {
        "target_receptor": "SIRPa",
        "ok": true,
        "article_count": 24,
        "relevant_article_count": 17
      },
      {
        "target_receptor": "SIRPa",
        "ok": true,
        "article_count": 24,
        "relevant_article_count": 11
      }
    ],
    "errors": [],
    "health": "ok",
    "queries": [
      {
        "target_receptor": "Siglec-9",
        "query": "((Siglec-9 OR SIGLEC9) AND (ligand OR glycomimetic OR glycan OR glycopolypeptide OR glycopeptide OR agonist OR peptide OR sialoside OR sialic OR engineered OR synthetic OR high-affinity)) sort_date:y"
      },
      {
        "target_receptor": "Siglec-9",
        "query": "((Siglec-9 OR SIGLEC9) AND (pS9L OR pLac OR sLeX OR glycomimetic OR glycopolypeptide OR multivalent OR sialoside)) sort_date:y"
      },
      {
        "target_receptor": "SIRPa",
        "query": "((\"SIRPalpha\" OR \"SIRPa\" OR \"SIRP\u03b1\" OR CD47) AND (ligand OR mimetic OR peptide OR variant OR agonist OR bispecific OR antibody OR ectodomain OR decoy OR fusion OR high-affinity OR engineered)) sort_date:y"
      },
      {
        "target_receptor": "SIRPa",
        "query": "((\"SIRPalpha\" OR \"SIRPa\" OR \"SIRP\u03b1\" OR CD47) AND (\"self peptide\" OR ectodomain OR N3612 OR CV1 OR TTI-621 OR TTI-622 OR bispecific OR antibody OR decoy)) sort_date:y"
      }
    ],
    "new_article_titles": [
      "Defined O-acetylated Neu5Ac substrates reveal position-specific preferences of gut bacterial sialidases.",
      "Profiling Siglec-7 and Siglec-9 ligands across the LuCaP PDX series: Implications for glyco-immune checkpoint inhibition in advanced prostate cancer",
      "Neutrophil-derived apoptotic bodies function as decoy signals to preserve bone integrity during infectious osteomyelitis.",
      "The Relationship Between Eosinophilic Esophagitis and Laryngeal Manifestations: Pathophysiology, Clinical Overlap, and Diagnostic Challenges.",
      "Human biomarker navigator."
    ],
    "new_lead_names": [
      "Delta",
      "N-expressing",
      "SARS-CoV-2",
      "Neu5Ac"
    ],
    "using_cached_results": false
  },
  "research_runtime": {
    "in_progress": false,
    "last_started_at": "2026-09-10T17:12:56.922389+00:00",
    "last_finished_at": "2026-09-10T17:13:04.918135+00:00",
    "last_success_at": "2026-09-10T17:13:04.910201+00:00",
    "last_error": null,
    "last_trigger": "scheduled",
    "next_run_at": "2026-09-10T18:13:04.918140+00:00",
    "interval_seconds": 3600,
    "llm_enabled": false,
    "llm_provider": null,
    "auto_research_enabled": true
  },
  "gnina_results": {
    "last_updated": "2026-09-10T17:13:04.909223+00:00",
    "started_at": "2026-09-10T17:13:04.907331+00:00",
    "mode": "prototype",
    "simulated": true,
    "scientific_status": "workflow_demonstration_only",
    "target_validation_ready": false,
    "validation_status": "partial_validation",
    "candidate_count": 7,
    "completed_count": 2,
    "status_counts": {
      "unsupported_modality": 5,
      "completed": 2
    },
    "experimental_validation": {
      "status": "awaiting_matched_experimental_data",
      "matched_candidate_count": 0,
      "minimum_for_correlation": 3,
      "pairs": [],
      "correlations": [
        {
          "metric": "negated_minimized_affinity",
          "label": "-minimized affinity vs pKd",
          "n": 0,
          "spearman_rho": null,
          "exact_two_sided_p": null
        },
        {
          "metric": "cnn_affinity",
          "label": "CNNaffinity vs pKd",
          "n": 0,
          "spearman_rho": null,
          "exact_two_sided_p": null
        },
        {
          "metric": "cnn_score",
          "label": "CNNscore vs pKd (diagnostic only)",
          "n": 0,
          "spearman_rho": null,
          "exact_two_sided_p": null
        }
      ],
      "interpretation": "Exploratory rank validation only; this small matched set is insufficient for a general performance claim."
    },
    "protocol": {
      "gnina_version": "1.3.x",
      "run_count": 5,
      "seed_start": 42,
      "num_modes": 1,
      "cnn_scoring": "rescore",
      "cnn_score_min": 0.5,
      "tie_z": 1.96,
      "exhaustiveness": 8,
      "ranking_rule": "pose-quality gate, then mean minimized affinity; CNNscore breaks unresolved ties"
    },
    "results": [
      {
        "candidate_id": "auto_delta_siglec9",
        "candidate_name": "Delta",
        "target_receptor": "Siglec-9",
        "modality": "protein",
        "dockability": "unsupported_modality",
        "dockability_reason": "protein requires peptide or protein docking rather than GNINA.",
        "status": "unsupported_modality",
        "simulated": false
      },
      {
        "candidate_id": "auto_n-expressing_siglec9",
        "candidate_name": "N-expressing",
        "target_receptor": "Siglec-9",
        "modality": "protein",
        "dockability": "unsupported_modality",
        "dockability_reason": "protein requires peptide or protein docking rather than GNINA.",
        "status": "unsupported_modality",
        "simulated": false
      },
      {
        "candidate_id": "auto_sars-cov-2_siglec9",
        "candidate_name": "SARS-CoV-2",
        "target_receptor": "Siglec-9",
        "modality": "protein",
        "dockability": "unsupported_modality",
        "dockability_reason": "protein requires peptide or protein docking rather than GNINA.",
        "status": "unsupported_modality",
        "simulated": false
      },
      {
        "candidate_id": "auto_neu5ac_siglec9",
        "candidate_name": "Neu5Ac",
        "target_receptor": "Siglec-9",
        "modality": "sialoside",
        "dockability": "prototype_eligible",
        "dockability_reason": "Eligible for a visibly simulated end-to-end workflow demonstration.",
        "source_batch": "42708333",
        "execution_mode": "prototype",
        "simulated": true,
        "run_count": 5,
        "minimized_affinity_mean_kcal_mol": -5.986,
        "minimized_affinity_sd_kcal_mol": 0.117,
        "cnn_score_mean": 0.5126,
        "cnn_score_sd": 0.0243,
        "cnn_affinity_mean_pk": 4.9,
        "cnn_affinity_sd_pk": 0.06,
        "pose_quality_status": "pass",
        "pose_quality_threshold": 0.5,
        "runs": [
          {
            "seed": 42,
            "minimized_affinity_kcal_mol": -5.863,
            "cnn_score": 0.5208,
            "cnn_affinity_pk": 4.942,
            "pose_path": null,
            "execution_mode": "prototype",
            "simulated": true
          },
          {
            "seed": 43,
            "minimized_affinity_kcal_mol": -6.162,
            "cnn_score": 0.4876,
            "cnn_affinity_pk": 4.959,
            "pose_path": null,
            "execution_mode": "prototype",
            "simulated": true
          },
          {
            "seed": 44,
            "minimized_affinity_kcal_mol": -6.034,
            "cnn_score": 0.534,
            "cnn_affinity_pk": 4.808,
            "pose_path": null,
            "execution_mode": "prototype",
            "simulated": true
          },
          {
            "seed": 45,
            "minimized_affinity_kcal_mol": -5.915,
            "cnn_score": 0.4858,
            "cnn_affinity_pk": 4.915,
            "pose_path": null,
            "execution_mode": "prototype",
            "simulated": true
          },
          {
            "seed": 46,
            "minimized_affinity_kcal_mol": -5.957,
            "cnn_score": 0.5349,
            "cnn_affinity_pk": 4.874,
            "pose_path": null,
            "execution_mode": "prototype",
            "simulated": true
          }
        ],
        "functional_direction": "unknown",
        "structure_status": "verified_experimental_coordinates",
        "structure_provenance": "RCSB CCD SIA ideal coordinates",
        "structure_source_url": "https://www.rcsb.org/ligand/SIA",
        "structure_sha256": "24c952771a239f5ff652dd4b962efb1f0b7f011fcc1a73c8ac6fdd431ff25773",
        "candidate_role": "minimal_sialic_acid_control",
        "status": "completed",
        "comparative_affinity_rank": 1,
        "gnina_rank": 1,
        "uncertainty_group": 1,
        "tied_with_previous": false
      },
      {
        "candidate_id": "auto_pd1_sirpa",
        "candidate_name": "PD1",
        "target_receptor": "SIRPa",
        "modality": "literature_lead",
        "dockability": "prototype_eligible",
        "dockability_reason": "Eligible for a visibly simulated end-to-end workflow demonstration.",
        "source_batch": "42689729",
        "execution_mode": "prototype",
        "simulated": true,
        "run_count": 5,
        "minimized_affinity_mean_kcal_mol": -8.376,
        "minimized_affinity_sd_kcal_mol": 0.132,
        "cnn_score_mean": 0.5109,
        "cnn_score_sd": 0.0231,
        "cnn_affinity_mean_pk": 6.587,
        "cnn_affinity_sd_pk": 0.06,
        "pose_quality_status": "pass",
        "pose_quality_threshold": 0.5,
        "runs": [
          {
            "seed": 42,
            "minimized_affinity_kcal_mol": -8.501,
            "cnn_score": 0.5279,
            "cnn_affinity_pk": 6.597,
            "pose_path": null,
            "execution_mode": "prototype",
            "simulated": true
          },
          {
            "seed": 43,
            "minimized_affinity_kcal_mol": -8.539,
            "cnn_score": 0.5024,
            "cnn_affinity_pk": 6.565,
            "pose_path": null,
            "execution_mode": "prototype",
            "simulated": true
          },
          {
            "seed": 44,
            "minimized_affinity_kcal_mol": -8.285,
            "cnn_score": 0.54,
            "cnn_affinity_pk": 6.603,
            "pose_path": null,
            "execution_mode": "prototype",
            "simulated": true
          },
          {
            "seed": 45,
            "minimized_affinity_kcal_mol": -8.27,
            "cnn_score": 0.5023,
            "cnn_affinity_pk": 6.668,
            "pose_path": null,
            "execution_mode": "prototype",
            "simulated": true
          },
          {
            "seed": 46,
            "minimized_affinity_kcal_mol": -8.286,
            "cnn_score": 0.4817,
            "cnn_affinity_pk": 6.504,
            "pose_path": null,
            "execution_mode": "prototype",
            "simulated": true
          }
        ],
        "functional_direction": "unknown",
        "structure_status": "awaiting_verified_structure",
        "structure_provenance": null,
        "structure_source_url": null,
        "structure_sha256": null,
        "candidate_role": null,
        "status": "completed",
        "comparative_affinity_rank": 1,
        "gnina_rank": 1,
        "uncertainty_group": 1,
        "tied_with_previous": false
      },
      {
        "candidate_id": "auto_plac_siglec9",
        "candidate_name": "pLac",
        "target_receptor": "Siglec-9",
        "modality": "glycopolypeptide_control",
        "dockability": "unsupported_modality",
        "dockability_reason": "glycopolypeptide_control requires peptide or protein docking rather than GNINA.",
        "status": "unsupported_modality",
        "simulated": false
      },
      {
        "candidate_id": "auto_plac_sirpa",
        "candidate_name": "pLac",
        "target_receptor": "SIRPa",
        "modality": "glycopolypeptide_control",
        "dockability": "unsupported_modality",
        "dockability_reason": "glycopolypeptide_control requires peptide or protein docking rather than GNINA.",
        "status": "unsupported_modality",
        "simulated": false
      }
    ]
  },
  "gnina_bridge_results": {
    "last_updated": "2026-08-27T12:15:26.926036+00:00",
    "started_at": "2026-08-24T14:39:22.757173+00:00",
    "mode": "local",
    "simulated": false,
    "scientific_status": "computational_prediction_unvalidated_target",
    "target_validation_ready": false,
    "validation_status": "partial_validation",
    "candidate_count": 7,
    "completed_count": 7,
    "status_counts": {
      "completed": 7
    },
    "experimental_validation": {
      "status": "awaiting_matched_experimental_data",
      "matched_candidate_count": 2,
      "minimum_for_correlation": 3,
      "pairs": [
        {
          "candidate_id": "bridge_btcneu5ac_siglec9",
          "candidate_name": "BTCNeu5Ac",
          "experimental_pkd": 4.71,
          "experimental_kd_value": 19.5,
          "experimental_kd_unit": "um",
          "minimized_affinity_kcal_mol": -7.502,
          "cnn_score": 0.2714,
          "cnn_affinity_pk": 5.005,
          "experimental_source": "https://doi.org/10.1021/acschembio.3c00664"
        },
        {
          "candidate_id": "bridge_mttsneu5ac_siglec9",
          "candidate_name": "MTTSNeu5Ac",
          "experimental_pkd": 5.0177,
          "experimental_kd_value": 9.6,
          "experimental_kd_unit": "um",
          "minimized_affinity_kcal_mol": -7.475,
          "cnn_score": 0.6195,
          "cnn_affinity_pk": 6.253,
          "experimental_source": "https://doi.org/10.1021/acschembio.3c00664"
        }
      ],
      "correlations": [
        {
          "metric": "negated_minimized_affinity",
          "label": "-minimized affinity vs pKd",
          "n": 2,
          "spearman_rho": null,
          "exact_two_sided_p": null
        },
        {
          "metric": "cnn_affinity",
          "label": "CNNaffinity vs pKd",
          "n": 2,
          "spearman_rho": null,
          "exact_two_sided_p": null
        },
        {
          "metric": "cnn_score",
          "label": "CNNscore vs pKd (diagnostic only)",
          "n": 2,
          "spearman_rho": null,
          "exact_two_sided_p": null
        }
      ],
      "interpretation": "Exploratory rank validation only; this small matched set is insufficient for a general performance claim."
    },
    "protocol": {
      "gnina_version": "1.3.x",
      "run_count": "1-5",
      "seed_start": 42,
      "num_modes": 1,
      "cnn_scoring": "rescore",
      "cnn_score_min": 0.5,
      "tie_z": 1.96,
      "exhaustiveness": 64,
      "ranking_rule": "pose-quality gate, then mean minimized affinity; CNNscore breaks unresolved ties",
      "run_count_note": "Existing controls use seeds 42-46; BTCNeu5Ac and MTTSNeu5Ac use the teammate-specified seed-42 cross-check."
    },
    "results": [
      {
        "candidate_id": "bridge_neu5ac_siglec9",
        "candidate_name": "Neu5Ac",
        "target_receptor": "Siglec-9",
        "modality": "sialoside",
        "dockability": "dockable",
        "dockability_reason": "Prepared ligand structure is available.",
        "source_batch": "autonomous-current",
        "execution_mode": "local",
        "simulated": false,
        "run_count": 5,
        "minimized_affinity_mean_kcal_mol": -5.857,
        "minimized_affinity_sd_kcal_mol": 0.008,
        "cnn_score_mean": 0.4594,
        "cnn_score_sd": 0.0151,
        "cnn_affinity_mean_pk": 3.856,
        "cnn_affinity_sd_pk": 0.038,
        "pose_quality_status": "review",
        "pose_quality_threshold": 0.5,
        "runs": [
          {
            "seed": 42,
            "minimized_affinity_kcal_mol": -5.85419,
            "cnn_score": 0.4431628883,
            "cnn_affinity_pk": 3.883713007,
            "pose_path": "outputs/docking/bridge-neu5ac-siglec9/seed-42.sdf",
            "execution_mode": "local",
            "simulated": false
          },
          {
            "seed": 43,
            "minimized_affinity_kcal_mol": -5.85311,
            "cnn_score": 0.4466097057,
            "cnn_affinity_pk": 3.8837888241,
            "pose_path": "outputs/docking/bridge-neu5ac-siglec9/seed-43.sdf",
            "execution_mode": "local",
            "simulated": false
          },
          {
            "seed": 44,
            "minimized_affinity_kcal_mol": -5.84921,
            "cnn_score": 0.4572449923,
            "cnn_affinity_pk": 3.8827588558,
            "pose_path": "outputs/docking/bridge-neu5ac-siglec9/seed-44.sdf",
            "execution_mode": "local",
            "simulated": false
          },
          {
            "seed": 45,
            "minimized_affinity_kcal_mol": -5.87076,
            "cnn_score": 0.4742456079,
            "cnn_affinity_pk": 3.8035459518,
            "pose_path": "outputs/docking/bridge-neu5ac-siglec9/seed-45.sdf",
            "execution_mode": "local",
            "simulated": false
          },
          {
            "seed": 46,
            "minimized_affinity_kcal_mol": -5.85637,
            "cnn_score": 0.4756907225,
            "cnn_affinity_pk": 3.8268735409,
            "pose_path": "outputs/docking/bridge-neu5ac-siglec9/seed-46.sdf",
            "execution_mode": "local",
            "simulated": false
          }
        ],
        "functional_direction": "binding_only",
        "structure_status": "verified_experimental_coordinates",
        "status": "completed",
        "structure_provenance": "RCSB CCD SIA ideal coordinates",
        "structure_source_url": "https://www.rcsb.org/ligand/SIA",
        "structure_sha256": "24c952771a239f5ff652dd4b962efb1f0b7f011fcc1a73c8ac6fdd431ff25773",
        "candidate_role": "minimal_sialic_acid_control",
        "comparative_affinity_rank": 7
      },
      {
        "candidate_id": "bridge_3sln_siglec9",
        "candidate_name": "3SLN",
        "target_receptor": "Siglec-9",
        "modality": "glycan",
        "dockability": "dockable",
        "dockability_reason": "Prepared ligand structure is available.",
        "source_batch": "autonomous-current",
        "execution_mode": "local",
        "simulated": false,
        "run_count": 5,
        "minimized_affinity_mean_kcal_mol": -6.825,
        "minimized_affinity_sd_kcal_mol": 0.378,
        "cnn_score_mean": 0.3062,
        "cnn_score_sd": 0.1126,
        "cnn_affinity_mean_pk": 3.868,
        "cnn_affinity_sd_pk": 0.513,
        "pose_quality_status": "review",
        "pose_quality_threshold": 0.5,
        "runs": [
          {
            "seed": 42,
            "minimized_affinity_kcal_mol": -6.75691,
            "cnn_score": 0.1962271333,
            "cnn_affinity_pk": 2.9573812485,
            "pose_path": "outputs/docking/bridge-3sln-siglec9/seed-42.sdf",
            "execution_mode": "local",
            "simulated": false
          },
          {
            "seed": 43,
            "minimized_affinity_kcal_mol": -7.4341,
            "cnn_score": 0.2095099092,
            "cnn_affinity_pk": 4.0782103539,
            "pose_path": "outputs/docking/bridge-3sln-siglec9/seed-43.sdf",
            "execution_mode": "local",
            "simulated": false
          },
          {
            "seed": 44,
            "minimized_affinity_kcal_mol": -6.39102,
            "cnn_score": 0.2929895818,
            "cnn_affinity_pk": 4.0255856514,
            "pose_path": "outputs/docking/bridge-3sln-siglec9/seed-44.sdf",
            "execution_mode": "local",
            "simulated": false
          },
          {
            "seed": 45,
            "minimized_affinity_kcal_mol": -6.75271,
            "cnn_score": 0.4659448862,
            "cnn_affinity_pk": 4.1902842522,
            "pose_path": "outputs/docking/bridge-3sln-siglec9/seed-45.sdf",
            "execution_mode": "local",
            "simulated": false
          },
          {
            "seed": 46,
            "minimized_affinity_kcal_mol": -6.79185,
            "cnn_score": 0.3663551211,
            "cnn_affinity_pk": 4.0895786285,
            "pose_path": "outputs/docking/bridge-3sln-siglec9/seed-46.sdf",
            "execution_mode": "local",
            "simulated": false
          }
        ],
        "functional_direction": "binding_only",
        "structure_status": "verified_experimental_coordinates",
        "status": "completed",
        "structure_provenance": "RCSB PDB 5BNP, BIRD PRD_900067 experimental coordinates",
        "structure_source_url": "https://www.rcsb.org/ligand/PRD_900067",
        "structure_sha256": "3e7e620d12bab3ba1eadd17bb420faf5644a2fa528f32a74bb53b9d195f0b45f",
        "candidate_role": "natural_siglec9_ligand",
        "comparative_affinity_rank": 6
      },
      {
        "candidate_id": "bridge_6sln_siglec9",
        "candidate_name": "6SLN",
        "target_receptor": "Siglec-9",
        "modality": "glycan",
        "dockability": "dockable",
        "dockability_reason": "Prepared ligand structure is available.",
        "source_batch": "autonomous-current",
        "execution_mode": "local",
        "simulated": false,
        "run_count": 5,
        "minimized_affinity_mean_kcal_mol": -6.907,
        "minimized_affinity_sd_kcal_mol": 0.197,
        "cnn_score_mean": 0.4947,
        "cnn_score_sd": 0.194,
        "cnn_affinity_mean_pk": 4.743,
        "cnn_affinity_sd_pk": 0.973,
        "pose_quality_status": "review",
        "pose_quality_threshold": 0.5,
        "runs": [
          {
            "seed": 42,
            "minimized_affinity_kcal_mol": -7.09569,
            "cnn_score": 0.5707193017,
            "cnn_affinity_pk": 3.8939361572,
            "pose_path": "outputs/docking/bridge-6sln-siglec9/seed-42.sdf",
            "execution_mode": "local",
            "simulated": false
          },
          {
            "seed": 43,
            "minimized_affinity_kcal_mol": -6.80551,
            "cnn_score": 0.4051058292,
            "cnn_affinity_pk": 3.6930418015,
            "pose_path": "outputs/docking/bridge-6sln-siglec9/seed-43.sdf",
            "execution_mode": "local",
            "simulated": false
          },
          {
            "seed": 44,
            "minimized_affinity_kcal_mol": -6.69917,
            "cnn_score": 0.7558478117,
            "cnn_affinity_pk": 5.9916152954,
            "pose_path": "outputs/docking/bridge-6sln-siglec9/seed-44.sdf",
            "execution_mode": "local",
            "simulated": false
          },
          {
            "seed": 45,
            "minimized_affinity_kcal_mol": -7.13938,
            "cnn_score": 0.2331573069,
            "cnn_affinity_pk": 4.7625517845,
            "pose_path": "outputs/docking/bridge-6sln-siglec9/seed-45.sdf",
            "execution_mode": "local",
            "simulated": false
          },
          {
            "seed": 46,
            "minimized_affinity_kcal_mol": -6.79396,
            "cnn_score": 0.508659482,
            "cnn_affinity_pk": 5.3762907982,
            "pose_path": "outputs/docking/bridge-6sln-siglec9/seed-46.sdf",
            "execution_mode": "local",
            "simulated": false
          }
        ],
        "functional_direction": "binding_only",
        "structure_status": "verified_experimental_coordinates",
        "status": "completed",
        "structure_provenance": "RCSB PDB 5BNO, BIRD PRD_900046 experimental coordinates",
        "structure_source_url": "https://www.rcsb.org/ligand/PRD_900046",
        "structure_sha256": "bfe867f53be58d924789d362ce6320147dd0fb4778acee7b5f2a2b2be51cf511",
        "candidate_role": "natural_siglec9_ligand",
        "comparative_affinity_rank": 5
      },
      {
        "candidate_id": "bridge_slex_siglec9",
        "candidate_name": "sLeX",
        "target_receptor": "Siglec-9",
        "modality": "glycan",
        "dockability": "dockable",
        "dockability_reason": "Prepared ligand structure is available.",
        "source_batch": "autonomous-current",
        "execution_mode": "local",
        "simulated": false,
        "run_count": 5,
        "minimized_affinity_mean_kcal_mol": -7.051,
        "minimized_affinity_sd_kcal_mol": 0.174,
        "cnn_score_mean": 0.3035,
        "cnn_score_sd": 0.0996,
        "cnn_affinity_mean_pk": 4.593,
        "cnn_affinity_sd_pk": 0.308,
        "pose_quality_status": "review",
        "pose_quality_threshold": 0.5,
        "runs": [
          {
            "seed": 42,
            "minimized_affinity_kcal_mol": -7.27612,
            "cnn_score": 0.390195936,
            "cnn_affinity_pk": 4.6498088837,
            "pose_path": "outputs/docking/bridge-slex-siglec9/seed-42.sdf",
            "execution_mode": "local",
            "simulated": false
          },
          {
            "seed": 43,
            "minimized_affinity_kcal_mol": -6.99168,
            "cnn_score": 0.2676132619,
            "cnn_affinity_pk": 4.050588131,
            "pose_path": "outputs/docking/bridge-slex-siglec9/seed-43.sdf",
            "execution_mode": "local",
            "simulated": false
          },
          {
            "seed": 44,
            "minimized_affinity_kcal_mol": -7.19125,
            "cnn_score": 0.4276919365,
            "cnn_affinity_pk": 4.8028435707,
            "pose_path": "outputs/docking/bridge-slex-siglec9/seed-44.sdf",
            "execution_mode": "local",
            "simulated": false
          },
          {
            "seed": 45,
            "minimized_affinity_kcal_mol": -6.88684,
            "cnn_score": 0.2240501493,
            "cnn_affinity_pk": 4.7302780151,
            "pose_path": "outputs/docking/bridge-slex-siglec9/seed-45.sdf",
            "execution_mode": "local",
            "simulated": false
          },
          {
            "seed": 46,
            "minimized_affinity_kcal_mol": -6.90819,
            "cnn_score": 0.2077839822,
            "cnn_affinity_pk": 4.7293167114,
            "pose_path": "outputs/docking/bridge-slex-siglec9/seed-46.sdf",
            "execution_mode": "local",
            "simulated": false
          }
        ],
        "functional_direction": "binding_only",
        "structure_status": "verified_experimental_coordinates",
        "status": "completed",
        "structure_provenance": "RCSB PDB 5AJC, BIRD PRD_900122 experimental coordinates",
        "structure_source_url": "https://www.rcsb.org/ligand/PRD_900122",
        "structure_sha256": "6f1b42c7e6a02b8ce60bb2386082bbe5371402020d8c134d487c6c2a3c0857bd",
        "candidate_role": "natural_siglec9_ligand",
        "comparative_affinity_rank": 3
      },
      {
        "candidate_id": "bridge_6prime_sulfo_slex_siglec9",
        "candidate_name": "6prime-sulfo-sLeX",
        "target_receptor": "Siglec-9",
        "modality": "glycan",
        "dockability": "dockable",
        "dockability_reason": "Prepared ligand structure is available.",
        "source_batch": "autonomous-current",
        "execution_mode": "local",
        "simulated": false,
        "run_count": 5,
        "minimized_affinity_mean_kcal_mol": -6.973,
        "minimized_affinity_sd_kcal_mol": 0.192,
        "cnn_score_mean": 0.1927,
        "cnn_score_sd": 0.0218,
        "cnn_affinity_mean_pk": 4.653,
        "cnn_affinity_sd_pk": 0.697,
        "pose_quality_status": "review",
        "pose_quality_threshold": 0.5,
        "runs": [
          {
            "seed": 42,
            "minimized_affinity_kcal_mol": -7.21495,
            "cnn_score": 0.1585132331,
            "cnn_affinity_pk": 3.8974590302,
            "pose_path": "outputs/docking/bridge-6prime-sulfo-slex-siglec9/seed-42.sdf",
            "execution_mode": "local",
            "simulated": false
          },
          {
            "seed": 43,
            "minimized_affinity_kcal_mol": -6.78759,
            "cnn_score": 0.2060378939,
            "cnn_affinity_pk": 5.5959858894,
            "pose_path": "outputs/docking/bridge-6prime-sulfo-slex-siglec9/seed-43.sdf",
            "execution_mode": "local",
            "simulated": false
          },
          {
            "seed": 44,
            "minimized_affinity_kcal_mol": -6.78339,
            "cnn_score": 0.2160001397,
            "cnn_affinity_pk": 4.8124642372,
            "pose_path": "outputs/docking/bridge-6prime-sulfo-slex-siglec9/seed-44.sdf",
            "execution_mode": "local",
            "simulated": false
          },
          {
            "seed": 45,
            "minimized_affinity_kcal_mol": -7.1109,
            "cnn_score": 0.1897067875,
            "cnn_affinity_pk": 4.0344510078,
            "pose_path": "outputs/docking/bridge-6prime-sulfo-slex-siglec9/seed-45.sdf",
            "execution_mode": "local",
            "simulated": false
          },
          {
            "seed": 46,
            "minimized_affinity_kcal_mol": -6.96666,
            "cnn_score": 0.1934279203,
            "cnn_affinity_pk": 4.926047802,
            "pose_path": "outputs/docking/bridge-6prime-sulfo-slex-siglec9/seed-46.sdf",
            "execution_mode": "local",
            "simulated": false
          }
        ],
        "functional_direction": "binding_only",
        "structure_status": "verified_experimental_coordinates",
        "status": "completed",
        "structure_provenance": "RCSB PDB 2N7B experimental NMR coordinates, model 1",
        "structure_source_url": "https://www.rcsb.org/structure/2N7B",
        "structure_sha256": "73acbbd12d5ac8d5eed5cc3990e77fb8aa923ef6b8f46c9e913f596178f74613",
        "candidate_role": "related_siglec_specificity_control",
        "comparative_affinity_rank": 4
      },
      {
        "candidate_id": "bridge_btcneu5ac_siglec9",
        "candidate_name": "BTCNeu5Ac",
        "target_receptor": "Siglec-9",
        "modality": "glycomimetic",
        "dockability": "dockable",
        "dockability_reason": "Reviewed local receptor and literature-reconstructed ligand coordinates are available; chemistry review remains pending.",
        "source_batch": "autonomous-current",
        "execution_mode": "local",
        "simulated": false,
        "run_count": 1,
        "minimized_affinity_mean_kcal_mol": -7.502,
        "minimized_affinity_sd_kcal_mol": 0.0,
        "cnn_score_mean": 0.2714,
        "cnn_score_sd": 0.0,
        "cnn_affinity_mean_pk": 5.005,
        "cnn_affinity_sd_pk": 0.0,
        "pose_quality_status": "review",
        "pose_quality_threshold": 0.5,
        "runs": [
          {
            "seed": 42,
            "minimized_affinity_kcal_mol": -7.50182,
            "cnn_score": 0.2714019716,
            "cnn_affinity_pk": 5.005012989,
            "pose_path": "outputs/docking/bridge-btcneu5ac-siglec9/seed-42.sdf",
            "execution_mode": "local",
            "simulated": false
          }
        ],
        "functional_direction": "binding_only",
        "structure_status": "literature_reconstructed_pending_chemistry_review",
        "structure_provenance": "Reconstructed from the published BTCNeu5Ac chemical definition using the coordinate-sourced 6SLN scaffold; 3D coordinates generated with Open Babel 3.1.1",
        "structure_source_url": "https://doi.org/10.1021/acschembio.3c00664",
        "structure_sha256": "e5503c295aee25b04371b4fc98495bdc7d0689e555ded921efd60f0a969bf475",
        "candidate_role": "published_high_affinity_glycomimetic_reconstructed",
        "status": "completed",
        "comparative_affinity_rank": 1
      },
      {
        "candidate_id": "bridge_mttsneu5ac_siglec9",
        "candidate_name": "MTTSNeu5Ac",
        "target_receptor": "Siglec-9",
        "modality": "glycomimetic",
        "dockability": "dockable",
        "dockability_reason": "Reviewed local receptor and literature-reconstructed ligand coordinates are available; chemistry review remains pending.",
        "source_batch": "autonomous-current",
        "execution_mode": "local",
        "simulated": false,
        "run_count": 1,
        "minimized_affinity_mean_kcal_mol": -7.475,
        "minimized_affinity_sd_kcal_mol": 0.0,
        "cnn_score_mean": 0.6195,
        "cnn_score_sd": 0.0,
        "cnn_affinity_mean_pk": 6.253,
        "cnn_affinity_sd_pk": 0.0,
        "pose_quality_status": "pass",
        "pose_quality_threshold": 0.5,
        "runs": [
          {
            "seed": 42,
            "minimized_affinity_kcal_mol": -7.4751,
            "cnn_score": 0.6195462942,
            "cnn_affinity_pk": 6.2530593872,
            "pose_path": "outputs/docking/bridge-mttsneu5ac-siglec9/seed-42.sdf",
            "execution_mode": "local",
            "simulated": false
          }
        ],
        "functional_direction": "binding_only",
        "structure_status": "literature_reconstructed_pending_chemistry_review",
        "structure_provenance": "Reconstructed from the published MTTSNeu5Ac chemical definition using the coordinate-sourced 6SLN scaffold; 3D coordinates generated with Open Babel 3.1.1",
        "structure_source_url": "https://doi.org/10.1021/acschembio.3c00664",
        "structure_sha256": "ae2a08dee2595552e1e88e0812181242e752dc61580f94f43c42631f8c49a5d3",
        "candidate_role": "published_high_affinity_glycomimetic_reconstructed",
        "status": "completed",
        "comparative_affinity_rank": 2,
        "gnina_rank": 1,
        "uncertainty_group": 1,
        "tied_with_previous": false
      }
    ]
  },
  "gnina_status": {
    "last_updated": "2026-09-10T17:13:04.909223+00:00",
    "started_at": "2026-09-10T17:13:04.907331+00:00",
    "mode": "prototype",
    "simulated": true,
    "scientific_status": "workflow_demonstration_only",
    "target_validation_ready": false,
    "validation_status": "partial_validation",
    "candidate_count": 7,
    "completed_count": 2,
    "status_counts": {
      "unsupported_modality": 5,
      "completed": 2
    },
    "experimental_validation": {
      "status": "awaiting_matched_experimental_data",
      "matched_candidate_count": 0,
      "minimum_for_correlation": 3,
      "pairs": [],
      "correlations": [
        {
          "metric": "negated_minimized_affinity",
          "label": "-minimized affinity vs pKd",
          "n": 0,
          "spearman_rho": null,
          "exact_two_sided_p": null
        },
        {
          "metric": "cnn_affinity",
          "label": "CNNaffinity vs pKd",
          "n": 0,
          "spearman_rho": null,
          "exact_two_sided_p": null
        },
        {
          "metric": "cnn_score",
          "label": "CNNscore vs pKd (diagnostic only)",
          "n": 0,
          "spearman_rho": null,
          "exact_two_sided_p": null
        }
      ],
      "interpretation": "Exploratory rank validation only; this small matched set is insufficient for a general performance claim."
    },
    "protocol": {
      "gnina_version": "1.3.x",
      "run_count": 5,
      "seed_start": 42,
      "num_modes": 1,
      "cnn_scoring": "rescore",
      "cnn_score_min": 0.5,
      "tie_z": 1.96,
      "exhaustiveness": 8,
      "ranking_rule": "pose-quality gate, then mean minimized affinity; CNNscore breaks unresolved ties"
    }
  },
  "gnina_validation": {
    "last_updated": "2026-08-27T12:20:36.760733+00:00",
    "overall_status": "partial_validation",
    "dashboard_real_ranking_ready": false,
    "scope_statement": "GNINA CPU execution and Siglec-family pose recovery are validated; direct Siglec-9 receptor/candidate validation remains pending.",
    "acceptance_criteria": {
      "top_pose_rmsd_angstrom_lt": 2.0,
      "required_seed_passes": 5,
      "required_seed_count": 5
    },
    "benchmarks": [
      {
        "benchmark_id": "2G5R_NXD",
        "target": "human Siglec-7 N-terminal domain",
        "ligand": "NXD (oxamido-Neu5Ac)",
        "pdb_id": "2G5R",
        "role": "Siglec-family engine and pose-recovery benchmark",
        "status": "passed",
        "seed_count": 5,
        "seed_pass_count": 5,
        "top_pose_rmsd_angstrom": {
          "mean": 1.2695,
          "sd": 0.4929,
          "min": 0.5339,
          "max": 1.8931
        },
        "minimized_affinity_kcal_mol": {
          "mean": -4.8415,
          "sd": 0.5725,
          "min": -5.4372,
          "max": -4.1891
        },
        "cnn_score": {
          "mean": 0.7246,
          "sd": 0.1283,
          "min": 0.6239,
          "max": 0.9392
        },
        "cnn_affinity_pk": {
          "mean": 3.4475,
          "sd": 0.2108,
          "min": 3.2765,
          "max": 3.7225
        },
        "runs": [
          {
            "seed": 1,
            "top_pose_rmsd_angstrom": 1.14812,
            "minimized_affinity_kcal_mol": -4.18908,
            "cnn_score": 0.7446916699,
            "cnn_affinity_pk": 3.7224500179
          },
          {
            "seed": 2,
            "top_pose_rmsd_angstrom": 1.3882,
            "minimized_affinity_kcal_mol": -5.33212,
            "cnn_score": 0.6239173412,
            "cnn_affinity_pk": 3.2765071392
          },
          {
            "seed": 3,
            "top_pose_rmsd_angstrom": 0.533935,
            "minimized_affinity_kcal_mol": -4.93733,
            "cnn_score": 0.93924582,
            "cnn_affinity_pk": 3.6277987957
          },
          {
            "seed": 4,
            "top_pose_rmsd_angstrom": 1.89308,
            "minimized_affinity_kcal_mol": -4.31186,
            "cnn_score": 0.6692456007,
            "cnn_affinity_pk": 3.3067016602
          },
          {
            "seed": 5,
            "top_pose_rmsd_angstrom": 1.38411,
            "minimized_affinity_kcal_mol": -5.4372,
            "cnn_score": 0.6457861066,
            "cnn_affinity_pk": 3.303855896
          }
        ]
      },
      {
        "benchmark_id": "7QUI_F9I",
        "target": "human Siglec-8 N-terminal domain",
        "ligand": "F9I sulfonamide sialoside analogue",
        "pdb_id": "7QUI",
        "role": "flexible glycomimetic challenge benchmark",
        "status": "needs_protocol_review",
        "seed_count": 1,
        "best_observed_rmsd_angstrom": 2.66899,
        "note": "Neither the baseline nor tighter-box trial met the predefined <2.0 A full-ligand RMSD criterion. Do not tune retrospectively to claim a pass."
      }
    ],
    "next_gate": {
      "name": "direct_siglec9_validation",
      "status": "in_progress_pending_independent_chemistry_and_interaction_review",
      "requirements": [
        "Independent carbohydrate-chemistry review of reconstructed BTCNeu5Ac and MTTSNeu5Ac structures",
        "Reproduction of the published Siglec-9 interaction constraints",
        "Matched multi-seed docking after chemistry sign-off",
        "Comparison with published affinity and interaction evidence"
      ]
    },
    "direct_target_assets": {
      "registry_path": "docking_inputs/structure_registry.json",
      "status": "reconstructed_ligand_coordinates_pending_independent_review",
      "ranking_unlocked": false,
      "receptor_review_status": "provisional_reconstruction",
      "receptor_p53_state": "cis",
      "verified_ligand_count": 0,
      "reconstructed_ligand_count": 2,
      "required_ligand_count": 2,
      "blocking_reasons": [
        "Exact author Siglec-9 model coordinates are not deposited with the article.",
        "The available AlphaFold reconstruction is canonical WT, while the reported NMR construct carried C36S.",
        "BTCNeu5Ac and MTTSNeu5Ac are literature-reconstructed rather than author-deposited coordinates and still require independent carbohydrate-chemistry review.",
        "NMR/MD interaction constraints have not yet been reproduced on this reconstruction."
      ]
    }
  },
  "a2a_curation": {
    "created_at": "2026-09-10T12:57:45.687575+00:00",
    "specification_id": "a2a-computational-curation-v1.3",
    "amendment_status": "prospective_amendment_before_new_label_admission_and_holdout_access",
    "source_hashes": {
      "config": "b57888fb1379a3971f0d8b4e7a604c4c6f9a00ebeae9d784fbc2862ed1b829c4",
      "frozen_plan_v1.2": "85aa30f9c2ee76c5cfe0530dce5ba4a1f203d9ba1dd70efed2ab1aeaf4ceb9ea",
      "evidence_packet": "0dfd133a0ecce7e5835d5bfe2ee5dae6ea5ad6d35d2617c6c1999b084d55a711",
      "standardized_structures": "ace1a1abc33ee83d97642df275035942044bcdb454cef951752e0863b15723f2",
      "raw_activity_snapshot": "244ad73210922157d6d02d99a514256e56c1961d2b8d36ed3b693beb4b74fa62"
    },
    "plan_record_count": 220,
    "decision_record_count": 220,
    "decision_counts": {
      "accept_agonist": 64,
      "accept_antagonist": 140,
      "needs_full_text": 4,
      "quarantine_excluded_function": 11,
      "reject_context": 1
    },
    "accepted_record_count": 204,
    "accepted_class_counts": {
      "agonist": 64,
      "antagonist": 140
    },
    "quarantined_or_rejected_count": 16,
    "raw_excluded_function_record_count": 11,
    "raw_excluded_function_classes": {
      "inverse_agonist": 24
    },
    "human_approval_required": false,
    "human_validation_claimed": false,
    "label_admission_uses_auc": false,
    "label_admission_uses_scaffold_agreement": false,
    "training_eligible_count": 0,
    "next_gate": "rebuild and hash scaffold-separated development and untouched holdout manifests from accepted computational labels"
  },
  "a2a_partitions": {
    "created_at": "2026-09-10T13:03:20.300590+00:00",
    "specification_id": "a2a-computational-partitions-v1.3",
    "manifest_sha256": "c87a21b8569e92c0a17c49f5add32341803110fd4f37342444ffc60f68fdd0f8",
    "accepted_record_count": 204,
    "partition_counts": {
      "development": 164,
      "locked_holdout": 40
    },
    "class_partition_counts": {
      "development:agonist": 51,
      "development:antagonist": 113,
      "locked_holdout:agonist": 13,
      "locked_holdout:antagonist": 27
    },
    "development_training_eligible_count": 163,
    "holdout_evaluation_eligible_count": 40,
    "missing_docking_ids": [
      "CHEMBL3414942"
    ],
    "development_scaffold_count": 160,
    "locked_holdout_scaffold_count": 40,
    "scaffold_overlap_count": 0,
    "membership_preserved_from_v1.2": true,
    "removed_from_frozen_population_count": 11,
    "removed_from_frozen_population_ids": [
      "CHEMBL113",
      "CHEMBL113142",
      "CHEMBL240624",
      "CHEMBL273094",
      "CHEMBL3904408",
      "CHEMBL4125975",
      "CHEMBL4126427",
      "CHEMBL4127213",
      "CHEMBL4159215",
      "CHEMBL4167557",
      "CHEMBL431770"
    ],
    "human_validation_claimed": false,
    "next_gate": "build the v1.3 computational feature matrix without accessing holdout outcomes"
  },
  "a2a_features": {
    "schema_version": 1,
    "created_at": "2026-09-10T13:08:35.650328+00:00",
    "protocol_id": "a2a-feature-construction-v1.3",
    "source_hashes": {
      "docking_report": "e7a25166a13def1c793e401c3f71f3fe859fbb22acbf5c1d870bcf2a77104d97",
      "partitions": "c87a21b8569e92c0a17c49f5add32341803110fd4f37342444ffc60f68fdd0f8",
      "evidence_review": "ea585972993a331d1f3bd44b5b0d2bd96027a3eb5d2c4605f1c3c07eb955b755",
      "standardized_chemistry": "ace1a1abc33ee83d97642df275035942044bcdb454cef951752e0863b15723f2"
    },
    "feature_matrix_sha256": "7c3997e7898481baa8e1fb2cf8e40995ef58260a130649625b87c1acbe921b88",
    "output_row_count": 203,
    "development_row_count": 163,
    "locked_holdout_row_count": 40,
    "class_counts": {
      "agonist": 63,
      "antagonist": 140
    },
    "partition_class_counts": {
      "development:agonist": 50,
      "development:antagonist": 113,
      "locked_holdout:agonist": 13,
      "locked_holdout:antagonist": 27
    },
    "missing_metadata_ids": [],
    "excluded_by_computational_curation_ids": [
      "CHEMBL113",
      "CHEMBL113142",
      "CHEMBL240624",
      "CHEMBL273094",
      "CHEMBL3904408",
      "CHEMBL4125975",
      "CHEMBL4126427",
      "CHEMBL4127213",
      "CHEMBL4159215",
      "CHEMBL4167557",
      "CHEMBL431770"
    ],
    "accepted_without_valid_docking_ids": [
      "CHEMBL3414942"
    ],
    "pose_quality": {
      "agonist": {
        "molecule_count": 63,
        "molecules_with_any_soft_flag": 31,
        "inactive_5NM4": {
          "flagged_seed_count": 63,
          "seed_count": 189,
          "flag_rate": 0.333333
        },
        "active_like_2YDO": {
          "flagged_seed_count": 27,
          "seed_count": 189,
          "flag_rate": 0.142857
        },
        "all_receptors": {
          "flagged_seed_count": 90,
          "seed_count": 378,
          "flag_rate": 0.238095
        }
      },
      "antagonist": {
        "molecule_count": 140,
        "molecules_with_any_soft_flag": 9,
        "inactive_5NM4": {
          "flagged_seed_count": 11,
          "seed_count": 420,
          "flag_rate": 0.02619
        },
        "active_like_2YDO": {
          "flagged_seed_count": 11,
          "seed_count": 420,
          "flag_rate": 0.02619
        },
        "all_receptors": {
          "flagged_seed_count": 22,
          "seed_count": 840,
          "flag_rate": 0.02619
        }
      }
    },
    "hard_filter_sensitivity_not_primary": {
      "agonist": {
        "unfiltered": 63,
        "all_six_seeds_pass": 32,
        "at_least_two_passing_seeds_per_receptor": 42,
        "at_least_one_passing_seed_per_receptor": 49
      },
      "antagonist": {
        "unfiltered": 140,
        "all_six_seeds_pass": 131,
        "at_least_two_passing_seeds_per_receptor": 135,
        "at_least_one_passing_seed_per_receptor": 137
      }
    },
    "scaffold_overlap_count": 0,
    "label_status": "computationally_adjudicated_functional",
    "human_approval_required": false,
    "human_validation_claimed": false,
    "holdout_accessed": false,
    "next_gate": "freeze development-only model settings, then perform one confirmatory evaluation on the locked holdout"
  },
  "a2a_confirmatory": {
    "schema_version": 1,
    "created_at": "2026-09-10T15:02:33.421554+00:00",
    "specification_id": "a2a-conformation-associated-cnn-signal-v1.3.1",
    "analysis_status": "one_time_locked_holdout_evaluation_complete",
    "freeze_manifest_sha256": "39e78626268f1fc7d17e52f03d4fa3d730d9b770a58b3b133fe1a4a2bd7ff234",
    "holdout_accessed": true,
    "holdout_record_count": 40,
    "holdout_agonists": 13,
    "holdout_antagonists": 27,
    "development_fitted_chemistry_variance_explained": 0.9485333335614485,
    "primary_confirmatory_endpoint": {
      "observed_coefficient": 1.0477268836180138,
      "alternative": "greater_than_zero",
      "resamples": 10000,
      "exceedances": 818,
      "one_sided_p_value": 0.08189181081891811,
      "success": false
    },
    "mandatory_sensitivity": {
      "pose_quality_correlation_d_pk_d_cnnscore": 0.7334213127947362,
      "joint_model_standardized_d_pk_coefficient": -115.4480335903875,
      "joint_model_standardized_d_cnnscore_coefficient": 280.8736040233806,
      "force_field_d_affinity": {
        "observed_coefficient": 0.0019354589034221033,
        "alternative": "greater_than_zero",
        "resamples": 2000,
        "exceedances": 1038,
        "one_sided_p_value": 0.519240379810095
      },
      "predictive_AB_vs_E": {
        "claim_status": "descriptive_only",
        "roc_auc_AB": 0.9886039886039886,
        "roc_auc_E": 0.9857549857549858,
        "delta_E_minus_AB": -0.002849002849002802
      }
    },
    "interpretation_boundary": "A positive holdout result supports a conformation-associated CNN scoring signal, not biological efficacy; external or experimental validation remains required.",
    "human_validation_claimed": false,
    "biological_efficacy_claimed": false
  }
};
