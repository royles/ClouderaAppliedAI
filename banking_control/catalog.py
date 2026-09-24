"""EU retail + commercial banking control catalog (~380 controls, 80 golden)."""

from __future__ import annotations

from dataclasses import dataclass

RiskTier = str
Frequency = str


@dataclass(frozen=True)
class ControlDefinition:
    control_code: str
    control_name: str
    domain: str
    risk_tier: RiskTier
    owner: str
    frequency: Frequency
    description: str
    is_golden: bool = False
    similarity_key: str | None = None


DOMAIN_OWNERS: dict[str, str] = {
    "AML": "Group BSA/AML Officer",
    "KYC": "Head of KYC Operations",
    "FRAUD": "Head of Financial Crime",
    "CREDIT": "Chief Credit Officer",
    "RETAIL": "Head of Retail Conduct",
    "COMM": "Head of Commercial Banking",
    "TREAS": "Group Treasurer",
    "FIN": "Group Controller",
    "ITGC": "CIO / IT Risk",
    "CYBER": "CISO",
    "TPRM": "Third-Party Risk Lead",
    "OPS": "Chief Operating Officer",
    "MRM": "Model Risk Officer",
    "PRIV": "Data Protection Officer",
    "CONDUCT": "Head of HR Compliance",
    "REG": "Head of Regulatory Affairs",
    "PHYS": "Corporate Security",
}

# Target counts per domain (total 380, including golden).
DOMAIN_TARGETS: dict[str, int] = {
    "AML": 44,
    "KYC": 33,
    "FRAUD": 24,
    "CREDIT": 35,
    "RETAIL": 28,
    "COMM": 21,
    "TREAS": 21,
    "FIN": 30,
    "ITGC": 30,
    "CYBER": 30,
    "TPRM": 21,
    "OPS": 24,
    "MRM": 10,
    "PRIV": 17,
    "CONDUCT": 10,
    "REG": 12,
    "PHYS": 6,
}


