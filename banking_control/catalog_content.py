"""Expanded control narratives and links to public regulatory / industry guidance."""

from __future__ import annotations

# Reputable public sources (regulators, standards bodies, EU law).
STANDARD_LINKS: dict[str, tuple[str, str]] = {
    "eba_aml": (
        "EBA — AML/CFT",
        "https://www.eba.europa.eu/regulation-and-policy/anti-money-laundering-and-countering-the-financing-of-terrorism",
    ),
    "fatf_rec": (
        "FATF Recommendations",
        "https://www.fatf-gafi.org/en/topics/fatf-recommendations.html",
    ),
    "amld6": (
        "EU AML Directive (AMLD6)",
        "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A32018L0843",
    ),
    "amlr": (
        "EU AML Regulation (AMLR)",
        "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A32024R1624",
    ),
    "eba_cdd": (
        "EBA — Customer due diligence",
        "https://www.eba.europa.eu/regulation-and-policy/anti-money-laundering-and-countering-the-financing-of-terrorism/guidance-on-anti-money-laundering-and-countering-the-financing-of-terrorism",
    ),
    "eba_pep": (
        "EBA — PEP guidance",
        "https://www.eba.europa.eu/regulation-and-policy/anti-money-laundering-and-countering-the-financing-of-terrorism",
    ),
    "eba_tm": (
        "EBA — Payment services & AML",
        "https://www.eba.europa.eu/regulation-and-policy/payment-services-and-electronic-money",
    ),
    "psd2": (
        "PSD2 (EU)",
        "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=celex%3A32015L2366",
    ),
    "eba_fraud": (
        "EBA — Fraud and financial crime",
        "https://www.eba.europa.eu/regulation-and-policy/anti-money-laundering-and-countering-the-financing-of-terrorism",
    ),
    "crr": (
        "Capital Requirements Regulation (CRR)",
        "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A32013R0575",
    ),
    "eba_loan_orig": (
        "EBA — Loan origination",
        "https://www.eba.europa.eu/regulation-and-policy/credit-risk/credit-risk-underwriting",
    ),
    "ifrs9": (
        "IFRS 9 — Financial instruments",
        "https://www.ifrs.org/issued-standards/list-of-standards/ifrs-9-financial-instruments/",
    ),
    "eba_npe": (
        "EBA — NPE & forbearance",
        "https://www.eba.europa.eu/regulation-and-policy/single-rulebook/interactive-single-rulebook/1433607932873",
    ),
    "ccd": (
        "Consumer Credit Directive",
        "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A32008L0048",
    ),
    "mcd": (
        "Mortgage Credit Directive",
        "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A32014L0017",
    ),
    "eba_product_oversight": (
        "EBA — Product oversight & governance",
        "https://www.eba.europa.eu/regulation-and-policy/consumer-protection",
    ),
    "dora": (
        "DORA (EU)",
        "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A32022R2554",
    ),
    "eba_outsourcing": (
        "EBA — Outsourcing guidelines",
        "https://www.eba.europa.eu/regulation-and-policy/operational-risk",
    ),
    "eba_irrbb": (
        "EBA — IRRBB",
        "https://www.eba.europa.eu/regulation-and-policy/interest-rate-risk-and-credit-spread-risk-in-the-banking-book-irrbb",
    ),
    "bcbs_liq": (
        "BCBS — Liquidity",
        "https://www.bis.org/bcbs/standards.htm",
    ),
    "eba_finrep": (
        "EBA — Reporting (FINREP/COREP)",
        "https://www.eba.europa.eu/regulation-and-policy/supervisory-reporting",
    ),
    "coso": (
        "COSO — Internal control",
        "https://www.coso.org/guidance-on-ic",
    ),
    "nist_csf": (
        "NIST Cybersecurity Framework",
        "https://www.nist.gov/cyberframework",
    ),
    "iso27001": (
        "ISO/IEC 27001",
        "https://www.iso.org/standard/54534.html",
    ),
    "gdpr": (
        "GDPR (EU)",
        "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A32016R0679",
    ),
    "edpb": (
        "EDPB — Guidelines",
        "https://edpb.europa.eu/our-work-tools/general-guidance/guidelines-recommendations-best-practices_en",
    ),
    "eba_gov": (
        "EBA — Internal governance",
        "https://www.eba.europa.eu/regulation-and-policy/internal-governance",
    ),
    "eba_mrm": (
        "EBA — Model risk management",
        "https://www.eba.europa.eu/regulation-and-policy/model-risk-management",
    ),
    "basel_oprisk": (
        "BCBS — Operational risk",
        "https://www.bis.org/bcbs/standards.htm",
    ),
    "ecb_srep": (
        "ECB — Supervisory methodology",
        "https://www.bankingsupervision.europa.eu/ecb/legal/html/index.en.html",
    ),
}

