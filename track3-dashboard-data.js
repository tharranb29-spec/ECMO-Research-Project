window.A2A_DASHBOARD_DATA = {
  "contracts": {
    "applicability_uncertainty": {
      "contract_version": "1.0.0",
      "records": [
        {
          "assessment_id": "pBind_Ki:AB_Ridge:development-v1.6",
          "calibration_warning": "Empirical interval coverage is development-only and is not an external calibration claim.",
          "descriptor_distance_threshold": 7.595001386539151,
          "external_thresholds_frozen": false,
          "inside_n": 74,
          "model_id": "AB_Ridge",
          "outside_n": 4,
          "r2_interval": {
            "estimate": 0.552653734355324,
            "lower": 0.4396435513343424,
            "upper": 0.6487845133745116
          },
          "scope": "development grouped out-of-fold predictions",
          "similarity_threshold": 0.25,
          "source": {
            "path": "outputs/v1.6/model_reproduction/development_results.json",
            "sha256": "c7ab76ca99cd79ee3dc37b1028a9fcf0933253e3d3dd226969189103902384db"
          }
        }
      ],
      "schema_id": "a2a-dashboard.applicability-uncertainty.v1"
    },
    "audit_log": {
      "contract_version": "1.0.0",
      "records": [
        {
          "action": "protocol-freeze",
          "actor": "repository-artifact-ingest",
          "entry_hash": "0a299f40f802f969f31919dd9e54dc7fad58ffc4e2738137a01d78f387d6e8d1",
          "event_id": "audit-0001",
          "previous_entry_hash": "GENESIS",
          "record_id": "a2a-track3-protocol-v1.6",
          "record_type": "protocol",
          "sequence": 1,
          "source": {
            "path": "outputs/v1.6/protocol_freeze_manifest.json",
            "sha256": "446e9f5e38c26360b710ee5a842cbb907989455f70814cf1bef4bdeb8d2ac9ce"
          }
        },
        {
          "action": "evidence-pass1",
          "actor": "repository-artifact-ingest",
          "entry_hash": "3d6a6013b668b3321e71a624de99c4f4137485ca82ba1442cb0fc90f2da7fe5d",
          "event_id": "audit-0002",
          "previous_entry_hash": "0a299f40f802f969f31919dd9e54dc7fad58ffc4e2738137a01d78f387d6e8d1",
          "record_id": "external-pass-1",
          "record_type": "evidence_inbox",
          "sequence": 2,
          "source": {
            "path": "outputs/v1.6/external_evidence/pass1_metadata_preflight/pass1_metadata_preflight_audit.json",
            "sha256": "9536bc10e09888512cc37ccec1539506bc6f2908589d59a1964a1dc6a54b5867"
          }
        },
        {
          "action": "evidence-pass2-freeze",
          "actor": "repository-artifact-ingest",
          "entry_hash": "0719147cbbe561bb0b5f7e59724fc4d683ca8f05fff4f35cccc5937e43122f98",
          "event_id": "audit-0003",
          "previous_entry_hash": "3d6a6013b668b3321e71a624de99c4f4137485ca82ba1442cb0fc90f2da7fe5d",
          "record_id": "a2a-external-cohort-membership-freeze-v1.6",
          "record_type": "evidence_inbox",
          "sequence": 3,
          "source": {
            "path": "outputs/v1.6/external_evidence/pass2_source_extraction/cohort_freeze_manifest.json",
            "sha256": "89d6a1ddd8ba4f2960a63df11713cc34ce505eb99a30c2376a9fa411a2f99cf0"
          }
        },
        {
          "action": "model-reproduction",
          "actor": "repository-artifact-ingest",
          "entry_hash": "db545a5a035fea94dcdb5035246c06951fdeed17a7125ff06a376a16ccb69280",
          "event_id": "audit-0004",
          "previous_entry_hash": "0719147cbbe561bb0b5f7e59724fc4d683ca8f05fff4f35cccc5937e43122f98",
          "record_id": "pBind_Ki-development",
          "record_type": "model_registry",
          "sequence": 4,
          "source": {
            "path": "outputs/v1.6/model_reproduction/development_results.json",
            "sha256": "c7ab76ca99cd79ee3dc37b1028a9fcf0933253e3d3dd226969189103902384db"
          }
        },
        {
          "action": "prospective-docking",
          "actor": "repository-artifact-ingest",
          "entry_hash": "da7cdd46323f52235e2b4901fb6b497d0cbb66462a741937c8c371a6450bf07b",
          "event_id": "audit-0005",
          "previous_entry_hash": "db545a5a035fea94dcdb5035246c06951fdeed17a7125ff06a376a16ccb69280",
          "record_id": "a2a-external-validation-v1.4",
          "record_type": "dual_state_docking",
          "sequence": 5,
          "source": {
            "path": "outputs/v1.4/docking/literature_pilot_2025_report.json",
            "sha256": "2f34dbd781a1221ab3c7cd9215cef755b3d8b5974205b83c984b19ad74a50d17"
          }
        },
        {
          "action": "md-gate",
          "actor": "repository-artifact-ingest",
          "entry_hash": "a6645c01c2829e82fd9c28dc49c1f7b93d1fb8ded2285a787839a13d67b2ce8d",
          "event_id": "audit-0006",
          "previous_entry_hash": "da7cdd46323f52235e2b4901fb6b497d0cbb66462a741937c8c371a6450bf07b",
          "record_id": "a2a-tier-a-equilibration-gate-v1.6.4",
          "record_type": "md_gates",
          "sequence": 6,
          "source": {
            "path": "outputs/v1.6/md/tier_a_equilibration/equilibration_gate_report.json",
            "sha256": "9f5e377c4a2ca6754a710d491f520edee7663b432d147a90584dbcb4f555fd11"
          }
        },
        {
          "action": "md-production-authorized",
          "actor": "repository-artifact-ingest",
          "entry_hash": "03acdd1fc40b9061f3bee507c0f667c1421dcb49ae2b1144ae82ef59bc23f387",
          "event_id": "audit-0007",
          "previous_entry_hash": "a6645c01c2829e82fd9c28dc49c1f7b93d1fb8ded2285a787839a13d67b2ce8d",
          "record_id": "a2a-md-production-v1.6",
          "record_type": "md_gates",
          "sequence": 7,
          "source": {
            "path": "config/md_production.v1.6.json",
            "sha256": "21d6a5c2332bf9379b21ee04999eb31261bed7ed5d1dfd5e6ad510490a011e07"
          }
        },
        {
          "action": "shadow-policy",
          "actor": "repository-artifact-ingest",
          "entry_hash": "2714619893f22c5af6ee1a604587950b6457baa3c300f8417492e263d0953c37",
          "event_id": "audit-0008",
          "previous_entry_hash": "03acdd1fc40b9061f3bee507c0f667c1421dcb49ae2b1144ae82ef59bc23f387",
          "record_id": "a2a-shadow-update-v1.4",
          "record_type": "promotion",
          "sequence": 8,
          "source": {
            "path": "config/shadow_update.v1.4.json",
            "sha256": "b48669165f967039449f9965b90ac8159a5b62890297e98c8690516a3cace908"
          }
        }
      ],
      "schema_id": "a2a-dashboard.audit-log.v1"
    },
    "candidate_portfolio": {
      "contract_version": "1.0.0",
      "records": [
        {
          "d_affinity_kcal_mol": 0.0684,
          "dual_state_complete": true,
          "label_status": "blinded",
          "md_status": "tier_b_locked",
          "molecule_id": "LIT25-MET-PGD2",
          "next_gate": "Not promotable under v1.6: external floors failed and Tier B remains locked.",
          "portfolio_id": "portfolio:LIT25-MET-PGD2",
          "promotion_status": "shadow_proposal",
          "source": {
            "path": "outputs/v1.4/docking/literature_pilot_2025_report.json",
            "sha256": "2f34dbd781a1221ab3c7cd9215cef755b3d8b5974205b83c984b19ad74a50d17"
          },
          "status": "computationally_prioritized"
        },
        {
          "d_affinity_kcal_mol": -0.4107,
          "dual_state_complete": true,
          "label_status": "blinded",
          "md_status": "tier_b_locked",
          "molecule_id": "LIT25-RL-C5",
          "next_gate": "Not promotable under v1.6: external floors failed and Tier B remains locked.",
          "portfolio_id": "portfolio:LIT25-RL-C5",
          "promotion_status": "shadow_proposal",
          "source": {
            "path": "outputs/v1.4/docking/literature_pilot_2025_report.json",
            "sha256": "2f34dbd781a1221ab3c7cd9215cef755b3d8b5974205b83c984b19ad74a50d17"
          },
          "status": "computationally_prioritized"
        },
        {
          "d_affinity_kcal_mol": 0.5118,
          "dual_state_complete": true,
          "label_status": "blinded",
          "md_status": "tier_b_locked",
          "molecule_id": "LIT25-RL-C7",
          "next_gate": "Not promotable under v1.6: external floors failed and Tier B remains locked.",
          "portfolio_id": "portfolio:LIT25-RL-C7",
          "promotion_status": "shadow_proposal",
          "source": {
            "path": "outputs/v1.4/docking/literature_pilot_2025_report.json",
            "sha256": "2f34dbd781a1221ab3c7cd9215cef755b3d8b5974205b83c984b19ad74a50d17"
          },
          "status": "computationally_prioritized"
        },
        {
          "d_affinity_kcal_mol": 0.7303,
          "dual_state_complete": true,
          "label_status": "blinded",
          "md_status": "tier_b_locked",
          "molecule_id": "LIT25-RL-C9",
          "next_gate": "Not promotable under v1.6: external floors failed and Tier B remains locked.",
          "portfolio_id": "portfolio:LIT25-RL-C9",
          "promotion_status": "shadow_proposal",
          "source": {
            "path": "outputs/v1.4/docking/literature_pilot_2025_report.json",
            "sha256": "2f34dbd781a1221ab3c7cd9215cef755b3d8b5974205b83c984b19ad74a50d17"
          },
          "status": "computationally_prioritized"
        }
      ],
      "schema_id": "a2a-dashboard.candidate-portfolio.v1"
    },
    "dual_state_docking": {
      "contract_version": "1.0.0",
      "records": [
        {
          "claim_limit": "Computational docking evidence; not measured affinity or functional activity.",
          "docking_id": "LIT25-MET-PGD2:5NM4",
          "median_affinity_kcal_mol": -7.1291,
          "median_cnn_score": 0.5859,
          "molecule_id": "LIT25-MET-PGD2",
          "receptor_id": "5NM4",
          "receptor_state": "inactive",
          "retained_pose_sha256": "cb4ed5dd1f12a71a52ebc90585c2789af30066b3f1f9731e7d3dfcf9873b6b46",
          "source": {
            "path": "outputs/v1.4/docking/literature_pilot_2025_report.json",
            "sha256": "2f34dbd781a1221ab3c7cd9215cef755b3d8b5974205b83c984b19ad74a50d17"
          },
          "status": "valid",
          "valid_seed_count": 3
        },
        {
          "claim_limit": "Computational docking evidence; not measured affinity or functional activity.",
          "docking_id": "LIT25-MET-PGD2:2YDO",
          "median_affinity_kcal_mol": -7.0607,
          "median_cnn_score": 0.7386,
          "molecule_id": "LIT25-MET-PGD2",
          "receptor_id": "2YDO",
          "receptor_state": "active-like",
          "retained_pose_sha256": "ab2f616cd8212db94ccbc834fd7234db1167b104db20587a03ba89034d775cf2",
          "source": {
            "path": "outputs/v1.4/docking/literature_pilot_2025_report.json",
            "sha256": "2f34dbd781a1221ab3c7cd9215cef755b3d8b5974205b83c984b19ad74a50d17"
          },
          "status": "valid",
          "valid_seed_count": 3
        },
        {
          "claim_limit": "Computational docking evidence; not measured affinity or functional activity.",
          "docking_id": "LIT25-RL-C5:5NM4",
          "median_affinity_kcal_mol": -9.6379,
          "median_cnn_score": 0.9373,
          "molecule_id": "LIT25-RL-C5",
          "receptor_id": "5NM4",
          "receptor_state": "inactive",
          "retained_pose_sha256": "eef82e4467fe43ce48c8a49dfb12d6736809d99e03c51027317e19d7233b3aa0",
          "source": {
            "path": "outputs/v1.4/docking/literature_pilot_2025_report.json",
            "sha256": "2f34dbd781a1221ab3c7cd9215cef755b3d8b5974205b83c984b19ad74a50d17"
          },
          "status": "valid",
          "valid_seed_count": 3
        },
        {
          "claim_limit": "Computational docking evidence; not measured affinity or functional activity.",
          "docking_id": "LIT25-RL-C5:2YDO",
          "median_affinity_kcal_mol": -10.0486,
          "median_cnn_score": 0.9171,
          "molecule_id": "LIT25-RL-C5",
          "receptor_id": "2YDO",
          "receptor_state": "active-like",
          "retained_pose_sha256": "4c83f630af89935a0757ba91c7e60ece4ac058407c440a6f35b1e0e5aea65a5d",
          "source": {
            "path": "outputs/v1.4/docking/literature_pilot_2025_report.json",
            "sha256": "2f34dbd781a1221ab3c7cd9215cef755b3d8b5974205b83c984b19ad74a50d17"
          },
          "status": "valid",
          "valid_seed_count": 3
        },
        {
          "claim_limit": "Computational docking evidence; not measured affinity or functional activity.",
          "docking_id": "LIT25-RL-C7:5NM4",
          "median_affinity_kcal_mol": -9.9848,
          "median_cnn_score": 0.9685,
          "molecule_id": "LIT25-RL-C7",
          "receptor_id": "5NM4",
          "receptor_state": "inactive",
          "retained_pose_sha256": "6b420e87e04ab119b58397408b35d7d506071bcfc62d0352459ea7a447351c34",
          "source": {
            "path": "outputs/v1.4/docking/literature_pilot_2025_report.json",
            "sha256": "2f34dbd781a1221ab3c7cd9215cef755b3d8b5974205b83c984b19ad74a50d17"
          },
          "status": "valid",
          "valid_seed_count": 3
        },
        {
          "claim_limit": "Computational docking evidence; not measured affinity or functional activity.",
          "docking_id": "LIT25-RL-C7:2YDO",
          "median_affinity_kcal_mol": -9.473,
          "median_cnn_score": 0.9553,
          "molecule_id": "LIT25-RL-C7",
          "receptor_id": "2YDO",
          "receptor_state": "active-like",
          "retained_pose_sha256": "75e9cad3a1e9e90f8a0920aaa8d5169010269752b02aeaad242ff34621254db5",
          "source": {
            "path": "outputs/v1.4/docking/literature_pilot_2025_report.json",
            "sha256": "2f34dbd781a1221ab3c7cd9215cef755b3d8b5974205b83c984b19ad74a50d17"
          },
          "status": "valid",
          "valid_seed_count": 3
        },
        {
          "claim_limit": "Computational docking evidence; not measured affinity or functional activity.",
          "docking_id": "LIT25-RL-C9:5NM4",
          "median_affinity_kcal_mol": -9.5699,
          "median_cnn_score": 0.97,
          "molecule_id": "LIT25-RL-C9",
          "receptor_id": "5NM4",
          "receptor_state": "inactive",
          "retained_pose_sha256": "b658fe15e11501aa691fedb3119391d445f5c4b09cb553fab938104d72f85991",
          "source": {
            "path": "outputs/v1.4/docking/literature_pilot_2025_report.json",
            "sha256": "2f34dbd781a1221ab3c7cd9215cef755b3d8b5974205b83c984b19ad74a50d17"
          },
          "status": "valid",
          "valid_seed_count": 3
        },
        {
          "claim_limit": "Computational docking evidence; not measured affinity or functional activity.",
          "docking_id": "LIT25-RL-C9:2YDO",
          "median_affinity_kcal_mol": -8.8396,
          "median_cnn_score": 0.8326,
          "molecule_id": "LIT25-RL-C9",
          "receptor_id": "2YDO",
          "receptor_state": "active-like",
          "retained_pose_sha256": "5456dd456a4e4a0274291b19c8d410845cb2f1ead3ef3e9cd0de7afd27b041de",
          "source": {
            "path": "outputs/v1.4/docking/literature_pilot_2025_report.json",
            "sha256": "2f34dbd781a1221ab3c7cd9215cef755b3d8b5974205b83c984b19ad74a50d17"
          },
          "status": "valid",
          "valid_seed_count": 3
        }
      ],
      "schema_id": "a2a-dashboard.dual-state-docking.v1"
    },
    "evidence_inbox": {
      "contract_version": "1.0.0",
      "records": [
        {
          "count": 1,
          "disposition": "review",
          "membership_frozen": true,
          "outcome_fields_loaded": false,
          "record_id": "evidence-lane:metadata_pass_doi_only_needs_source_retrieval",
          "source": {
            "path": "outputs/v1.6/external_evidence/pass1_metadata_preflight/pass1_metadata_preflight_audit.json",
            "sha256": "9536bc10e09888512cc37ccec1539506bc6f2908589d59a1964a1dc6a54b5867"
          },
          "stage": "pass_1_historical",
          "status": "metadata_pass_doi_only_needs_source_retrieval",
          "title": "DOI-only retrieval"
        },
        {
          "count": 24,
          "disposition": "review",
          "membership_frozen": true,
          "outcome_fields_loaded": false,
          "record_id": "evidence-lane:metadata_pass_fulltext_ready",
          "source": {
            "path": "outputs/v1.6/external_evidence/pass1_metadata_preflight/pass1_metadata_preflight_audit.json",
            "sha256": "9536bc10e09888512cc37ccec1539506bc6f2908589d59a1964a1dc6a54b5867"
          },
          "stage": "pass_1_historical",
          "status": "metadata_pass_fulltext_ready",
          "title": "Full text ready"
        },
        {
          "count": 131,
          "disposition": "review",
          "membership_frozen": true,
          "outcome_fields_loaded": false,
          "record_id": "evidence-lane:metadata_pass_needs_fulltext",
          "source": {
            "path": "outputs/v1.6/external_evidence/pass1_metadata_preflight/pass1_metadata_preflight_audit.json",
            "sha256": "9536bc10e09888512cc37ccec1539506bc6f2908589d59a1964a1dc6a54b5867"
          },
          "stage": "pass_1_historical",
          "status": "metadata_pass_needs_fulltext",
          "title": "Needs source text"
        },
        {
          "count": 31,
          "disposition": "review",
          "membership_frozen": true,
          "outcome_fields_loaded": false,
          "record_id": "evidence-lane:metadata_pass_requires_endpoint_resolution",
          "source": {
            "path": "outputs/v1.6/external_evidence/pass1_metadata_preflight/pass1_metadata_preflight_audit.json",
            "sha256": "9536bc10e09888512cc37ccec1539506bc6f2908589d59a1964a1dc6a54b5867"
          },
          "stage": "pass_1_historical",
          "status": "metadata_pass_requires_endpoint_resolution",
          "title": "Endpoint resolution"
        },
        {
          "count": 7,
          "disposition": "quarantined",
          "membership_frozen": true,
          "outcome_fields_loaded": false,
          "record_id": "evidence-lane:quarantine_nonprimary_source",
          "source": {
            "path": "outputs/v1.6/external_evidence/pass1_metadata_preflight/pass1_metadata_preflight_audit.json",
            "sha256": "9536bc10e09888512cc37ccec1539506bc6f2908589d59a1964a1dc6a54b5867"
          },
          "stage": "pass_1_historical",
          "status": "quarantine_nonprimary_source",
          "title": "Non-primary source"
        },
        {
          "count": 46,
          "disposition": "quarantined",
          "membership_frozen": true,
          "outcome_fields_loaded": false,
          "record_id": "evidence-lane:quarantine_target_not_supported",
          "source": {
            "path": "outputs/v1.6/external_evidence/pass1_metadata_preflight/pass1_metadata_preflight_audit.json",
            "sha256": "9536bc10e09888512cc37ccec1539506bc6f2908589d59a1964a1dc6a54b5867"
          },
          "stage": "pass_1_historical",
          "status": "quarantine_target_not_supported",
          "title": "A2A not supported"
        },
        {
          "count": 29,
          "disposition": "reviewed",
          "membership_frozen": true,
          "outcome_fields_loaded": false,
          "record_id": "evidence-stage:pass-2-source-grounded",
          "source": {
            "path": "outputs/v1.6/external_evidence/pass2_source_extraction/pass2_source_extraction_audit.json",
            "sha256": "f46828a0a569fdec47f265ec815fe51214878f37852e60bf9924a48af809b9d5"
          },
          "stage": "pass_2_frozen",
          "status": "pass_2_source_grounded",
          "title": "Source-grounded in pass 2"
        },
        {
          "count": 0,
          "disposition": "blocked",
          "membership_frozen": true,
          "outcome_fields_loaded": false,
          "record_id": "evidence-stage:admitted",
          "source": {
            "path": "outputs/v1.6/external_evidence/pass2_source_extraction/cohort_freeze_manifest.json",
            "sha256": "89d6a1ddd8ba4f2960a63df11713cc34ce505eb99a30c2376a9fa411a2f99cf0"
          },
          "stage": "cohort_freeze",
          "status": "frozen_floor_failure",
          "title": "Admitted to external cohort"
        }
      ],
      "schema_id": "a2a-dashboard.evidence-inbox.v1"
    },
    "md_gates": {
      "contract_version": "1.0.0",
      "records": [
        {
          "claim_limit": "This gate authorizes Tier A pilot production; it does not establish control stability or unlock Tier B.",
          "gate_id": "G7:tier-a-equilibration",
          "missing_audits": [],
          "observed_runs": 6,
          "passed_runs": 6,
          "required_runs": 6,
          "source": {
            "path": "outputs/v1.6/md/tier_a_equilibration/equilibration_gate_report.json",
            "sha256": "9f5e377c4a2ca6754a710d491f520edee7663b432d147a90584dbcb4f555fd11"
          },
          "specification_id": "a2a-tier-a-equilibration-gate-v1.6.4",
          "status": "tier_a_equilibration_gate_passed",
          "tier_a_production_unlocked": true,
          "tier_b_unlocked": false
        },
        {
          "claim_limit": "The pilot tests short-timescale pose stability. It is not a convergence, affinity, efficacy, or experimental-validation claim.",
          "gate_id": "G7:tier-a-production",
          "missing_audits": [],
          "observed_runs": 0,
          "passed_runs": 0,
          "required_runs": 6,
          "source": {
            "path": "config/md_production.v1.6.json",
            "sha256": "21d6a5c2332bf9379b21ee04999eb31261bed7ed5d1dfd5e6ad510490a011e07"
          },
          "specification_id": "a2a-md-production-v1.6",
          "status": "authorized_not_started",
          "tier_a_production_unlocked": true,
          "tier_b_unlocked": false
        },
        {
          "claim_limit": "Candidate MD cannot start until both Tier A native controls pass the frozen production rule.",
          "gate_id": "G8:candidate-md",
          "missing_audits": [],
          "observed_runs": 0,
          "passed_runs": 0,
          "required_runs": 24,
          "source": {
            "path": "outputs/v1.5/md/preflight_status.json",
            "sha256": "50c4d49deae777f47efdc55bac27440ddc945fe5d8af539d1e899bbb5d6a2ea8"
          },
          "specification_id": "a2a-tier-a-equilibration-gate-v1.6.4",
          "status": "locked",
          "tier_a_production_unlocked": true,
          "tier_b_unlocked": false
        }
      ],
      "schema_id": "a2a-dashboard.md-gates.v1"
    },
    "model_registry": {
      "contract_version": "1.0.0",
      "records": [
        {
          "development_n": 78,
          "display_name": "training-development mean pBind_Ki",
          "endpoint": "pBind_Ki",
          "external_outcomes_loaded": false,
          "lifecycle_status": "candidate_not_served",
          "mae": 0.9849072084268139,
          "model_id": "Mean",
          "promotion_allowed": false,
          "r2": -0.037004677818093024,
          "rmse": 1.165203074140081,
          "role": "development comparator",
          "scaffold_count": 68,
          "source": {
            "path": "outputs/v1.6/model_reproduction/development_results.json",
            "sha256": "c7ab76ca99cd79ee3dc37b1028a9fcf0933253e3d3dd226969189103902384db"
          }
        },
        {
          "development_n": 78,
          "display_name": "AB_Ridge",
          "endpoint": "pBind_Ki",
          "external_outcomes_loaded": false,
          "lifecycle_status": "candidate_not_served",
          "mae": 0.6154408512881633,
          "model_id": "AB_Ridge",
          "promotion_allowed": false,
          "r2": 0.5605377886314917,
          "rmse": 0.7585287258909658,
          "role": "primary external predictor",
          "scaffold_count": 68,
          "source": {
            "path": "outputs/v1.6/model_reproduction/development_results.json",
            "sha256": "c7ab76ca99cd79ee3dc37b1028a9fcf0933253e3d3dd226969189103902384db"
          }
        },
        {
          "development_n": 78,
          "display_name": "AB_RF_500_sqrt_1",
          "endpoint": "pBind_Ki",
          "external_outcomes_loaded": false,
          "lifecycle_status": "candidate_not_served",
          "mae": 0.672131599959301,
          "model_id": "AB_RF",
          "promotion_allowed": false,
          "r2": 0.5027539353878119,
          "rmse": 0.8068576878008816,
          "role": "development comparator",
          "scaffold_count": 68,
          "source": {
            "path": "outputs/v1.6/model_reproduction/development_results.json",
            "sha256": "c7ab76ca99cd79ee3dc37b1028a9fcf0933253e3d3dd226969189103902384db"
          }
        },
        {
          "development_n": 78,
          "display_name": "E_RF_500_sqrt_1",
          "endpoint": "pBind_Ki",
          "external_outcomes_loaded": false,
          "lifecycle_status": "candidate_not_served",
          "mae": 0.6909425643467652,
          "model_id": "E_RF",
          "promotion_allowed": false,
          "r2": 0.4817420330774198,
          "rmse": 0.8237288133904465,
          "role": "development comparator",
          "scaffold_count": 68,
          "source": {
            "path": "outputs/v1.6/model_reproduction/development_results.json",
            "sha256": "c7ab76ca99cd79ee3dc37b1028a9fcf0933253e3d3dd226969189103902384db"
          }
        }
      ],
      "schema_id": "a2a-dashboard.model-registry.v1"
    },
    "molecule_registry": {
      "contract_version": "1.0.0",
      "records": [
        {
          "display_name": "MET-PGD2",
          "functional_label_blinded": true,
          "identity_status": "structure prepared",
          "molecule_id": "LIT25-MET-PGD2",
          "registry_version": "prospective-literature-pilot-v1.4",
          "role": "label-blind prospective candidate",
          "source": {
            "path": "outputs/v1.4/docking/literature_pilot_2025_report.json",
            "sha256": "2f34dbd781a1221ab3c7cd9215cef755b3d8b5974205b83c984b19ad74a50d17"
          },
          "training_eligible": false
        },
        {
          "display_name": "RL-C5",
          "functional_label_blinded": true,
          "identity_status": "structure prepared",
          "molecule_id": "LIT25-RL-C5",
          "registry_version": "prospective-literature-pilot-v1.4",
          "role": "label-blind prospective candidate",
          "source": {
            "path": "outputs/v1.4/docking/literature_pilot_2025_report.json",
            "sha256": "2f34dbd781a1221ab3c7cd9215cef755b3d8b5974205b83c984b19ad74a50d17"
          },
          "training_eligible": false
        },
        {
          "display_name": "RL-C7",
          "functional_label_blinded": true,
          "identity_status": "structure prepared",
          "molecule_id": "LIT25-RL-C7",
          "registry_version": "prospective-literature-pilot-v1.4",
          "role": "label-blind prospective candidate",
          "source": {
            "path": "outputs/v1.4/docking/literature_pilot_2025_report.json",
            "sha256": "2f34dbd781a1221ab3c7cd9215cef755b3d8b5974205b83c984b19ad74a50d17"
          },
          "training_eligible": false
        },
        {
          "display_name": "RL-C9",
          "functional_label_blinded": true,
          "identity_status": "structure prepared",
          "molecule_id": "LIT25-RL-C9",
          "registry_version": "prospective-literature-pilot-v1.4",
          "role": "label-blind prospective candidate",
          "source": {
            "path": "outputs/v1.4/docking/literature_pilot_2025_report.json",
            "sha256": "2f34dbd781a1221ab3c7cd9215cef755b3d8b5974205b83c984b19ad74a50d17"
          },
          "training_eligible": false
        },
        {
          "display_name": "ZM241385",
          "functional_label_blinded": false,
          "identity_status": "parameterized and pose-mapped",
          "molecule_id": "CTRL-5NM4-ZMA",
          "registry_version": "tier-a-native-controls-v1.6",
          "role": "inactive-state native control",
          "source": {
            "path": "config/md_production.v1.6.json",
            "sha256": "21d6a5c2332bf9379b21ee04999eb31261bed7ed5d1dfd5e6ad510490a011e07"
          },
          "training_eligible": false
        },
        {
          "display_name": "NECA",
          "functional_label_blinded": false,
          "identity_status": "parameterized and pose-mapped",
          "molecule_id": "CTRL-5G53-NECA",
          "registry_version": "tier-a-native-controls-v1.6",
          "role": "active-state native control",
          "source": {
            "path": "config/md_production.v1.6.json",
            "sha256": "21d6a5c2332bf9379b21ee04999eb31261bed7ed5d1dfd5e6ad510490a011e07"
          },
          "training_eligible": false
        }
      ],
      "schema_id": "a2a-dashboard.molecule-registry.v1"
    },
    "shadow_actions": {
      "contract_version": "1.0.0",
      "records": [
        {
          "action_id": "shadow-01-literature-intake",
          "authority": "May propose sources and passages; cannot create evidence truth.",
          "executor": "LLM-assisted discovery",
          "prohibited_actions": [
            "assign_training_label",
            "admit_external_member"
          ],
          "required_gate": "Source provenance and primary-publication filter",
          "source": {
            "path": "config/shadow_update.v1.4.json",
            "sha256": "b48669165f967039449f9965b90ac8159a5b62890297e98c8690516a3cace908"
          },
          "stage": "Literature discovery & intake",
          "status": "proposal_only"
        },
        {
          "action_id": "shadow-02-source-filter",
          "authority": "May quarantine; cannot relax the frozen 60/20 floors.",
          "executor": "Deterministic rules",
          "prohibited_actions": [
            "read_sealed_outcomes",
            "weaken_floor"
          ],
          "required_gate": "Primary source, human wild-type A2A, exact endpoint context",
          "source": {
            "path": "outputs/v1.6/external_evidence/pass2_source_extraction/cohort_freeze_manifest.json",
            "sha256": "89d6a1ddd8ba4f2960a63df11713cc34ce505eb99a30c2376a9fa411a2f99cf0"
          },
          "stage": "Source filtering",
          "status": "frozen_floor_failure"
        },
        {
          "action_id": "shadow-03-standardize",
          "authority": "May propose canonical identity and overlap flags; conflicts remain quarantined.",
          "executor": "Deterministic chemistry pipeline",
          "prohibited_actions": [
            "infer_activity",
            "overwrite_registry"
          ],
          "required_gate": "Identity, stereochemistry, exact-structure and scaffold audit",
          "source": {
            "path": "config/shadow_update.v1.4.json",
            "sha256": "b48669165f967039449f9965b90ac8159a5b62890297e98c8690516a3cace908"
          },
          "stage": "Standardize & deduplicate",
          "status": "proposal_only"
        },
        {
          "action_id": "shadow-04-evidence-extract",
          "authority": "May draft categorical fields with citations; disagreements are quarantined.",
          "executor": "Independent computational passes",
          "prohibited_actions": [
            "extract_numeric_sealed_ki",
            "self_approve"
          ],
          "required_gate": "Exact field agreement before membership freeze",
          "source": {
            "path": "outputs/v1.6/external_evidence/pass2_source_extraction/pass2_source_extraction_audit.json",
            "sha256": "f46828a0a569fdec47f265ec815fe51214878f37852e60bf9924a48af809b9d5"
          },
          "stage": "Proposed evidence extraction",
          "status": "human_review_required"
        },
        {
          "action_id": "shadow-05-rank",
          "authority": "May write computational priorities; predictions cannot become labels or hits.",
          "executor": "Frozen development model",
          "prohibited_actions": [
            "serve_model",
            "publish_validated_hit"
          ],
          "required_gate": "Model version, provenance, and molecule identity checks",
          "source": {
            "path": "outputs/v1.6/model_reproduction/development_results.json",
            "sha256": "c7ab76ca99cd79ee3dc37b1028a9fcf0933253e3d3dd226969189103902384db"
          },
          "stage": "Candidate ranking",
          "status": "shadow_only"
        },
        {
          "action_id": "shadow-06-domain",
          "authority": "May flag unsupported chemistry; cannot claim external calibration.",
          "executor": "Frozen development diagnostics",
          "prohibited_actions": [
            "suppress_out_of_domain_flag",
            "claim_external_calibration"
          ],
          "required_gate": "Similarity and descriptor-distance assessment",
          "source": {
            "path": "outputs/v1.6/model_reproduction/development_results.json",
            "sha256": "c7ab76ca99cd79ee3dc37b1028a9fcf0933253e3d3dd226969189103902384db"
          },
          "stage": "Applicability & uncertainty",
          "status": "external_thresholds_not_frozen"
        },
        {
          "action_id": "shadow-07-promotion",
          "authority": "May emit a blocked proposal with reasons; cannot change served state.",
          "executor": "Gate evaluator",
          "prohibited_actions": [
            "promote_model",
            "start_tier_b",
            "release_candidate"
          ],
          "required_gate": "External confirmation plus named human release approval",
          "source": {
            "path": "outputs/v1.6/external_evidence/pass2_source_extraction/cohort_freeze_manifest.json",
            "sha256": "89d6a1ddd8ba4f2960a63df11713cc34ce505eb99a30c2376a9fa411a2f99cf0"
          },
          "stage": "Promotion proposal",
          "status": "blocked"
        }
      ],
      "schema_id": "a2a-dashboard.shadow-actions.v1"
    }
  },
  "dashboard_contract_version": "1.0.0",
  "project": {
    "claim_level": "Retrospective association plus limited prospective prioritization; no external or biological validation.",
    "deadline": "2026-09-30",
    "protocol": "a2a-track3-protocol-v1.6",
    "short_title": "A2A Evidence Command Center",
    "target": "Human ADORA2A \u00b7 CHEMBL251",
    "title": "Evidence-Gated Dual-State Docking and Machine Learning for Functional Classification and Virtual Screening of A2A Adenosine Receptor Ligands"
  },
  "promotion": {
    "automatic_model_replacement_enabled": false,
    "candidate_model": "a2a-external-validation-v1.4",
    "external_gate_passed": false,
    "human_release_approved": false,
    "mode": "shadow_only",
    "permitted_label": "computationally prioritized",
    "prohibited_label": "validated hit",
    "served_model": null,
    "source": {
      "path": "outputs/v1.4/shadow_update_status.json",
      "sha256": "ee09c22cb06824843aae242e423cd85ab3171af2fb5edfe6d5c2179f2eb54185"
    }
  },
  "snapshot_created_at_utc": "2026-09-17T13:35:06+00:00",
  "summary": {
    "docked_candidates": 4,
    "evidence_queue": 240,
    "external_admitted": 0,
    "external_floors_passed": false,
    "external_membership_frozen": true,
    "external_minimum_molecules": 60,
    "external_minimum_scaffolds": 20,
    "external_outcomes_loaded": false,
    "external_scaffolds": 0,
    "md_runs_passed": 6,
    "md_runs_required": 6,
    "outcome_join_authorized": false,
    "pass_2_required": 187,
    "primary_model": "AB_Ridge",
    "primary_model_r2": 0.5605377886314917,
    "promotion_mode": "shadow_only",
    "tier_a_production_started": false,
    "tier_a_production_unlocked": true,
    "tier_b_unlocked": false
  }
};