def _golden_controls() -> list[ControlDefinition]:
    """MVP golden set (80) — EU retail + commercial, supervisory-aligned."""
    g: list[tuple[str, str, str, RiskTier, Frequency, str]] = [
        # AML (10)
        ("AML-001", "Enterprise ML/TF risk assessment", "AML", "Critical", "Annual",
         "Board-approved ML/TF risk assessment refreshed annually; EBA AML/CFT Guidelines."),
        ("AML-002", "Group-wide AML/CFT policy", "AML", "Critical", "Annual",
         "Policies aligned with AMLR/AMLD and national transposition; board attestation."),
        ("AML-003", "Sanctions screening — payments", "AML", "Critical", "Daily",
         "Real-time EU/consolidated lists screening on outbound and inbound payments."),
        ("AML-004", "Sanctions screening — trade finance", "AML", "Critical", "Daily",
         "Documentary trade screened pre-release; dual-list coverage documented."),
        ("AML-005", "Transaction monitoring — retail instant payments", "AML", "Critical", "Daily",
         "Scenario library covers APP fraud and velocity per EBA payment AML expectations."),
        ("AML-006", "STR filing timeliness", "AML", "Critical", "Event",
         "Suspicious transaction reports filed within national FIU deadlines."),
        ("AML-007", "PEP identification and approval", "AML", "High", "Event",
         "PEP classification, senior approval, and enhanced monitoring triggers."),
        ("AML-008", "Correspondent banking due diligence", "AML", "High", "Annual",
         "EBA correspondent banking due diligence and periodic review where applicable."),
        ("AML-009", "AML model / rule validation", "AML", "High", "Annual",
         "TM and scoring models validated per EBA/SSM model governance expectations."),
        ("AML-010", "AML training — role-based", "AML", "Medium", "Annual",
         "Retail frontline and commercial RM completion tracked with escalation."),
        # KYC (8)
        ("KYC-001", "Retail CDD at onboarding", "KYC", "Critical", "Event",
         "Identity verification and CDD before account activation; AMLR CDD standards."),
        ("KYC-002", "Legal entity UBO verification", "KYC", "Critical", "Event",
         "Beneficial ownership identified and verified for corporate clients."),
        ("KYC-003", "Periodic retail CDD refresh", "KYC", "High", "Quarterly",
         "Risk-based refresh cycles for retail customers including dormant reactivation."),
        ("KYC-004", "Commercial periodic review", "KYC", "High", "Annual",
         "Annual review of corporate files including signatories and purpose of relationship."),
        ("KYC-005", "High-risk third-country EDD", "KYC", "Critical", "Event",
         "Enhanced due diligence for high-risk jurisdictions per EBA high-risk factors."),
        ("KYC-006", "Remote onboarding fraud controls", "KYC", "High", "Daily",
         "Video-ID and device signals for digital retail onboarding."),
        ("KYC-007", "Mandate and signatory register", "KYC", "High", "Event",
         "Authorized signers validated before high-value commercial payment release."),
        ("KYC-008", "KYC file completeness QA", "KYC", "Medium", "Monthly",
         "Quality assurance sample on closed onboarding files."),
        # FRAUD (6)
        ("FRAUD-001", "APP fraud detection — retail", "FRAUD", "Critical", "Daily",
         "PSD2-aligned monitoring and payer/payee confirmation for instant payments."),
        ("FRAUD-002", "Card fraud rules and 3DS", "FRAUD", "High", "Daily",
         "Strong customer authentication and fraud rules on card e-commerce."),
        ("FRAUD-003", "Internal fraud — dual control", "FRAUD", "High", "Daily",
         "Segregation on manual payment adjustments and fee waivers."),
        ("FRAUD-004", "Mule account identification", "FRAUD", "High", "Daily",
         "Retail account behaviour scenarios linked to TM and account closure."),
        ("FRAUD-005", "Commercial beneficiary validation", "FRAUD", "High", "Event",
         "Callback or multi-factor confirmation for new high-value beneficiaries."),
        ("FRAUD-006", "Fraud loss root-cause review", "FRAUD", "Medium", "Monthly",
         "Monthly thematic review of fraud typologies and control tuning."),
        # CREDIT (10)
        ("CREDIT-001", "Group credit policy — retail", "CREDIT", "Critical", "Annual",
         "Retail lending policy including affordability; EBA loan origination GL."),
        ("CREDIT-002", "Group credit policy — commercial", "CREDIT", "Critical", "Annual",
         "SME/corporate policy including delegated authority matrix."),
        ("CREDIT-003", "IFRS 9 staging and SICR", "CREDIT", "Critical", "Quarterly",
         "Significant increase in credit risk and staging governance."),
        ("CREDIT-004", "Large exposures monitoring", "CREDIT", "Critical", "Daily",
         "CRR Art. 395 large exposure limits monitored with escalation."),
        ("CREDIT-005", "Retail mortgage LTV and stress", "CREDIT", "High", "Event",
         "LTV caps and borrower stress tested at origination."),
        ("CREDIT-006", "Commercial covenant monitoring", "CREDIT", "High", "Quarterly",
         "Financial covenant testing and waiver governance."),
        ("CREDIT-007", "Forbearance and NPE identification", "CREDIT", "High", "Monthly",
         "EBA NPE/forbearance definitions applied consistently."),
        ("CREDIT-008", "Collateral valuation refresh", "CREDIT", "High", "Annual",
         "Commercial collateral revaluation cadence by collateral type."),
        ("CREDIT-009", "Credit risk review — large corporates", "CREDIT", "High", "Annual",
         "Independent review of top exposures and rating overrides."),
        ("CREDIT-010", "Connected clients aggregation", "CREDIT", "High", "Quarterly",
         "Group of connected clients identified per CRR for limit purposes."),
        # RETAIL (8)
        ("RETAIL-001", "Pre-contractual information — consumer credit", "RETAIL", "Critical", "Event",
         "APRC/APR and pre-contractual disclosures per Consumer Credit Directive."),
        ("RETAIL-002", "Product approval — retail products", "RETAIL", "High", "Annual",
         "Product governance and target market assessment before launch."),
        ("RETAIL-003", "Vulnerable customer identification", "RETAIL", "High", "Quarterly",
         "Staff guidance and flags for vulnerable retail customers."),
        ("RETAIL-004", "Complaints handling SLA", "RETAIL", "High", "Monthly",
         "Regulatory complaint timelines monitored with root-cause tracking."),
        ("RETAIL-005", "Fair value — bundled accounts", "RETAIL", "Medium", "Annual",
         "Fee bundles assessed for fair value and conduct risk."),
        ("RETAIL-006", "Arrears management — retail", "RETAIL", "High", "Monthly",
         "Early arrears contact and forbearance options documented."),
        ("RETAIL-007", "Digital channel conduct monitoring", "RETAIL", "Medium", "Quarterly",
         "UX and sales journey reviews for mis-selling risk."),
        ("RETAIL-008", "Retail sales incentive governance", "RETAIL", "High", "Quarterly",
         "Remuneration and incentives do not encourage mis-selling."),
        # COMM (6)
        ("COMM-001", "Commercial dual approval — wires", "COMM", "Critical", "Daily",
         "Dual control on high-value commercial payment release."),
        ("COMM-002", "Trade finance document examination", "COMM", "High", "Daily",
         "Independent examination of trade documents before payment."),
        ("COMM-003", "FX sales suitability — SME", "COMM", "High", "Event",
         "FX product sold consistent with client sophistication."),
        ("COMM-004", "Cash management access recertification", "COMM", "High", "Quarterly",
         "Portal users recertified for commercial clients."),
        ("COMM-005", "Working capital facility annual review", "COMM", "High", "Annual",
         "Revolving facilities reviewed against latest financials."),
        ("COMM-006", "Commercial pricing exception approval", "COMM", "Medium", "Event",
         "Margin exceptions documented with approver hierarchy."),
        # TREAS (5)
        ("TREAS-001", "LCR/NSFR monitoring", "TREAS", "Critical", "Daily",
         "CRR liquidity metrics calculated and reported with breach escalation."),
        ("TREAS-002", "IRRBB measurement and limits", "TREAS", "Critical", "Monthly",
         "EBA IRRBB expectations; limit breaches escalated to ALCO."),
        ("TREAS-003", "Funds transfer pricing governance", "TREAS", "High", "Quarterly",
         "FTP methodology approved and applied consistently."),
        ("TREAS-004", "Liquidity contingency plan test", "TREAS", "High", "Annual",
         "Contingency funding plan tested and board-reviewed."),
        ("TREAS-005", "Market data integrity — treasury", "TREAS", "High", "Daily",
         "Independent price sources for valuation of treasury positions."),
        # FIN (6)
        ("FIN-001", "FINREP/COREP submission quality", "FIN", "Critical", "Quarterly",
         "Regulatory returns reconciled to general ledger with sign-off."),
        ("FIN-002", "Financial close — SOX-style JE controls", "FIN", "Critical", "Monthly",
         "Journal entry approval thresholds and segregation for material entries."),
        ("FIN-003", "IFRS 9 ECL model governance", "FIN", "Critical", "Quarterly",
         "ECL models and overlays challenged by finance and validated."),
        ("FIN-004", "Balance sheet substantiation", "FIN", "High", "Monthly",
         "Material balance sheet accounts reconciled timely."),
        ("FIN-005", "Provisions and write-off policy", "FIN", "High", "Quarterly",
         "Write-offs approved per delegated authority with audit trail."),
        ("FIN-006", "Regulatory reporting change log", "FIN", "Medium", "Event",
         "FINREP/COREP mapping updated when products or systems change."),
        # ITGC (6)
        ("ITGC-001", "Privileged access recertification", "ITGC", "Critical", "Quarterly",
         "Admin access reviewed; DORA/EBA ICT access expectations."),
        ("ITGC-002", "Production change management", "ITGC", "Critical", "Daily",
         "Emergency change process with retrospective review."),
        ("ITGC-003", "Batch job monitoring — core banking", "ITGC", "High", "Daily",
         "Critical batch failures escalated within defined SLA."),
        ("ITGC-004", "Segregation of environments", "ITGC", "High", "Quarterly",
         "No production data in non-prod without masking approval."),
        ("ITGC-005", "IT general controls — user lifecycle", "ITGC", "High", "Daily",
         "Joiner/mover/leaver synced to identity store within SLA."),
        ("ITGC-006", "End-user computing policy", "ITGC", "Medium", "Annual",
         "Spreadsheet and macro inventory for material finance models."),
        # CYBER (8)
        ("CYBER-001", "DORA ICT risk management framework", "CYBER", "Critical", "Annual",
         "Board-approved ICT risk framework per DORA."),
        ("CYBER-002", "Major incident classification and reporting", "CYBER", "Critical", "Event",
         "DORA incident reporting timelines to competent authority."),
        ("CYBER-003", "Vulnerability remediation SLA", "CYBER", "High", "Weekly",
         "Critical patch SLAs tracked for internet-facing and core systems."),
        ("CYBER-004", "Security logging and retention", "CYBER", "High", "Daily",
         "Centralized logs retained per policy; tamper protection."),
        ("CYBER-005", "MFA for privileged and remote access", "CYBER", "Critical", "Daily",
         "MFA enforced for admin and remote workforce access."),
        ("CYBER-006", "TLPT / penetration testing", "CYBER", "High", "Annual",
         "Threat-led or independent penetration test on critical functions."),
        ("CYBER-007", "Security awareness phishing simulation", "CYBER", "Medium", "Quarterly",
         "Phishing exercises with remedial training."),
        ("CYBER-008", "Cryptographic key management", "CYBER", "High", "Quarterly",
         "HSM and key rotation for payment and channel encryption."),
        # TPRM (5)
        ("TPRM-001", "DORA register of information", "TPRM", "Critical", "Quarterly",
         "Register of ICT third-party arrangements maintained for supervisors."),
        ("TPRM-002", "Critical ICT provider due diligence", "TPRM", "Critical", "Event",
         "Due diligence before contracting critical outsourced ICT."),
        ("TPRM-003", "Fourth-party concentration risk", "TPRM", "High", "Quarterly",
         "Sub-outsourcing and concentration assessed per DORA."),
        ("TPRM-004", "Vendor access review", "TPRM", "High", "Quarterly",
         "Vendor remote access recertified and time-bound."),
        ("TPRM-005", "Exit plan — critical vendor", "TPRM", "High", "Annual",
         "Documented exit strategy for core banking SaaS/hosting."),
        # OPS (4)
        ("OPS-001", "Business continuity test", "OPS", "Critical", "Annual",
         "BCP test evidences RTO/RPO for critical retail and payment services."),
        ("OPS-002", "Operational loss data collection", "OPS", "High", "Quarterly",
         "Basel operational loss events captured for risk assessment."),
        ("OPS-003", "Payment scheme reconciliation", "OPS", "High", "Daily",
         "SEPA/instant payment scheme reconciliations completed daily."),
        ("OPS-004", "Records management retention", "OPS", "Medium", "Quarterly",
         "Retention schedules align AML and GDPR requirements."),
        # MRM (2)
        ("MRM-001", "Model inventory and tiering", "MRM", "Critical", "Annual",
         "All material models inventoried with tier and owner per ECB/EBA guidance."),
        ("MRM-002", "Independent model validation", "MRM", "Critical", "Annual",
         "Tier 1 models independently validated before use and periodically."),
        # PRIV (4)
        ("PRIV-001", "ROPA and lawful basis register", "PRIV", "Critical", "Annual",
         "GDPR Article 30 records of processing maintained."),
        ("PRIV-002", "DPIA for high-risk processing", "PRIV", "Critical", "Event",
         "DPIA completed for scoring, profiling, and large-scale monitoring."),
        ("PRIV-003", "DSAR fulfilment SLA", "PRIV", "High", "Monthly",
         "Data subject requests answered within GDPR timelines."),
        ("PRIV-004", "Data breach notification", "PRIV", "Critical", "Event",
         "72-hour supervisory notification process tested."),
        # CONDUCT (2)
        ("CONDUCT-001", "Whistleblowing channel and protection", "CONDUCT", "High", "Annual",
         "EU Whistleblowing Directive aligned channel with anti-retaliation."),
        ("CONDUCT-002", "Fit and proper — material risk takers", "CONDUCT", "High", "Annual",
         "EBA internal governance fit-and-proper for key function holders."),
        # REG (2)
        ("REG-001", "Horizon scanning — EU regulatory", "REG", "High", "Monthly",
         "Tracking AMLR, DORA RTS, and EBA consultation papers."),
        ("REG-002", "Regulatory breach escalation", "REG", "Critical", "Event",
         "Material breaches reported to compliance committee and NCA where required."),
        # PHYS (2)
        ("PHYS-001", "Branch cash handling dual control", "PHYS", "High", "Daily",
         "Retail branch cash vault access requires dual control."),
        ("PHYS-002", "ATM replenishment audit trail", "PHYS", "Medium", "Daily",
         "CIT replenishment logs reconciled to cash positions."),
    ]
    out: list[ControlDefinition] = []
    for code, name, domain, tier, freq, desc in g:
        out.append(
            ControlDefinition(
                control_code=code,
                control_name=name,
                domain=domain,
                risk_tier=tier,
                owner=DOMAIN_OWNERS[domain],
                frequency=freq,
                description=desc,
                is_golden=True,
            )
        )
    return out


