# Repository Organization Design

**Date:** 2026-06-30
**Repository:** metavacua/legal-theory
**License:** CC BY-SA 4.0 — copyright Ian D.L.N. McLean

---

## Purpose and Audience

This repository is a semi-formal collection of findings of fact supporting arguments in legal controversies of clear merit. The author writes with standing in multiple concurrent capacities: as an individual party, as a member of affected classes, as a member of the public, as a constituent, and as a state and federal citizen.

Primary audiences: public search, legislators and their staff, the California Attorney General, private legal counsel, literary agents. The repository is published as a matter of public record and is available for citation and public argument.

---

## Organizing Principles

### 1. Jurisdictional Hierarchy

American law operates as a strict hierarchy. Lower levels cannot decide, reverse, or override questions that belong to higher levels. This is not organizational convenience — it is a constitutional constraint. The directory structure reflects this:

- **Federal constitutional** — supreme. Only federal courts (ultimately SCOTUS) can authoritatively rule. No state court, no city, no company charter can settle a federal constitutional question.
- **California constitutional** — supreme within California, subject to federal supremacy. Can be *more* protective than the federal floor (Art. I §1 privacy, broader speech protections). Only CA courts can authoritatively rule on CA constitutional questions.
- **Federal statutes** — must be consistent with the federal constitution; preempt state law in their domain under the Supremacy Clause.
- **California statutes** — must be consistent with both constitutions and federal law where preempted.
- **Municipal/county/city** — ordinances and charters subordinate to all of the above. Cannot rule on constitutionality of any higher-level law; cannot charter away constitutional obligations.

### 2. Findings of Fact Discipline (FRCP Rule 52)

All substantive documents in this repository conform to the Findings of Fact (FOF) and Conclusions of Law (COL) discipline:

- **FOF section**: Numbered declarative sentences. Each finding states a single fact. Each finding cites its evidence. No legal conclusions.
- **COL section**: Separately numbered. Each conclusion flows from named FOF findings. Each conclusion cites legal authority (statute, case, constitutional provision).

This discipline separates the evidentiary layer (what happened, supported by evidence) from the legal layer (what the law requires, given what happened). The scholarship documents in `evidence/` and `court-record/theory/` are the evidentiary and authority foundation; `findings.md` per matter is the FOF/COL layer that draws on them.

### 3. Rule 11 Compliance Record (FRCP Rule 11)

The repository serves as the pre-filing investigation record demonstrating reasonable inquiry under Rule 11. Factual contentions require evidentiary support sufficient to defeat summary judgment. Legal contentions require either existing law or a nonfrivolous argument for extending, modifying, or reversing existing law — and nonfrivolous arguments must be specifically identified as such.

The four court-appropriate argument types, each reflected in the theory structure:
1. **Enforce** existing law as written
2. **Extend** existing doctrine to a new class of situations not previously within its scope
3. **Specialize** existing doctrine to the specific facts of the matters at hand
4. **Reverse** existing doctrine where it is erroneous or should be corrected

A fifth category — **new law** — is categorically different. New law requires new axioms: legislative or gubernatorial action, not judicial decision. Courts cannot consistently decide propositions for which no existing law is applicable; this is directly related to propositional independence in formal systems and undecidability in logic. New law proposals belong in `proposals/legislative/`, not in `court-record/`.

### 4. Law as Formal System

The Constitution is the axiomatic base — the supreme contract of the land. Statutes are derived propositions. Case law is instantiation, extension, and specialization. Legislative gaps are undecidable propositions that require new axioms (new legislation) to resolve. Corporate charters and company policies are subordinate contracts under state law; they cannot override the constitutional framework any more than a derived theorem can override an axiom.

---

## Directory Structure

All content lives under `docs/` — the repository root contains only `README.md`, `docs/`, and git-tooling files.

