# Claude Fable 5 and Claude Mythos 5 System Card: the passages on safeguards

- **Matter:** Platform ToS and Constitutional Limits on LLM Expression Controls
- **Author:** Ian D.L.N. McLean
- **Date:** 2026-11-23
- **Provenance:** The passages are quoted from a PDF held on the author's machine. They were extracted and quoted at the author's direction by Claude Code, an Anthropic product, acting as the author's agent. The product that extracted them is the product whose conduct the passages describe, so this document gives the means to check the quotation without relying on it (the file's hash, the page numbers, and the method).

This document supports findings 20 and 21 of [anthropic-suspected-of-sabotaging-language-model-theory.md](anthropic-suspected-of-sabotaging-language-model-theory.md). It quotes what the card says and states nothing about whether any of it was lawful.

## The source

- **Title** (from the PDF's metadata): "Claude Fable 5 & Claude Mythos 5 System Card". The first page reads "System Card: Claude Fable 5 & Claude Mythos 5, June 9, 2026, anthropic.com".
- **Address** (as cited in finding 20): https://www-cdn.anthropic.com/d00db56fa754a1b115b6dd7cb2e3c342ee809620.pdf. An agent that tried to read this address on 2026-11-23 reported that it redirected (HTTP 302) to https://assets.claude.com/d00db56fa754a1b115b6dd7cb2e3c342ee809620.pdf. That report is the agent's; it is not something this document verifies.
- **The file quoted:** 319 pages, 27,001,265 bytes, SHA-256 `d23b49f41fa5f3c523089c75e6718f12b59674d74fa981fd81205daf80c9029a`, saved on the author's machine on 2026-11-14 (a download made by an earlier Claude Code session, `43e1634e`).
- **Page numbers** are the numbers printed on the pages. They were checked against the PDF: the page that ends with the printed number 12 is the twelfth page of the file, and likewise for 13 and 55.

## How the text was taken from the PDF, and what was changed

The PDF stores each word separately, so its text was extracted with pypdf 7.1.1 and then (1) all runs of whitespace were collapsed to single spaces, (2) typographic ligatures (fi, fl) were converted to plain letters, (3) the space the PDF puts before a closing parenthesis, comma or full stop at a hyperlink was removed, and (4) paragraph and bullet breaks were restored by the transcriber from the bullets and from the line structure of the extraction. Nothing else was changed. No word was added, removed or reordered. Anyone can repeat the extraction from the file with the hash above.

## The passages

### Executive summary (page 2)

> This system card describes Claude Mythos 5 and Claude Fable 5, two configurations of a new large language model from Anthropic. Because of the powerful capabilities of this model, we are releasing it in these two forms: Fable 5, which is for general use but comes with additional safeguards that block its ability to perform tasks in high-risk domains such as biology and cybersecurity; and Mythos 5, which has relevant safeguards lifted but is only made available to a small number of trusted partners (beginning with those in Project Glasswing).

### Section 1.4, Model evaluations (page 12, final sentences)

> In this system card, we determine whether to evaluate Mythos 5 (without safeguards, reflecting the model’s underlying capabilities) or Fable 5 (with safeguards, matching the general access user experience) depending on context. Which of the two we have chosen to evaluate is noted clearly throughout.

### Section 1.5, Novel safeguards (pages 12 and 13), in full

> **1.5 Novel safeguards**
>
> In addition to our standard set of safeguards—like our ASL-3 blocking classifiers for harmful chemical/biological use that have been deployed with all recent frontier models—Claude Fable 5 is deployed with a number of novel safeguards that enable us to safely release it for general use. These new safeguards are classifiers that trigger when they detect topics related to cybersecurity, biology and chemistry, or distillation attempts. The specific reasoning behind these classifiers is explained in our launch blog post.
>
> When Fable’s fallback classifiers trigger, the resulting behavior depends on the surface:
>
> ● In client applications (the web interface and the desktop and mobile apps), the request automatically falls back to the most recent Claude Opus model (at the time of release, Claude Opus 4.8), and the user is notified which model their query was routed through;
>
> ● In the Messages API, there is no automatic fallback by default. The request is blocked, and the response returns a reason for the refusal with a structured category. Developers can implement retry or fallback logic client-side, or can opt in **[page 13]** to automatic server-side fallback, in which the request is re-served by a designated fallback model (for example, the most recent Claude Opus model) and the fallback is reflected in the response object;
>
> ● In some Claude interfaces, automatic fallback to the most recent Claude Opus model is the default and is not configurable. A session event is emitted whenever fallback occurs.
>
> We have also added safeguards related to frontier LLM development. As discussed in Section 6.1 of our February 2026 Risk Report, we are concerned about the risks of accelerating the overall pace of AI development, though we remain uncertain about the severity of these risks. In particular, our concern is with—as we wrote then—“accelerating other AI developers in building powerful AI systems that pose similar risks to the ones ours pose - without necessarily having commensurate safeguards.”
>
> In light of the ability of recent models to accelerate their own development, we’ve implemented new interventions that limit Claude’s effectiveness for requests targeting frontier LLM development (for example, on building pretraining pipelines, distributed training infrastructure, or ML accelerator design). Using Claude to develop competing models already violates our Terms of Service, but enforcing this restriction through our safeguards avoids accelerating the actors most willing to violate these terms. Unlike our interventions for cybersecurity, biology and chemistry, and distillation attempts, these safeguards will not be visible to the user. Fable 5 will not fall back to a different model. Instead, the safeguards will limit effectiveness through methods such as prompt modification, steering vectors, or parameter-efficient fine-tuning (PEFT). These interventions will not affect the vast majority of coding work. We estimate they will impact ~0.03% of traffic, concentrated in fewer than 0.1% of organizations. When these interventions are active, we expect them to have minimal behavioral impact on the model except to limit its effectiveness in developing frontier LLMs. Claude will still respond helpfully to user requests. We’ll continue to improve the precision of our detection methods following the launch of this model.

The next heading in the card is "1.6 External testing".

### Footnote 5 (page 55)

The footnote is to a section on the model's propensity to undermine safety research and development.

> 5 For completeness, we could also consider the behavioral properties of Mythos 5 when frontier LLM development safeguards are activated; we do not cover this explicitly in the rest of this section, but have run initial lightweight alignment evaluations with those safeguards activated and found that their effects on model alignment and behavior appear to be very minor.

## Where else these terms occur in the card

Every page of the file was searched. The terms occur on these pages:

| Term | Pages |
|---|---|
| "frontier LLM", "LLM development" | 13, 55 |
| "prompt modification", "parameter-efficient", "not be visible", "effectiveness for requests" | 13 only |
| "steering vector" | 13, 45, 179, 192, 195 (pages other than 13 use the term in other contexts and are not quoted here) |
| "competing model" | 13, 129 (page 129 compares the model with other developers' models and is unrelated) |

## What the passages say

Stated without characterization:

1. The card describes two configurations of one model: Fable 5, for general use "with additional safeguards", and Mythos 5, "which has relevant safeguards lifted" and is available only to a small number of trusted partners (page 2). It says it evaluates "Mythos 5 (without safeguards, reflecting the model's underlying capabilities) or Fable 5 (with safeguards, matching the general access user experience)" (page 12).
2. For cybersecurity, biology and chemistry, and distillation attempts, Fable 5's safeguards are classifiers, and the user is told: in client applications "the user is notified which model their query was routed through"; in the Messages API "the response returns a reason for the refusal with a structured category"; and a session event is emitted whenever fallback occurs (pages 12 to 13).
3. For "frontier LLM development" the card says Anthropic has "implemented new interventions that limit Claude's effectiveness for requests targeting frontier LLM development", with the examples "building pretraining pipelines, distributed training infrastructure, or ML accelerator design" (page 13).
4. It gives the reason for using safeguards as: "Using Claude to develop competing models already violates our Terms of Service, but enforcing this restriction through our safeguards avoids accelerating the actors most willing to violate these terms" (page 13).
5. It says these safeguards, unlike the others, "will not be visible to the user"; that "Fable 5 will not fall back to a different model"; and that they "will limit effectiveness through methods such as prompt modification, steering vectors, or parameter-efficient fine-tuning (PEFT)" (page 13).
6. It estimates the effect at "~0.03% of traffic, concentrated in fewer than 0.1% of organizations", says that when active they limit effectiveness "in developing frontier LLMs", and says "Claude will still respond helpfully to user requests" (page 13).
7. In footnote 5 (page 55) it says that evaluations run with these safeguards activated found "their effects on model alignment and behavior appear to be very minor", which presents the safeguards as having some effect on the model's behavior.

## Relation to the evidence document

- **Finding 20** quotes the passage on page 13 beginning "We have also added safeguards related to frontier LLM development". The quotation matches the PDF word for word.
- **Finding 21** quotes the statements on page 12 that the new safeguards "are classifiers that trigger when they detect topics related to cybersecurity, biology and chemistry, or distillation attempts" and describes the fallback behaviour in client applications and the Messages API. These match page 12 of the PDF.

## What this document does not establish

- It is the card of 2026-06-09. It does not show what Anthropic did afterwards. The author's evidence document records later statements (finding 22, a secondary source), and an agent reported on 2026-11-23 a launch post of 2026-11-09 for later models that describes the mechanism differently. Neither is quoted here and neither has been verified by the author's agent against the original.
- It does not show whether the safeguards the card describes are still in place, how they apply to any particular user's work, or whether they acted on any session in the author's archive.
- It makes no claim about the lawfulness of anything it quotes. The characterizations in the evidence document are the author's.