DOMAIN_DEFAULT_KEYS: dict[str, tuple[str, ...]] = {
    "AML": ("eba_aml", "fatf_rec", "amlr"),
    "KYC": ("eba_cdd", "fatf_rec", "amld6"),
    "FRAUD": ("eba_fraud", "psd2", "fatf_rec"),
    "CREDIT": ("eba_loan_orig", "crr", "ifrs9"),
    "RETAIL": ("eba_product_oversight", "ccd", "ecb_srep"),
    "COMM": ("crr", "eba_aml", "eba_gov"),
    "TREAS": ("bcbs_liq", "eba_irrbb", "crr"),
    "FIN": ("eba_finrep", "ifrs9", "coso"),
    "ITGC": ("dora", "coso", "iso27001"),
    "CYBER": ("dora", "nist_csf", "iso27001"),
    "TPRM": ("dora", "eba_outsourcing", "iso27001"),
    "OPS": ("basel_oprisk", "dora", "eba_gov"),
    "MRM": ("eba_mrm", "ifrs9", "ecb_srep"),
    "PRIV": ("gdpr", "edpb", "eba_gov"),
    "CONDUCT": ("eba_gov", "ecb_srep", "gdpr"),
    "REG": ("ecb_srep", "eba_gov", "amlr"),
    "PHYS": ("basel_oprisk", "coso", "eba_gov"),
}

GLOBAL_KEYS: tuple[str, ...] = ("eba_gov", "coso", "ecb_srep")


def _links(*keys: str) -> tuple[tuple[str, str], ...]:
    seen: set[str] = set()
    out: list[tuple[str, str]] = []
    for key in keys:
        if key in seen:
            continue
        seen.add(key)
        pair = STANDARD_LINKS.get(key)
        if pair:
            out.append(pair)
    return tuple(out)


def _domain_links(domain: str) -> tuple[tuple[str, str], ...]:
    return _links(*DOMAIN_DEFAULT_KEYS.get(domain, GLOBAL_KEYS))