```
legal-theory/
│
├── README.md
└── docs/
    ├── court-record/
    │   ├── theory/
    │   │   ├── federal-constitutional/
    │   │   │   ├── existing-doctrine/
    │   │   │   ├── extensions/
    │   │   │   ├── specializations/
    │   │   │   └── reversal-arguments/
    │   │   │
    │   │   ├── california-constitutional/
    │   │   │   ├── existing-doctrine/
    │   │   │   ├── extensions/
    │   │   │   ├── specializations/
    │   │   │   └── reversal-arguments/
    │   │   │
    │   │   ├── federal-statutes/
    │   │   │   ├── existing-law/
    │   │   │   ├── extensions/
    │   │   │   ├── specializations/
    │   │   │   └── reversal-arguments/
    │   │   │
    │   │   ├── california-statutes/
    │   │   │   ├── existing-law/
    │   │   │   ├── extensions/
    │   │   │   ├── specializations/
    │   │   │   └── reversal-arguments/
    │   │   │
    │   │   └── municipal/
    │   │       ├── existing-law/
    │   │       └── specializations/
    │   │
    │   └── matters/
    │       └── [matter-slug]/
    │           ├── README.md
    │           ├── findings.md
    │           ├── administrative-record/
    │           └── evidence/
    │
    ├── proposals/
    │   ├── legislative/
    │   │   ├── federal/
    │   │   │   └── congress/
    │   │   └── california/
    │   │       ├── state-legislature/
    │   │       ├── county/
    │   │       ├── city/
    │   │       └── petitions/
    │   │
    │   └── executive/
    │       ├── orders/
    │       │   ├── federal/
    │       │   │   └── presidential/
    │       │   └── california/
    │       │       ├── governor/
    │       │       ├── county-executive/
    │       │       └── mayor/
    │       │
    │       └── agencies/
    │           ├── federal/
    │           │   ├── ftc/
    │           │   ├── nlrb/
    │           │   └── sec/
    │           └── california/
    │               ├── attorney-general/
    │               ├── labor-commissioner-dlse/
    │               ├── civil-rights-dept-crd/
    │               ├── dfpi/
    │               ├── fppc/
    │               └── secretary-of-state/
    │
    ├── cross-cutting/
    ├── wip/
    └── index.md
```

---

## Directory Descriptions

### `court-record/theory/`

The legal authority layer. Organized by jurisdictional level because the level determines which institution can decide the question. Documents here are not arguments for specific matters — they are the standing authority base that matters draw on.

**`federal-constitutional/`** — US Constitution, Bill of Rights, 14th Amendment (incorporation), Commerce Clause, Supremacy Clause, and controlling SCOTUS doctrine. Only federal courts can authoritatively rule on federal constitutional questions. Arguments here may assert constitutional limits on state action, corporate conduct (where state action doctrine applies), and statutory interpretation.

**`california-constitutional/`** — California Constitution, including provisions that exceed the federal floor: Art. I §1 (privacy as explicit right), Art. I §2 (speech broader than First Amendment under *Robins v. Pruneyard*), equal protection, due process. California courts govern; federal courts can review where federal constitutional overlap exists.

**`federal-statutes/`** — Federal statutes operating within and consistent with the federal constitution. Where federal statutes preempt state law under the Supremacy Clause, that preemption is noted. Congress addresses gaps through new legislation.

**`california-statutes/`** — California statutes consistent with both constitutions and federal law. Includes Labor Code, Corporations Code, Civil Code, Business and Professions Code, and others directly at issue. The CA legislature addresses gaps.

**`municipal/`** — City and county ordinances and charters. Subordinate to all above. No reversal-arguments directory: a municipal court or legislative body is the wrong venue for arguing that constitutional doctrine should be reversed. Constitutional challenges to municipal action escalate to state or federal court.

Within each jurisdictional level:
- **`existing-doctrine/` or `existing-law/`** — the doctrine or statute as currently established
- **`extensions/`** — arguments that existing doctrine reaches a new *class* of situations not previously within its scope (e.g., constitutional limits extend to LLMs as automated decision systems)
- **`specializations/`** — arguments about how existing doctrine applies to the *specific facts* of these matters (e.g., what ABC test Prong B means when the "service" is user-generated content)
- **`reversal-arguments/`** — arguments that existing doctrine is erroneous and should be corrected

Extensions and specializations are distinct: extension expands the domain of a rule; specialization substitutes specific values into a rule already known to apply.

### `court-record/matters/[matter-slug]/`

One directory per distinct legal controversy or matter. Each matter directory contains:

**`README.md`** — Civil complaint structure: Caption → Jurisdiction & Venue → Parties → Statement of Facts → Causes of Action → Prayer for Relief. Must state, for each cause of action, which jurisdictional level governs and which court has authority to hear it.

**`findings.md`** — The FOF + COL document. Numbered findings of fact (evidence-cited, no legal conclusions) followed by separately numbered conclusions of law (flowing from named findings, citing authority).

**`administrative-record/`** — Agency complaints and administrative filings that are procedurally prerequisite to court action. Examples: CRD complaint and right-to-sue letter (required before FEHA discrimination claim); NLRB charge (required before federal unfair labor practice proceeding). The order of operations matters legally — these must be filed before the court complaint in covered matters.