# Thematic expansions per domain (EU retail + commercial bank).
_DOMAIN_THEMES: dict[str, list[tuple[str, RiskTier, Frequency, str]]] = {
    "AML": [
        ("Cash threshold aggregation review", "High", "Daily", "Structuring scenarios on cash and ATM deposits."),
        ("Cross-border corridor monitoring", "High", "Daily", "Corridor-specific rules for high-risk remittance flows."),
        ("Trade-based ML red flags", "High", "Weekly", "Over/under invoicing indicators on trade finance clients."),
        ("Private banking enhanced monitoring", "High", "Monthly", "Enhanced review of high-net-worth PEP relationships."),
        ("Crypto asset exposure screening", "Medium", "Weekly", "VASP and crypto exposure identified where permitted."),
        ("AML alert investigation SLA", "High", "Daily", "Analyst queue aged items escalated per policy."),
        ("Sanctions false positive tuning", "Medium", "Monthly", "Screening fuzzy logic tuned with documented approvals."),
        ("Politically exposed entity exit review", "High", "Event", "PEP offboarding and residual risk sign-off."),
        ("Tax evasion typology scenarios", "Medium", "Quarterly", "AML scenarios aligned to national tax evasion risks."),
        ("Shell company risk indicators", "High", "Event", "Commercial onboarding checks for shell-like structures."),
    ],
    "KYC": [
        ("Simplified due diligence eligibility", "Medium", "Event", "Low-risk product SDD criteria documented."),
        ("Adverse media screening", "High", "Event", "Automated and analyst review on onboarding and triggers."),
        ("Document expiry monitoring", "Medium", "Weekly", "ID document expiry blocks high-risk transactions."),
        ("Non-face-to-face CDD enhancement", "High", "Event", "Additional checks for remote commercial onboarding."),
        ("Trust and foundation CDD", "High", "Event", "Complex trust structures escalated to specialist team."),
        ("Branch walk-in identity checks", "Medium", "Daily", "Retail counter onboarding checklist compliance."),
        ("Relationship purpose documentation", "Medium", "Event", "Expected activity recorded for commercial clients."),
        ("KYC remediation backlog management", "Medium", "Monthly", "Aged KYC gaps tracked with executive dashboard."),
    ],
    "FRAUD": [
        ("SIM swap detection", "High", "Daily", "Mobile channel SIM change correlated with payment spikes."),
        ("Social engineering call-back policy", "Medium", "Daily", "High-value retail transfers require call-back."),
        ("Commercial invoice fraud controls", "High", "Event", "Invoice redirection fraud checks on SME payments."),
        ("Chargeback dispute monitoring", "Medium", "Weekly", "Card chargeback trends reviewed for merchant fraud."),
        ("Biometric login anomaly detection", "Medium", "Daily", "Mobile app biometric failure rate monitoring."),
        ("Fraud intelligence sharing", "Medium", "Quarterly", "Participation in national fraud intelligence forums."),
    ],
    "CREDIT": [
        ("Retail unsecured affordability", "High", "Event", "Income and expenditure assessment documented."),
        ("SME scorecard override governance", "High", "Event", "Score overrides require credit committee trail."),
        ("Sector concentration limits", "High", "Monthly", "Commercial sector limits vs board appetite."),
        ("Guarantor financial review", "Medium", "Annual", "Personal guarantees supported by financial evidence."),
        ("Early warning signal — commercial", "High", "Monthly", "Behavioral and financial EWS for SME portfolio."),
        ("Retail collections strategy", "Medium", "Monthly", "Collections treatment aligned to conduct rules."),
        ("Credit data bureau usage", "Medium", "Event", "Permissible purpose and consent for bureau pulls."),
        ("Project finance milestone release", "High", "Event", "Construction drawdowns tied to engineer certificates."),
    ],
    "RETAIL": [
        ("Mortgage broker commission disclosure", "High", "Event", "Third-party broker conflicts disclosed to customers."),
        ("Overdraft fairness assessment", "Medium", "Annual", "Overdraft pricing and limits conduct review."),
        ("Savings product rate change notice", "Medium", "Event", "Notice periods for variable retail savings rates."),
        ("Mobile app terms update consent", "Medium", "Event", "Material T&C changes communicated and logged."),
        ("Retail account closure conduct", "Medium", "Event", "Fair treatment on closure and fee transparency."),
    ],
    "COMM": [
        ("Letter of credit amendment approval", "High", "Event", "Amendments independently checked before issue."),
        ("Bank guarantee wording legal review", "High", "Event", "Standard wording deviations require legal sign-off."),
        ("Supply chain finance buyer limit", "High", "Quarterly", "Anchor buyer limits recalibrated to credit rating."),
        ("Commercial overdraft excess handling", "High", "Daily", "Excess positions escalated same day."),
    ],
    "TREAS": [
        ("FX position limits intraday", "High", "Daily", "Trading book and structural FX limits monitored."),
        ("Collateral management — derivatives", "High", "Daily", "CSA margin calls reconciled daily."),
        ("Intragroup liquidity limits", "High", "Monthly", "CRR group support and transfer pricing documented."),
        ("ALCO pack timeliness", "Medium", "Monthly", "ALCO materials distributed before committee deadline."),
    ],
    "FIN": [
        ("Intercompany reconciliation", "High", "Monthly", "Group entity balances reconciled and aged items cleared."),
        ("Tax reporting data lineage", "High", "Quarterly", "Tax packs traceable to sub-ledger and GL."),
        ("Fixed asset capitalization review", "Medium", "Quarterly", "Capital vs opex thresholds enforced in workflow."),
        ("Management reporting sign-off", "High", "Monthly", "CFO sign-off on flash and statutory bridges."),
    ],
    "ITGC": [
        ("Database access logging review", "High", "Weekly", "Privileged DB queries sampled for anomalies."),
        ("Interface monitoring — payment hub", "High", "Daily", "File exchange and API errors escalated."),
        ("Disaster recovery failover test", "Critical", "Annual", "DR test for core ledger with documented results."),
        ("Software license compliance", "Low", "Annual", "Material software licenses inventoried."),
    ],
    "CYBER": [
        ("Endpoint detection response coverage", "High", "Weekly", "EDR agent coverage report for workstations and servers."),
        ("Cloud security posture review", "High", "Monthly", "CSPM findings remediated per SLA."),
        ("Secure SDLC gate — critical apps", "High", "Event", "Security review before major release to production."),
        ("DDoS protection test", "Medium", "Annual", "Payment channel DDoS playbooks tested."),
    ],
    "TPRM": [
        ("Cloud provider SOC/ISAE evidence", "High", "Annual", "Annual assurance reports reviewed with gap tracking."),
        ("Outsourced call centre oversight", "Medium", "Quarterly", "Mystery shopping and QA on outsourced collections."),
        ("Payment processor SLA monitoring", "High", "Monthly", "Scheme certification and uptime SLA tracked."),
    ],
    "OPS": [
        ("Manual payment queue four-eyes", "High", "Daily", "Manual payment repairs require second checker."),
        ("Retail lockbox processing accuracy", "Medium", "Daily", "Commercial lockbox exception rate monitored."),
        ("Data quality — customer master", "High", "Weekly", "Duplicate and orphan customer records remediated."),
    ],
    "MRM": [
        ("Model use exception tracking", "High", "Quarterly", "Temporary model overrides time-bound and approved."),
        ("PD/LGD model monitoring", "High", "Quarterly", "IFRS 9 PD/LGD backtesting and drift analysis."),
        ("AI/ML credit model documentation", "High", "Annual", "Explainability and bias testing for ML credit models."),
    ],
    "PRIV": [
        ("Marketing consent preference centre", "Medium", "Monthly", "Opt-in/opt-out honored across channels."),
        ("Cross-border data transfer assessment", "High", "Event", "SCCs and transfer impact assessments documented."),
        ("Privacy training completion", "Medium", "Annual", "Staff privacy training tracked by business unit."),
    ],
    "CONDUCT": [
        ("Code of conduct attestation", "Medium", "Annual", "All staff attest to code of conduct annually."),
        ("Conflict of interest declarations", "High", "Annual", "Material conflicts registered for commercial RMs."),
    ],
    "REG": [
        ("License and passporting register", "High", "Quarterly", "EEA passport and branch permissions current."),
        ("Regulatory exam action tracking", "High", "Monthly", "Supervisory findings tracked to closure."),
    ],
    "PHYS": [
        ("Data centre physical access log", "High", "Daily", "Visitor and contractor access to DC reviewed daily."),
        ("Branch robbery response procedure", "Medium", "Annual", "Staff training on robbery and duress protocols."),
    ],
}