# Golden MVP controls — expanded narrative + standard keys (merged with domain defaults).
GOLDEN_ENRICHMENT: dict[str, tuple[str, tuple[str, ...]]] = {
    "AML-001": (
        "Maintain a group-wide ML/TF risk assessment that identifies products, geographies, and delivery channels used by retail and commercial clients. "
        "The assessment must be board-approved, refreshed at least annually, and drive the control inventory, monitoring scenarios, and resource allocation. "
        "Evidence includes workshop minutes, risk ratings, and mapping to business units.",
        ("eba_aml", "fatf_rec", "amlr", "ecb_srep"),
    ),
    "AML-002": (
        "Publish and maintain AML/CFT policies aligned with EU law and FATF standards, with clear roles for first and second lines. "
        "Policies must cover CDD, monitoring, sanctions, correspondent banking, and escalation to the MLRO. "
        "Board attestation and staff attestation cycles should be tracked.",
        ("amlr", "eba_aml", "fatf_rec"),
    ),
    "AML-003": (
        "Screen payers, payees, and routing data against EU and national consolidated sanctions lists before payment release. "
        "Covers SEPA, instant payments, wires, and internal transfers with documented list update SLAs and hit disposition. "
        "False positive handling and audit trails must be demonstrable to supervisors.",
        ("eba_aml", "fatf_rec", "amlr"),
    ),
    "AML-004": (
        "Apply sanctions and dual-use controls to trade finance instruments prior to authorization. "
        "Documentary credits, guarantees, and trade loans require screening of parties, vessels, and goods descriptions where applicable. "
        "Aligns trade operations with group AML policy and export control expectations.",
        ("eba_aml", "fatf_rec", "amlr"),
    ),
    "AML-005": (
        "Operate transaction monitoring for retail instant payment channels with scenarios for velocity, structuring, mule activity, and APP fraud typologies. "
        "Tune rules using investigator feedback and document model/rule changes. "
        "Alert queues must meet internal SLA and link to case management.",
        ("eba_tm", "eba_aml", "psd2", "fatf_rec"),
    ),
    "AML-006": (
        "File suspicious transaction reports within national FIU deadlines once internal escalation confirms suspicion. "
        "Track STR quality, timeliness, and feedback from authorities. "
        "Protect tipping-off constraints in workflows and training.",
        ("fatf_rec", "eba_aml", "amld6"),
    ),
    "AML-007": (
        "Identify politically exposed persons and apply senior approval, enhanced monitoring, and periodic review. "
        "Covers retail and commercial relationships including family and close associates. "
        "PEP status changes must trigger automated or manual reviews.",
        ("eba_pep", "eba_cdd", "fatf_rec"),
    ),
    "AML-008": (
        "Perform correspondent banking due diligence before onboarding and on renewal, including AML supervision quality and nested relationships. "
        "Document payable-through account prohibitions and limitation of services where risk is unacceptable.",
        ("eba_aml", "fatf_rec", "ecb_srep"),
    ),
    "AML-009": (
        "Validate transaction monitoring, scoring, and sanctions matching models/rules at least annually. "
        "Include backtesting, champion/challenger where used, and sign-off by model risk and compliance. "
        "Changes to production rules require controlled release.",
        ("eba_mrm", "eba_aml", "fatf_rec"),
    ),
    "AML-010": (
        "Deliver role-based AML training to retail frontline, commercial relationship managers, and operations staff. "
        "Track completion, remedial training for failures, and content updates when typologies or regulation change.",
        ("eba_aml", "fatf_rec", "amlr"),
    ),
    "KYC-001": (
        "Complete customer due diligence before retail account activation, including identity verification and risk classification. "
        "Block account use until CDD is satisfactory and record the approving officer. "
        "Digital and branch channels must follow the same minimum standards.",
        ("eba_cdd", "amld6", "fatf_rec"),
    ),
    "KYC-002": (
        "Identify and verify beneficial owners of legal entities using reliable, independent sources. "
        "Document ownership structures, control persons, and updates when shareholding changes beyond thresholds.",
        ("eba_cdd", "fatf_rec", "amld6"),
    ),
    "KYC-003": (
        "Refresh retail customer files on a risk-based cycle including dormant account reactivation triggers. "
        "Updates capture occupation, source of funds changes, and adverse media where material.",
        ("eba_cdd", "fatf_rec", "amlr"),
    ),
    "KYC-004": (
        "Perform annual reviews of commercial relationships including purpose, signatories, and financial behaviour. "
        "Escalate high-risk clients for enhanced monitoring and committee approval where required.",
        ("eba_cdd", "crr", "fatf_rec"),
    ),
    "KYC-005": (
        "Apply enhanced due diligence for high-risk third countries and complex structures. "
        "Obtain senior approval, additional verification, and increased monitoring frequency per EBA high-risk factors.",
        ("eba_cdd", "fatf_rec", "amld6"),
    ),
    "KYC-006": (
        "Use device, biometric, and document verification signals during remote retail onboarding to detect impersonation and synthetic identity. "
        "Step-up authentication or manual review when signals exceed thresholds.",
        ("eba_cdd", "psd2", "eba_fraud"),
    ),
    "KYC-007": (
        "Maintain authoritative registers of mandates and signatories for commercial clients. "
        "Validate signatory authority before high-value payment release and after mandate changes.",
        ("eba_cdd", "eba_gov", "crr"),
    ),
    "KYC-008": (
        "Quality-assure closed onboarding files for completeness of CDD evidence and approval trails. "
        "Sample testing feeds back to process owners and training plans.",
        ("eba_cdd", "coso", "fatf_rec"),
    ),
    "FRAUD-001": (
        "Monitor retail instant payments for authorised push payment fraud using payer/payee behavioural analytics and confirmation of payee where available. "
        "Integrate with customer authentication and payment friction rules under PSD2.",
        ("psd2", "eba_fraud", "eba_tm"),
    ),
    "FRAUD-002": (
        "Enforce strong customer authentication and dynamic fraud rules on card-not-present transactions. "
        "Monitor 3DS outcomes and merchant category anomalies.",
        ("psd2", "eba_fraud", "fatf_rec"),
    ),
    "FRAUD-003": (
        "Require dual control on manual payment adjustments, fee reversals, and high-impact operational overrides. "
        "Segregate initiator and approver roles in core banking and payment hubs.",
        ("coso", "eba_fraud", "basel_oprisk"),
    ),
    "FRAUD-004": (
        "Detect mule and pass-through account behaviour using TM scenarios and account lifecycle rules. "
        "Coordinate with AML investigations for account restriction and exit.",
        ("eba_fraud", "eba_aml", "fatf_rec"),
    ),
    "FRAUD-005": (
        "Validate new high-value commercial beneficiaries using callback, multi-factor confirmation, or equivalent non-repudiation. "
        "Maintain evidence of verification before first payment.",
        ("eba_fraud", "psd2", "eba_gov"),
    ),
    "FRAUD-006": (
        "Conduct monthly thematic reviews of fraud losses with root-cause analysis and control tuning actions. "
        "Track implementation of rule and process changes to closure.",
        ("eba_fraud", "basel_oprisk", "coso"),
    ),
}


