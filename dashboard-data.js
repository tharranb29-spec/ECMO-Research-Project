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
        "id": "auto_cd40_sirpa",
        "candidate_name": "CD40",
        "target_receptor": "SIRPa",
        "modality": "protein",
        "predicted_score": 44.0,
        "recommendation": "reject",
        "explanation": "strong affinity evidence, strong immunomodulation evidence, good target specificity.",
        "evidence_summary": "Recent literature mention in article: Phase Ib trial of SL-172154, a bispecific CD47 inhibitor and CD40 agonist Fc-fusion protein, in combination with mirvetuximab soravtansine or pegylated liposomal doxorubicin in patients with platinum-resistant ovarian cancer. (new literature lead, heuristic extraction)",
        "source_urls": [
          "https://europepmc.org/article/MED/41951722"
        ],
        "lead_score": 67,
        "discovery_status": "new_literature_lead",
        "publication_date": "2026-04-08",
        "source_title": "Phase Ib trial of SL-172154, a bispecific CD47 inhibitor and CD40 agonist Fc-fusion protein, in combination with mirvetuximab soravtansine or pegylated liposomal doxorubicin in patients with platinum-resistant ovarian cancer.",
        "source_method": "heuristic",
        "is_new": false,
        "translational_suitability_score": 44.0,
        "gnina": {
          "candidate_id": "auto_cd40_sirpa",
          "candidate_name": "CD40",
          "target_receptor": "SIRPa",
          "modality": "protein",
          "dockability": "unsupported_modality",
          "dockability_reason": "protein requires peptide or protein docking rather than GNINA.",
          "status": "unsupported_modality",
          "simulated": false
        },
        "gnina_rank": null,
        "ranking_basis": "gnina_not_scored"
      },
      {
        "id": "auto_fc-fusion_sirpa",
        "candidate_name": "Fc-fusion",
        "target_receptor": "SIRPa",
        "modality": "protein",
        "predicted_score": 44.0,
        "recommendation": "reject",
        "explanation": "strong affinity evidence, strong immunomodulation evidence, good target specificity.",
        "evidence_summary": "Recent literature mention in article: Phase Ib trial of SL-172154, a bispecific CD47 inhibitor and CD40 agonist Fc-fusion protein, in combination with mirvetuximab soravtansine or pegylated liposomal doxorubicin in patients with platinum-resistant ovarian cancer. (new literature lead, heuristic extraction)",
        "source_urls": [
          "https://europepmc.org/article/MED/41951722"
        ],
        "lead_score": 67,
        "discovery_status": "new_literature_lead",
        "publication_date": "2026-04-08",
        "source_title": "Phase Ib trial of SL-172154, a bispecific CD47 inhibitor and CD40 agonist Fc-fusion protein, in combination with mirvetuximab soravtansine or pegylated liposomal doxorubicin in patients with platinum-resistant ovarian cancer.",
        "source_method": "heuristic",
        "is_new": false,
        "translational_suitability_score": 44.0,
        "gnina": {
          "candidate_id": "auto_fc-fusion_sirpa",
          "candidate_name": "Fc-fusion",
          "target_receptor": "SIRPa",
          "modality": "protein",
          "dockability": "unsupported_modality",
          "dockability_reason": "protein requires peptide or protein docking rather than GNINA.",
          "status": "unsupported_modality",
          "simulated": false
        },
        "gnina_rank": null,
        "ranking_basis": "gnina_not_scored"
      },
      {
        "id": "auto_siglec-7_siglec9",
        "candidate_name": "Siglec-7",
        "target_receptor": "Siglec-9",
        "modality": "antibody",
        "predicted_score": 57.2,
        "recommendation": "hold",
        "explanation": "strong affinity evidence, strong immunomodulation evidence, good target specificity.",
        "evidence_summary": "Recent literature mention in article: Targeting ST3GAL1 to downregulate ligands for the glycoimmune checkpoint Siglec-7 and reverse immune escape in hepatocellular carcinoma. (new literature lead, heuristic extraction)",
        "source_urls": [
          "https://europepmc.org/article/MED/41961075"
        ],
        "lead_score": 74,
        "discovery_status": "new_literature_lead",
        "publication_date": "2026-04-10",
        "source_title": "Targeting ST3GAL1 to downregulate ligands for the glycoimmune checkpoint Siglec-7 and reverse immune escape in hepatocellular carcinoma.",
        "source_method": "heuristic",
        "is_new": true,
        "translational_suitability_score": 57.2,
        "gnina": {
          "candidate_id": "auto_siglec-7_siglec9",
          "candidate_name": "Siglec-7",
          "target_receptor": "Siglec-9",
          "modality": "antibody",
          "dockability": "unsupported_modality",
          "dockability_reason": "antibody requires peptide or protein docking rather than GNINA.",
          "status": "unsupported_modality",
          "simulated": false
        },
        "gnina_rank": null,
        "ranking_basis": "gnina_not_scored"
      },
      {
        "id": "auto_plac_siglec9",
        "candidate_name": "pLac",
        "target_receptor": "Siglec-9",
        "modality": "literature_lead",
        "predicted_score": 49.8,
        "recommendation": "reject",
        "explanation": "strong affinity evidence, strong immunomodulation evidence, good target specificity.",
        "evidence_summary": "Recent literature mention in article: Nociceptor neurons control pollution-mediated neutrophilic asthma. (known reference, heuristic extraction)",
        "source_urls": [
          "https://europepmc.org/article/MED/41891831"
        ],
        "lead_score": 60,
        "discovery_status": "known_reference",
        "publication_date": "2026-03-27",
        "source_title": "Nociceptor neurons control pollution-mediated neutrophilic asthma.",
        "source_method": "heuristic",
        "is_new": true,
        "translational_suitability_score": 49.8,
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
        "ranking_basis": "gnina_not_scored"
      }
    ],
    "docking_summary": {
      "last_updated": "2026-08-24T08:36:07.722767+00:00",
      "mode": "prototype",
      "simulated": true,
      "completed_count": 0,
      "candidate_count": 4,
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
    "last_updated": "2026-08-24T08:36:07.725833+00:00",
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
    "ranked": []
  },
  "research_leads": {
    "last_updated": "2026-04-15T06:50:34.791895+00:00",
    "leads": [
      {
        "candidate_name": "Siglec-7",
        "target_receptor": "Siglec-9",
        "modality_guess": "antibody",
        "lead_score": 74,
        "lead_type": "literature_candidate_lead",
        "rationale": "Recent literature mention in article: Targeting ST3GAL1 to downregulate ligands for the glycoimmune checkpoint Siglec-7 and reverse immune escape in hepatocellular carcinoma.",
        "publication_date": "2026-04-10",
        "source_title": "Targeting ST3GAL1 to downregulate ligands for the glycoimmune checkpoint Siglec-7 and reverse immune escape in hepatocellular carcinoma.",
        "source_url": "https://europepmc.org/article/MED/41961075",
        "article_id": "41961075",
        "source_method": "heuristic",
        "is_new": true
      },
      {
        "candidate_name": "CD40",
        "target_receptor": "SIRPa",
        "modality_guess": "protein",
        "lead_score": 67,
        "lead_type": "literature_candidate_lead",
        "rationale": "Recent literature mention in article: Phase Ib trial of SL-172154, a bispecific CD47 inhibitor and CD40 agonist Fc-fusion protein, in combination with mirvetuximab soravtansine or pegylated liposomal doxorubicin in patients with platinum-resistant ovarian cancer.",
        "publication_date": "2026-04-08",
        "source_title": "Phase Ib trial of SL-172154, a bispecific CD47 inhibitor and CD40 agonist Fc-fusion protein, in combination with mirvetuximab soravtansine or pegylated liposomal doxorubicin in patients with platinum-resistant ovarian cancer.",
        "source_url": "https://europepmc.org/article/MED/41951722",
        "article_id": "41951722",
        "source_method": "heuristic",
        "is_new": false
      },
      {
        "candidate_name": "Fc-fusion",
        "target_receptor": "SIRPa",
        "modality_guess": "protein",
        "lead_score": 67,
        "lead_type": "literature_candidate_lead",
        "rationale": "Recent literature mention in article: Phase Ib trial of SL-172154, a bispecific CD47 inhibitor and CD40 agonist Fc-fusion protein, in combination with mirvetuximab soravtansine or pegylated liposomal doxorubicin in patients with platinum-resistant ovarian cancer.",
        "publication_date": "2026-04-08",
        "source_title": "Phase Ib trial of SL-172154, a bispecific CD47 inhibitor and CD40 agonist Fc-fusion protein, in combination with mirvetuximab soravtansine or pegylated liposomal doxorubicin in patients with platinum-resistant ovarian cancer.",
        "source_url": "https://europepmc.org/article/MED/41951722",
        "article_id": "41951722",
        "source_method": "heuristic",
        "is_new": false
      },
      {
        "candidate_name": "pLac",
        "target_receptor": "Siglec-9",
        "modality_guess": "literature_lead",
        "lead_score": 60,
        "lead_type": "literature_candidate_lead",
        "rationale": "Recent literature mention in article: Nociceptor neurons control pollution-mediated neutrophilic asthma.",
        "publication_date": "2026-03-27",
        "source_title": "Nociceptor neurons control pollution-mediated neutrophilic asthma.",
        "source_url": "https://europepmc.org/article/MED/41891831",
        "article_id": "41891831",
        "source_method": "heuristic",
        "is_new": true
      }
    ]
  },
  "research_status": {
    "last_updated": "2026-04-15T06:50:34.791895+00:00",
    "last_attempted_at": "2026-04-15T10:34:51.353154+00:00",
    "last_successful_data_at": "2026-04-15T06:50:34.791895+00:00",
    "article_count": 77,
    "relevant_article_count": 41,
    "new_article_count": 0,
    "lead_count": 4,
    "new_lead_count": 0,
    "autonomous_ranked_count": 4,
    "promoted_count": 0,
    "heuristic_lead_count": 4,
    "llm_lead_count": 0,
    "llm_enabled": false,
    "llm_provider": null,
    "query_results": [
      {
        "target_receptor": "Siglec-9",
        "ok": false,
        "error": "[Errno 61] Connection refused"
      },
      {
        "target_receptor": "Siglec-9",
        "ok": false,
        "error": "[Errno 61] Connection refused"
      },
      {
        "target_receptor": "SIRPa",
        "ok": false,
        "error": "[Errno 61] Connection refused"
      },
      {
        "target_receptor": "SIRPa",
        "ok": false,
        "error": "[Errno 61] Connection refused"
      }
    ],
    "errors": [
      "Siglec-9: Europe PMC network error - [Errno 61] Connection refused",
      "Siglec-9: Europe PMC network error - [Errno 61] Connection refused",
      "SIRPa: Europe PMC network error - [Errno 61] Connection refused",
      "SIRPa: Europe PMC network error - [Errno 61] Connection refused"
    ],
    "health": "warning",
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
    "new_article_titles": [],
    "new_lead_names": [],
    "using_cached_results": true
  },
  "research_runtime": {
    "in_progress": false,
    "last_started_at": "2026-04-15T10:34:51.286711+00:00",
    "last_finished_at": "2026-04-15T10:34:51.356551+00:00",
    "last_success_at": "2026-04-15T06:50:34.791895+00:00",
    "last_error": "Siglec-9: Europe PMC network error - [Errno 61] Connection refused | Siglec-9: Europe PMC network error - [Errno 61] Connection refused | SIRPa: Europe PMC network error - [Errno 61] Connection refused",
    "last_trigger": "scheduled",
    "next_run_at": "2026-04-15T11:34:51.356556+00:00",
    "interval_seconds": 3600,
    "llm_enabled": false,
    "llm_provider": null,
    "auto_research_enabled": true
  },
  "gnina_results": {
    "last_updated": "2026-08-24T08:36:07.722767+00:00",
    "started_at": "2026-08-24T08:36:07.722168+00:00",
    "mode": "prototype",
    "simulated": true,
    "scientific_status": "workflow_demonstration_only",
    "target_validation_ready": false,
    "validation_status": "partial_validation",
    "candidate_count": 4,
    "completed_count": 0,
    "status_counts": {
      "unsupported_modality": 4
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
      "interpretation": "Exploratory rank validation only; five compounds are insufficient for a general performance claim."
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
        "candidate_id": "auto_siglec-7_siglec9",
        "candidate_name": "Siglec-7",
        "target_receptor": "Siglec-9",
        "modality": "antibody",
        "dockability": "unsupported_modality",
        "dockability_reason": "antibody requires peptide or protein docking rather than GNINA.",
        "status": "unsupported_modality",
        "simulated": false
      },
      {
        "candidate_id": "auto_cd40_sirpa",
        "candidate_name": "CD40",
        "target_receptor": "SIRPa",
        "modality": "protein",
        "dockability": "unsupported_modality",
        "dockability_reason": "protein requires peptide or protein docking rather than GNINA.",
        "status": "unsupported_modality",
        "simulated": false
      },
      {
        "candidate_id": "auto_fc-fusion_sirpa",
        "candidate_name": "Fc-fusion",
        "target_receptor": "SIRPa",
        "modality": "protein",
        "dockability": "unsupported_modality",
        "dockability_reason": "protein requires peptide or protein docking rather than GNINA.",
        "status": "unsupported_modality",
        "simulated": false
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
      }
    ]
  },
  "gnina_status": {
    "last_updated": "2026-08-24T08:36:07.722767+00:00",
    "started_at": "2026-08-24T08:36:07.722168+00:00",
    "mode": "prototype",
    "simulated": true,
    "scientific_status": "workflow_demonstration_only",
    "target_validation_ready": false,
    "validation_status": "partial_validation",
    "candidate_count": 4,
    "completed_count": 0,
    "status_counts": {
      "unsupported_modality": 4
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
      "interpretation": "Exploratory rank validation only; five compounds are insufficient for a general performance claim."
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
    "last_updated": "2026-08-23T16:25:06.777124+00:00",
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
      "status": "in_progress_blocked_on_verified_ligand_coordinates",
      "requirements": [
        "Reviewed Siglec-9 receptor model matching the published modeling strategy",
        "Verified BTCNeu5Ac and MTTSNeu5Ac structures with provenance",
        "Five-seed docking with uncertainty reporting",
        "Comparison with published affinity and interaction evidence"
      ]
    },
    "direct_target_assets": {
      "registry_path": "docking_inputs/structure_registry.json",
      "status": "receptor_reconstruction_pending_ligand_coordinates",
      "ranking_unlocked": false,
      "receptor_review_status": "provisional_reconstruction",
      "receptor_p53_state": "cis",
      "verified_ligand_count": 0,
      "required_ligand_count": 2,
      "blocking_reasons": [
        "Exact author Siglec-9 model coordinates are not deposited with the article.",
        "The available AlphaFold reconstruction is canonical WT, while the reported NMR construct carried C36S.",
        "Verified stereochemically complete BTCNeu5Ac and MTTSNeu5Ac 3D files are not yet available locally.",
        "NMR/MD interaction constraints have not yet been reproduced on this reconstruction."
      ]
    }
  }
};