def _expand_domain(
    domain: str,
    target: int,
    existing: list[ControlDefinition],
) -> list[ControlDefinition]:
    """Fill domain to target count using golden + themed expansions."""
    domain_rows = [c for c in existing if c.domain == domain]
    if len(domain_rows) >= target:
        return domain_rows[:target]

    themes = _DOMAIN_THEMES.get(domain, [])
    seq = 1
    while len(domain_rows) < target:
        if themes:
            theme_idx = (len(domain_rows) - sum(1 for c in domain_rows if c.is_golden)) % len(themes)
            name, tier, freq, desc_suffix = themes[theme_idx]
            cycle = (len(domain_rows) // len(themes)) + 1
            control_name = f"{name} (cycle {cycle})" if cycle > 1 else name
            description = (
                f"{desc_suffix} Supports EU retail and commercial banking operating model."
            )
        else:
            control_name = f"{domain} operational control {seq}"
            description = f"Supplemental {domain} control for EU universal bank control catalog."
            tier, freq = "Medium", "Quarterly"
            seq += 1

        code = f"{domain}-{len(domain_rows) + 1:03d}"
        # Avoid clashing with golden codes that use same numbering space
        while any(c.control_code == code for c in domain_rows):
            code = f"{domain}-{int(code.split('-')[1]) + 1:03d}"

        domain_rows.append(
            ControlDefinition(
                control_code=code,
                control_name=control_name,
                domain=domain,
                risk_tier=tier,
                owner=DOMAIN_OWNERS[domain],
                frequency=freq,
                description=description,
                is_golden=False,
            )
        )
    return domain_rows


_GOLDEN_SIMILARITY: dict[str, str] = {
    "AML-003": "sanctions-screening",
    "AML-004": "sanctions-screening",
    "AML-005": "transaction-monitoring",
    "KYC-001": "customer-due-diligence",
    "KYC-002": "customer-due-diligence",
    "KYC-003": "customer-due-diligence",
    "FRAUD-001": "payment-fraud",
    "FRAUD-003": "dual-control",
    "FRAUD-005": "dual-control",
    "COMM-001": "dual-control",
    "PHYS-001": "dual-control",
    "ITGC-001": "access-recertification",
    "COMM-004": "access-recertification",
    "TPRM-004": "access-recertification",
    "CYBER-005": "access-recertification",
    "CYBER-002": "incident-response",
    "PRIV-004": "incident-response",
    "TPRM-001": "third-party-register",
    "TPRM-002": "third-party-register",
    "CREDIT-004": "exposure-limits",
    "CREDIT-010": "exposure-limits",
    "TREAS-001": "liquidity-metrics",
    "FIN-001": "regulatory-reporting",
    "FIN-006": "regulatory-reporting",
}


def _apply_similarity_keys(catalog: list[ControlDefinition]) -> list[ControlDefinition]:
    """Tag overlapping / similar controls (intentional duplication across domains)."""
    out: list[ControlDefinition] = []
    for ctrl in catalog:
        key = _GOLDEN_SIMILARITY.get(ctrl.control_code)
        if not key and "Sanctions" in ctrl.control_name:
            key = "sanctions-screening"
        if not key and "dual control" in ctrl.control_name.lower():
            key = "dual-control"
        if not key and "access" in ctrl.control_name.lower() and "recert" in ctrl.control_name.lower():
            key = "access-recertification"
        if not key and ctrl.is_golden:
            key = f"golden-{ctrl.domain.lower()}"
        out.append(
            ControlDefinition(
                control_code=ctrl.control_code,
                control_name=ctrl.control_name,
                domain=ctrl.domain,
                risk_tier=ctrl.risk_tier,
                owner=ctrl.owner,
                frequency=ctrl.frequency,
                description=ctrl.description,
                is_golden=ctrl.is_golden,
                similarity_key=key,
            )
        )
    return out


def build_control_catalog() -> list[ControlDefinition]:
    """Return full EU catalog (300–450 controls) including ≥80 golden MVP controls."""
    golden = _golden_controls()
    if len(golden) < 80:
        raise RuntimeError(f"Expected at least 80 golden controls, got {len(golden)}")

    by_code = {c.control_code: c for c in golden}
    catalog: list[ControlDefinition] = list(golden)

    for domain, target in DOMAIN_TARGETS.items():
        expanded = _expand_domain(domain, target, [c for c in catalog if c.domain == domain])
        for row in expanded:
            if row.control_code not in by_code:
                by_code[row.control_code] = row
                catalog.append(row)

    catalog = sorted(
        by_code.values(),
        key=lambda c: (c.domain, 0 if c.is_golden else 1, c.control_code),
    )
    catalog = _apply_similarity_keys(catalog)
    total = len(catalog)
    if not 300 <= total <= 450:
        raise RuntimeError(f"Catalog size {total} outside 300–450 target")
    golden_count = sum(1 for c in catalog if c.is_golden)
    if golden_count < 80:
        raise RuntimeError(f"Expected at least 80 golden controls, got {golden_count}")
    return catalog