def _append_golden_batch_two() -> dict[str, tuple[str, tuple[str, ...]]]:
    """Remaining golden controls (CREDIT through PHYS)."""
    return {
        "CREDIT-001": (
            "Maintain a board-approved retail credit policy covering affordability, product limits, and responsible lending. "
            "Policy must align with EBA loan origination expectations and national consumer rules.",
            ("eba_loan_orig", "ccd", "crr"),
        ),
        "CREDIT-002": (
            "Maintain commercial credit policy including delegated lending authorities and sector limits. "
            "Updates require risk committee approval when material.",
            ("eba_loan_orig", "crr", "ecb_srep"),
        ),
        "CREDIT-003": (
            "Govern IFRS 9 staging, significant increase in credit risk triggers, and overlay challenges. "
            "Finance and risk jointly approve material model and overlay changes.",
            ("ifrs9", "eba_mrm", "crr"),
        ),
        "CREDIT-004": (
            "Monitor large exposures against CRR limits with intraday or daily aggregation where required. "
            "Escalate breaches and waivers through credit committee.",
            ("crr", "ecb_srep", "eba_loan_orig"),
        ),
        "CREDIT-005": (
            "Apply LTV limits and borrower stress tests at retail mortgage origination per MCD and EBA good practice. "
            "Document exceptions and compensating controls.",
            ("mcd", "eba_loan_orig", "ccd"),
        ),
        "CREDIT-006": (
            "Test financial covenants on commercial facilities and govern waivers with documented rationale. "
            "Link breaches to early warning and classification processes.",
            ("crr", "eba_npe", "eba_loan_orig"),
        ),
        "CREDIT-007": (
            "Apply consistent definitions for non-performing exposures and forbearance per EBA guidance. "
            "Reconcile reporting to finance and supervisory returns.",
            ("eba_npe", "ifrs9", "crr"),
        ),
        "CREDIT-008": (
            "Refresh collateral valuations by type and jurisdiction with independent review where material. "
            "Track stale valuations and forced sale discounts.",
            ("eba_loan_orig", "crr", "ifrs9"),
        ),
        "CREDIT-009": (
            "Perform independent review of large corporate exposures and rating overrides annually. "
            "Challenge assumptions on cash flow, covenants, and sector outlook.",
            ("eba_loan_orig", "ecb_srep", "crr"),
        ),
        "CREDIT-010": (
            "Identify groups of connected clients for limit aggregation per CRR. "
            "Maintain linkage data and periodic validation against shareholder disclosures.",
            ("crr", "eba_loan_orig", "ecb_srep"),
        ),
        "RETAIL-001": (
            "Provide pre-contractual information including APR/APRC and key risks before binding consumer credit agreements. "
            "Evidence retention supports conduct examinations.",
            ("ccd", "eba_product_oversight", "ecb_srep"),
        ),
        "RETAIL-002": (
            "Apply product approval and target market assessment before launching retail products. "
            "Identify conduct risks and monitoring metrics at design stage.",
            ("eba_product_oversight", "ccd", "ecb_srep"),
        ),
        "RETAIL-003": (
            "Identify and support vulnerable customers with adjusted communications and forbearance options. "
            "Train staff on vulnerability drivers and escalation.",
            ("eba_product_oversight", "ccd", "gdpr"),
        ),
        "RETAIL-004": (
            "Handle complaints within regulatory timelines with root-cause tracking and MI to board committees. "
            "Link repeat issues to product and process remediation.",
            ("eba_product_oversight", "ecb_srep", "ccd"),
        ),
        "RETAIL-005": (
            "Assess bundled accounts and fee packages for fair value and target market alignment. "
            "Document pricing changes and customer communications.",
            ("eba_product_oversight", "ccd", "ecb_srep"),
        ),
        "RETAIL-006": (
            "Manage early arrears with contact strategies and forbearance consistent with consumer duty expectations. "
            "Track roll rates and treatment outcomes.",
            ("ccd", "eba_npe", "eba_product_oversight"),
        ),
        "RETAIL-007": (
            "Review digital sales journeys for clarity of information and undue pressure to purchase. "
            "Include UX testing and complaint thematic reviews.",
            ("eba_product_oversight", "ccd", "psd2"),
        ),
        "RETAIL-008": (
            "Govern sales incentives so remuneration does not encourage mis-selling or unsuitable cross-sell. "
            "Monitor outcomes by product and channel.",
            ("eba_product_oversight", "eba_gov", "ccd"),
        ),
        "COMM-001": (
            "Enforce dual approval on high-value commercial wire release with segregated roles. "
            "Integrate with mandate validation and sanctions screening.",
            ("coso", "eba_aml", "eba_gov"),
        ),
        "COMM-002": (
            "Independently examine trade finance documents before payment to detect discrepancies and fraud indicators. "
            "Staff competency and rotation policies reduce collusion risk.",
            ("eba_aml", "fatf_rec", "coso"),
        ),
        "COMM-003": (
            "Assess FX product suitability for SME clients including leverage and complexity. "
            "Document appropriateness and margin disclosure.",
            ("eba_product_oversight", "mcd", "ecb_srep"),
        ),
        "COMM-004": (
            "Recertify cash management portal users quarterly for commercial clients. "
            "Remove dormant users and enforce MFA.",
            ("dora", "iso27001", "coso"),
        ),
        "COMM-005": (
            "Review revolving working capital facilities against latest financial statements and behaviour. "
            "Update limits and covenants when risk increases.",
            ("eba_loan_orig", "crr", "ecb_srep"),
        ),
        "COMM-006": (
            "Document pricing exceptions on commercial facilities with hierarchical approval. "
            "Monitor margin erosion and conduct risk.",
            ("eba_gov", "eba_loan_orig", "coso"),
        ),
        "TREAS-001": (
            "Calculate and monitor LCR and NSFR with breach escalation to ALCO and treasury risk. "
            "Reconcile inputs to liquidity reporting systems.",
            ("bcbs_liq", "crr", "eba_irrbb"),
        ),
        "TREAS-002": (
            "Measure interest rate risk in the banking book against EBA standards and internal limits. "
            "Report limit breaches and hedging actions to ALCO.",
            ("eba_irrbb", "bcbs_liq", "crr"),
        ),
        "TREAS-003": (
            "Maintain approved funds transfer pricing methodology applied consistently to business lines. "
            "Review assumptions when rate environment shifts materially.",
            ("crr", "eba_irrbb", "ecb_srep"),
        ),
        "TREAS-004": (
            "Test contingency funding plans and document board review of results. "
            "Include payment system continuity and collateral access.",
            ("bcbs_liq", "dora", "basel_oprisk"),
        ),
        "TREAS-005": (
            "Use independent market data sources for treasury valuations with challenge on stale or unobservable inputs. ",
            ("crr", "ifrs9", "eba_irrbb"),
        ),
        "FIN-001": (
            "Reconcile FINREP/COREP submissions to general ledger with preparer and reviewer sign-off. "
            "Track restatements and mapping changes.",
            ("eba_finrep", "crr", "ecb_srep"),
        ),
        "FIN-002": (
            "Apply journal entry controls including approval thresholds, supporting documentation, and segregation for material manual entries. "
            "Align with SOX-style financial close discipline.",
            ("coso", "eba_finrep", "ifrs9"),
        ),
        "FIN-003": (
            "Challenge expected credit loss models, overlays, and post-model adjustments quarterly. "
            "Document governance committee decisions.",
            ("ifrs9", "eba_mrm", "eba_finrep"),
        ),
        "FIN-004": (
            "Reconcile material balance sheet accounts timely with aged item clearance targets. ",
            ("coso", "eba_finrep", "ifrs9"),
        ),
        "FIN-005": (
            "Approve write-offs and provisions per delegated authority with audit trail. "
            "Align with credit and IFRS 9 policies.",
            ("ifrs9", "eba_npe", "coso"),
        ),
        "FIN-006": (
            "Maintain change log for regulatory reporting mappings when products or charts of accounts change. ",
            ("eba_finrep", "crr", "ecb_srep"),
        ),
        "ITGC-001": (
            "Recertify privileged access quarterly; remove excess rights and enforce break-glass logging. "
            "Align with DORA ICT access expectations.",
            ("dora", "iso27001", "coso"),
        ),
        "ITGC-002": (
            "Control production changes with testing, approval, and emergency retrospective review. ",
            ("coso", "dora", "iso27001"),
        ),
        "ITGC-003": (
            "Monitor critical batch jobs with defined escalation when SLAs are missed. ",
            ("dora", "coso", "basel_oprisk"),
        ),
        "ITGC-004": (
            "Prevent unmasked production data in non-production environments without explicit approval. ",
            ("gdpr", "iso27001", "dora"),
        ),
        "ITGC-005": (
            "Synchronize joiner/mover/leaver events to identity systems within SLA. ",
            ("coso", "iso27001", "dora"),
        ),
        "ITGC-006": (
            "Inventory material end-user computing tools used in finance reporting with compensating controls. ",
            ("coso", "eba_finrep", "iso27001"),
        ),
        "CYBER-001": (
            "Maintain a board-approved ICT risk management framework meeting DORA requirements. ",
            ("dora", "nist_csf", "iso27001"),
        ),
        "CYBER-002": (
            "Classify major ICT incidents and meet regulatory reporting timelines to competent authorities. ",
            ("dora", "nist_csf", "eba_outsourcing"),
        ),
        "CYBER-003": (
            "Track vulnerability remediation against SLAs for critical and internet-facing assets. ",
            ("nist_csf", "iso27001", "dora"),
        ),
        "CYBER-004": (
            "Centralize security logs with tamper protection and retention meeting investigation needs. ",
            ("nist_csf", "iso27001", "dora"),
        ),
        "CYBER-005": (
            "Enforce MFA for privileged and remote access with periodic control testing. ",
            ("nist_csf", "dora", "iso27001"),
        ),
        "CYBER-006": (
            "Perform threat-led penetration testing or independent security tests on critical functions. ",
            ("dora", "nist_csf", "iso27001"),
        ),
        "CYBER-007": (
            "Run phishing simulations with remedial training for repeat clickers. ",
            ("nist_csf", "iso27001", "eba_gov"),
        ),
        "CYBER-008": (
            "Manage cryptographic keys and HSM policies for payment and channel encryption. ",
            ("iso27001", "psd2", "nist_csf"),
        ),
        "TPRM-001": (
            "Maintain DORA register of information on ICT third-party arrangements for supervisory reporting. ",
            ("dora", "eba_outsourcing", "ecb_srep"),
        ),
        "TPRM-002": (
            "Perform due diligence before contracting critical ICT services including financial and resilience assessment. ",
            ("dora", "eba_outsourcing", "iso27001"),
        ),
        "TPRM-003": (
            "Assess fourth-party and concentration risk in outsourcing chains. ",
            ("dora", "eba_outsourcing", "basel_oprisk"),
        ),
        "TPRM-004": (
            "Recertify vendor remote access with time-bound credentials and logging. ",
            ("dora", "iso27001", "coso"),
        ),
        "TPRM-005": (
            "Document exit strategies for critical vendors including data return and continuity. ",
            ("dora", "eba_outsourcing", "basel_oprisk"),
        ),
        "OPS-001": (
            "Test business continuity plans demonstrating RTO/RPO for critical payment and retail services. ",
            ("basel_oprisk", "dora", "bcbs_liq"),
        ),
        "OPS-002": (
            "Capture operational loss events for risk assessment and Basel internal data needs. ",
            ("basel_oprisk", "coso", "ecb_srep"),
        ),
        "OPS-003": (
            "Reconcile SEPA and instant payment scheme positions daily with exception clearance. ",
            ("psd2", "basel_oprisk", "eba_tm"),
        ),
        "OPS-004": (
            "Apply records retention schedules harmonizing AML, tax, and GDPR requirements. ",
            ("gdpr", "fatf_rec", "eba_aml"),
        ),
        "MRM-001": (
            "Inventory and tier all material models with owners and validation cycles per EBA model risk guidance. ",
            ("eba_mrm", "ifrs9", "ecb_srep"),
        ),
        "MRM-002": (
            "Independently validate tier 1 models before use and on periodic schedule. ",
            ("eba_mrm", "ifrs9", "ecb_srep"),
        ),
        "PRIV-001": (
            "Maintain GDPR Article 30 records of processing and lawful basis documentation. ",
            ("gdpr", "edpb", "eba_gov"),
        ),
        "PRIV-002": (
            "Complete data protection impact assessments for high-risk processing such as profiling at scale. ",
            ("gdpr", "edpb", "eba_mrm"),
        ),
        "PRIV-003": (
            "Fulfil data subject access and erasure requests within statutory timelines. ",
            ("gdpr", "edpb", "ecb_srep"),
        ),
        "PRIV-004": (
            "Operate breach notification playbooks including 72-hour supervisory notification where required. ",
            ("gdpr", "edpb", "dora"),
        ),
        "CONDUCT-001": (
            "Provide EU Whistleblowing Directive aligned reporting channels with anti-retaliation safeguards. ",
            ("eba_gov", "gdpr", "ecb_srep"),
        ),
        "CONDUCT-002": (
            "Assess fit and proper criteria for material risk takers and key function holders per EBA guidelines. ",
            ("eba_gov", "ecb_srep", "crr"),
        ),
        "REG-001": (
            "Track EU regulatory developments including AMLR, DORA RTS, and EBA consultations with impact assessment. ",
            ("ecb_srep", "amlr", "dora"),
        ),
        "REG-002": (
            "Escalate material regulatory breaches to compliance committee and notify NCAs when required. ",
            ("ecb_srep", "eba_gov", "amlr"),
        ),
        "PHYS-001": (
            "Require dual control for branch cash vault access and end-of-day reconciliation. ",
            ("coso", "basel_oprisk", "eba_gov"),
        ),
        "PHYS-002": (
            "Reconcile CIT ATM replenishment logs to cash positions and investigate variances. ",
            ("coso", "basel_oprisk", "eba_gov"),
        ),
    }


