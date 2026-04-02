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
  "autonomous": null,
  "research_leads": {
    "last_updated": "2026-04-02T05:37:22.467771+00:00",
    "leads": [
      {
        "candidate_name": "STING",
        "target_receptor": "SIRPa",
        "modality_guess": "antibody",
        "lead_score": 50,
        "lead_type": "literature_candidate_lead",
        "rationale": "Recent literature mention in article: Dual-Functional Anti-SIRP\u03b1-cGAMP Conjugate Reprograms the Tumor Immune Microenvironment and Enhances Antitumor Immunity.",
        "publication_date": "2026-04-01",
        "source_title": "Dual-Functional Anti-SIRP\u03b1-cGAMP Conjugate Reprograms the Tumor Immune Microenvironment and Enhances Antitumor Immunity.",
        "source_url": "https://europepmc.org/article/MED/41918375"
      }
    ]
  },
  "research_status": {
    "last_updated": "2026-04-02T05:37:22.467771+00:00",
    "article_count": 30,
    "lead_count": 1,
    "queries": [
      {
        "target_receptor": "Siglec-9",
        "query": "(Siglec-9 OR SIGLEC9) AND (ligand OR glycomimetic OR agonist OR peptide OR sialoside) sort_date:y"
      },
      {
        "target_receptor": "SIRPa",
        "query": "(\"SIRPalpha\" OR \"SIRPa\" OR \"SIRP\u03b1\" OR CD47) AND (ligand OR mimetic OR peptide OR variant OR agonist) sort_date:y"
      }
    ]
  }
};