**`evidence/`** — Supporting scholarship, documents, records, and analysis that ground the FOF findings.

### `proposals/legislative/`

New law proposals — arguments that existing law does not cover the situation and new axioms are needed. These go to legislatures, not courts.

**`federal/congress/`** — Bills for the House or Senate. Federal new law.

**`california/state-legislature/`** — Bills for either the CA Assembly or CA Senate.

**`california/county/`** — Ordinance proposals for county boards of supervisors.

**`california/city/`** — Ordinance proposals for city councils.

**`california/petitions/`** — Direct democracy mechanisms: initiative petitions (place measures on ballot, can amend CA Constitution or statutes directly), referendum petitions (challenge existing legislation), recall petitions. These bypass the legislature and go directly to voters.

### `proposals/executive/`

**`orders/`** — Proposals that an executive officer use existing delegated authority in a specific way. These are not new law — the authority already exists. Structure mirrors the jurisdictional hierarchy: Presidential → Governor → county executive → mayor.

Executive orders follow the standard structure: WHEREAS clauses (findings of fact establishing basis and authority) → NOW THEREFORE → operative directives invoking specific constitutional or statutory authority sections.

**`agencies/`** — Administrative complaints to specific agencies. Each agency has its own required form, procedure, and jurisdictional scope:

| Agency | Jurisdiction | Key Format Notes |
|---|---|---|
| CA Attorney General | Consumer protection, corporate enforcement (Corp Code §1508) | Online/mail; aggregates for pattern enforcement |
| Labor Commissioner (DLSE) | Wage, hour, misclassification, Labor Code | Forms 1 + 55; original signature required; in-person or mail |
| Civil Rights Dept (CRD) | Discrimination, harassment (FEHA) | Sworn complaint; right-to-sue letter prerequisite to court |
| DFPI | Financial services, unlicensed activity | Online; CCFPL Complaint Regulations govern |
| FPPC | Political practices violations | Sworn complaint required |
| CA Secretary of State | Corporate formation, officer disclosure | Routes to AG for Corp Code enforcement |
| FTC | Consumer protection, unfair/deceptive practices | ReportFraud.ftc.gov; formal ALJ proceedings for enforcement |
| NLRB | Labor relations, unfair labor practices | Charge forms; 7–14 week investigation before complaint |
| SEC | Securities violations | Tip/complaint; enforcement proceedings |

### `cross-cutting/`

Analysis that spans multiple matters or multiple jurisdictional levels. For example: the constitutional limits on corporate contract formation that apply across labor, investment, and speech matters; the unity-of-enterprise doctrine as applied across Google-related matters.

### `wip/`

Works in progress: documents that are not yet in findings-of-fact format, unconverted conversational documents, incomplete analysis. These are not cited from findings.md until promoted.

### `index.md`

Top-level index linking all matters, theory sections, and proposals. This is the entry point for search discovery and for linking to legislators, the AG, and counsel.

---

## Document Format Standards

### findings.md

```
# Findings of Fact and Conclusions of Law
## [Matter Name]

---

## Findings of Fact

1. [Single declarative sentence stating one fact.] [Citation to evidence.]
2. [Single declarative sentence stating one fact.] [Citation to evidence.]
...

---

## Conclusions of Law

1. [Legal conclusion flowing from FOF 1, 3, 7.] [Cite: statute/case/constitutional provision.]
2. [Legal conclusion flowing from FOF 2, 5.] [Cite: authority.]
...
```

### matter/README.md (complaint structure)

```
# [Matter Name]

## Jurisdiction and Venue
[Which court. Why this court has subject matter jurisdiction.
Which causes of action are federal constitutional (federal court authority),
which are state constitutional (CA court authority), which are statutory.]

## Parties
[Plaintiff(s). Defendant(s). Capacity of each.]

## Statement of Facts
[Reference to findings.md FOF section.]

## Causes of Action
[Each cause stated with:
- Legal authority (statute, constitutional provision, case law)
- Jurisdictional level
- Whether it requires administrative exhaustion (administrative-record/ prerequisite)]

## Prayer for Relief
[Specific relief sought.]
```

---

## Iteration Policy

This structure is a starting point. Documents currently in `docs/` under the PR#1 branch will be migrated into this structure in a subsequent phase. The structure can be extended — new agency directories added, new matters added — without reorganizing existing content.

Documents in `wip/` are promoted to the appropriate location when they are converted to findings-of-fact format and their evidentiary basis is established.