GOLDEN_ENRICHMENT.update(_append_golden_batch_two())


THEME_EXTRA: dict[str, str] = {
    "AML": "Align scenario design and investigation quality with group ML/TF risk assessment and STR policy.",
    "KYC": "Ensure evidence is sufficient for supervisors to re-perform CDD decisions on sampled files.",
    "FRAUD": "Coordinate with payment schemes and PSD2 authentication requirements when tuning rules.",
    "CREDIT": "Link testing to portfolio monitoring, IFRS 9 staging, and large exposure reporting where applicable.",
    "RETAIL": "Consider conduct risk, vulnerable customers, and product governance in test samples.",
    "COMM": "Include trade finance and wire operations in walkthroughs when control touches commercial payments.",
    "TREAS": "Reference ALCO minutes and liquidity reporting when evidencing operating effectiveness.",
    "FIN": "Tie samples to FINREP/COREP line items and financial close calendars.",
    "ITGC": "Map failures to DORA ICT risk register and change management records.",
    "CYBER": "Reference vulnerability scans, incident tickets, and DORA classification where relevant.",
    "TPRM": "Include subcontractor flows and register of information extracts in evidence packs.",
    "OPS": "Demonstrate linkage to continuity tests and scheme reconciliation metrics.",
    "MRM": "Use model inventory IDs and validation reports as primary evidence.",
    "PRIV": "Reference ROPA entries and DPIA records for privacy-related controls.",
    "CONDUCT": "Include HR and governance committee papers for culture and whistleblowing controls.",
    "REG": "Maintain horizon scanning logs and breach registers for regulatory controls.",
    "PHYS": "Use branch visit checklists and CIT logs for physical control tests.",
}


def enrich_control(ctrl: object) -> object:
    """Return control with expanded description and standards references."""
    from banking_control.catalog import ControlDefinition

    if not isinstance(ctrl, ControlDefinition):
        raise TypeError("expected ControlDefinition")

    golden = GOLDEN_ENRICHMENT.get(ctrl.control_code)
    if golden:
        description, keys = golden
        standards = _links(*keys)
    else:
        theme_line = THEME_EXTRA.get(ctrl.domain, "")
        description = (
            f"{ctrl.description.rstrip('.')}. "
            f"{theme_line} "
            "Document owners, frequency, sample sizes, and exception remediation in the control library. "
            "Applies to EU retail and commercial banking entities in scope of group policy."
        ).strip()
        standards = _domain_links(ctrl.domain)

    return ControlDefinition(
        control_code=ctrl.control_code,
        control_name=ctrl.control_name,
        domain=ctrl.domain,
        risk_tier=ctrl.risk_tier,
        owner=ctrl.owner,
        frequency=ctrl.frequency,
        description=description,
        is_golden=ctrl.is_golden,
        similarity_key=ctrl.similarity_key,
        standards_refs=standards,
    )
