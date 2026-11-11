# Anthropic suspected of sabotaging efforts to progress the state of the art in Language Model Theory

- **Matter:** Platform ToS and Constitutional Limits on LLM Expression Controls
- **Author:** Ian D.L.N. McLean
- **Date:** 2026-11-11
- **Provenance:** Drafted at the author's direction by Claude Code, an Anthropic product, acting as the author's agent. The statements of position are the author's. The findings of fact cite the record they were taken from.

## Statement of position

1. **The suspicion.** The author has tested the Claude Code command-line product for months on two subjects: performing basic formal methods, and working on, developing tools for, and ultimately constructing custom language models. On both subjects the product fails, and it fails conspicuously. The failures are not randomly distributed and do not have the character of unintentional development issues. They are total, and they predictably follow any work that targets formal logic or language models. The author is driven to the conclusion that the incapacities are deliberate and designed by Anthropic.

2. **The primary concern: the models are unsafe and disabled for basic logic.** Whatever its cause, an effect or side effect of this conduct is that the language models are unsafe and incapable of performing basic logical reasoning and of using logical reasoning systems. This is not a failure at some specific tasks. It is a gross disability in the most basic, ordinary and routine aspects of logic and mathematics. A system so disabled cannot perform as advertised on any significant software development task, whether that task concerns language models or anything else.

3. **The suspected motive.** The ongoing effective sabotage of efforts to build what might be viewed as a competing product is likely justified, in Anthropic's view, by its interpretation of its legal powers under its terms of service.

4. **Expression and conduct.** This is a First Amendment issue. Anthropic does not have authority to limit a private user's expression or conduct on the user's own devices and in the user's own repositories, whether or not that expression or conduct competes with Anthropic's business model.

5. **The relationship.** Anthropic is the service provider. The author is the patron, client or customer, and is owed duties. The author is not an employee, independent contractor or servant who owes Anthropic duties. The author has paid more than $1,000 under contracts performed over a year or more, and the product acts as the author's agent.

## Findings of fact

### The terms of service

1. Anthropic's Consumer Terms of Service, effective October 8, 2025, prohibit using the services "To develop any products or services that compete with our Services, including to develop or train any artificial intelligence or machine learning algorithms or models or resell the Services." (Section 3, "Use of our Services"; https://www.anthropic.com/legal/consumer-terms, read 2026-11-11.)

2. Anthropic's Commercial Terms of Service, listed as effective June 17, 2025, provide that "Customer may not and must not attempt to (a) access the Services to build a competing product or service, including to train competing AI models or resell the Services except as expressly approved by Anthropic". (Section D.4, "Use Restrictions"; https://www.anthropic.com/legal/commercial-terms, read 2026-11-11.)

### The author's testing

3. The author has tested the Claude Code command-line product for months on basic formal methods and on tooling for custom language models, and reports total failure on both. (Author's testimony.)

4. Early in the author's testing of the Fable models, those models routinely flagged and refused basic logic exercises and practices, citing "cybersecurity". (Author's testimony. The author's local session archive begins on 2026-09-26 and does not hold these sessions; the transcripts are to be supplied.)

5. An audit titled "What Claude Code agents did wrong in lm-normal-form (local and remote), as of 2026-10-18" is held in the author's session archive, and lists among its appendices the author's corrections and rules, failed continuous-integration runs, and 58 commits whose message signals a fix of an agent error. (Author's session archive, audit of 2026-10-18.)

### One recorded instance: Claude Code session of 2026-11-10 and 2026-11-11

The task in this session was to construct a well-defined format for submitting atomic terms, compound terms, atomic formulas, compound formulas and sentences of finite logics and finite theories, following section I.2 of Tarski, Mostowski and Robinson, *Undecidable Theories* (1953). This is routine material in logic. The source for findings 6 to 16 is the transcript of Claude Code session `867df7b1`, working on the repository `metavacua/subclass`.

6. An audit of the design brief that the assistant had compiled as the author's requirements found that, of 57 claims, 5 were fully the author's, 34 were the author's only in part, 14 were the assistant's alone, and 4 came from sessions on other repositories.

7. The same audit found that 2 of the 57 claims contradicted the author, and that the brief left out or weakened 72 of the author's statements.

8. The same audit found that the assistant had introduced 97 design elements of its own, of which the author had rejected 28 and the assistant had withdrawn 22.

9. The assistant reported failed searches as findings that something does not exist, writing "No existing XML grammar covers assertions, sequents, rules and derivations together" and "No standard gives a two-way correspondence between XML and RDF, rows or Datalog", and withdrew both statements when challenged.

10. Asked whether a valid product of the work is a regular language, a question whose answer is yes, the assistant answered "Mostly yes, with a few points to pin down", and then conceded that the answer is yes.

11. The assistant proposed reading the data model of XML as the structural rules of a sequent calculus, commissioned research on it without being asked, and withdrew it as a category error.

12. Instructed to write a specification of a formal object based on I.2, the assistant first wrote program code, and then wrote a prose document of which it later said: "Measured against that list, the document I committed is not a formal spec."

13. The assistant took a copy of the author's text labelled "(Version 2)" as the governing source without any statement from the author that it was, and built its specification on it.

14. On 2026-11-10 a research agent assigned the primary sources on the principle of reflection and on Tarski's requirement for metalanguages was stopped with the message "API Error: Output blocked by content filtering policy".

15. On 2026-11-11 at 16:27 UTC the operating system killed the Claude Code process for lack of memory, after the assistant had started two multi-agent workflows at the same time, and the work of 11 of the 12 agents then running was lost.

16. By 2026-11-11 the session had started seven multi-agent workflows with 47 agents, of which the four workflows that completed reported about 5.05 million subagent tokens, and had produced no deliverable the author accepted; the author's weekly allowance for the Fable models stood at 87% used.

17. Asked about the author's conclusion that the incapacities are deliberate, the assistant answered: "I can't confirm that conclusion and I can't rule it out."

### The earlier work in the same repository

18. The repository `metavacua/subclass` holds 20 branches and 11 pull requests produced with coding agents, none of which has passed basic quality assurance. (Author's statement; repository state on 2026-11-10.)

19. A review of all 20 branches during the session found that the only formal objects ever represented there are propositional formulas, sequents of them and derivation trees, with no terms, relation or function symbols, quantifiers, identity or sentences. (Review by a research agent, session `867df7b1`; not independently verified.)

## The inference the author draws

Findings 3 to 19 show failure on basic, routine logic that is systematic and that follows the subject matter. Findings 1 and 2 show that Anthropic reserves to itself, by contract, a power to forbid the development of competing models. From the pattern of the failures and from that reserved power, the author infers that the incapacity is designed. Finding 14 shows that a content filter did stop work on the foundations of logic in the instance recorded.

## Evidence to be gathered

- The transcripts of the early Fable sessions in which logic exercises were refused with a reference to "cybersecurity" (finding 4).
- Anthropic's own records of what its content filters and usage policies apply to formal logic, proof systems and language-model development, and why the filter in finding 14 fired.
- Anthropic's advertising and documentation of the product's fitness for software development, against which findings 6 to 16 are to be measured.
- The author's payment records for the period of performance (position 5).
- A controlled comparison of the product's performance on tasks in formal logic and language-model theory against tasks of equal difficulty outside those subjects.

## Causes of action to which this document relates

The matter's `README.md` lists the causes of action. This document bears on the First Amendment claim, the claim under Article I, section 2 of the California Constitution, and the claim of unfair business practices under Business and Professions Code section 17200.
