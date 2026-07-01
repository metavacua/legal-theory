# **A Formalized Legal and Data Framework for AI-Assisted Copyrightable Works**

  
  

## **Introduction: Navigating Copyright in the Age of Generative AI**

  
  

### **Problem Statement**

  

The proliferation of sophisticated generative artificial intelligence (AI) tools has created a critical legal and technical ambiguity at the heart of creative industries. Systems capable of producing text, images, and music that are aesthetically indistinguishable from human-created works challenge the foundational principles of intellectual property law.1 The central challenge is to delineate the boundary between a human-authored, AI-assisted work eligible for copyright protection and a machine-generated work that falls into the public domain. This ambiguity poses significant risks for creators, who need clarity on the protectability of their efforts; for technology platforms, which must manage liability and define terms of service; and for investors, who require a stable legal framework to assess the value of AI-driven enterprises.4 Without a clear, operational framework, innovation may be stifled by legal uncertainty, and the economic incentives that copyright is designed to foster may be undermined.3

  

### **Report's Objective and Scope**

  

This report provides a comprehensive, expert-level analysis of the legal doctrines governing AI-assisted works and related creative practices like sampling and remixing. Its primary objective is to translate these complex legal standards into a formalized data schema and a set of logical conditions. This framework is designed to be directly implemented within an AI-assisted creative tool to guide users, assess copyrightability in real-time, and manage intellectual property risk. The scope of this analysis is centered on United States copyright law, synthesizing the latest guidance from the U.S. Copyright Office (USCO), seminal and recent federal court decisions, and established legal doctrines of fair use, transformative use, and *de minimis* copying. The report culminates in a unified data model that provides a technical blueprint for a system of "Copyright Provenance," enabling an auditable and legally-grounded approach to modern creation.

  

### **Methodology**

  

The analysis synthesizes the latest guidance from the U.S. Copyright Office (USCO), seminal and recent federal court decisions, established legal doctrines of fair use and transformative use, and existing technical standards for data provenance. The report builds from foundational legal principles to concrete, actionable guidelines and a unified data model. It examines the USCO's multi-part report on AI, key judicial precedents including *Thaler v. Perlmutter* and *Andy Warhol Foundation v. Goldsmith*, and the statutory framework of the Copyright Act. By deconstructing these legal sources into their constituent logical parts, the report constructs a schema capable of capturing the legally significant events in the lifecycle of a creative work, from initial prompt to final human modification. This approach bridges the gap between abstract legal theory and concrete technical implementation, providing a robust foundation for the development of legally-compliant creative tools.

  

## **Part I: The Foundation of Copyrightability: Human Authorship in the AI Era**

  

The legal system's response to the advent of generative AI has not been to invent new legal paradigms, but rather to mount a vigorous defense of its most foundational principle: that copyright is an exclusively human right. This reaction is not merely an interpretation of statutory text but a reaffirmation of the constitutional, economic, and philosophical underpinnings of American intellectual property law. The consistent position of the legislature, the courts, and the primary administrative body for copyright is that for a work to be protected, it must originate from a human mind.

  

### **The Constitutional and Statutory Mandate for a Human Author**

  

The requirement for human authorship is deeply rooted in the U.S. Constitution and the subsequent statutes enacted under its authority. The Copyright Clause grants Congress the power to "secur\[e\] for limited Times to Authors... the exclusive Right to their respective Writings".7 The Supreme Court's earliest interpretations of this clause established a direct link between the concepts of "author" and "human intellect." In the seminal 1884 case

*Burrow-Giles Lithographic Co. v. Sarony*, the Court confronted the question of whether a photograph—a work created with the aid of a machine—could be copyrighted. It concluded that it could, but only insofar as the photograph was a representation of the photographer's "original intellectual conceptions".8 The Court defined an "author" as "he to whom anything owes its origin; originator; maker," consistently framing the role in human terms as a product of a person's "genius or intellect".9

This foundational understanding has been carried forward into modern copyright law. The Copyright Act of 1976, which governs current law, provides protection for "original works of authorship".11 While the Act does not explicitly define "author" to mean "human," the entire structure of the law—with its provisions on duration based on the author's life, termination rights, and inheritance—presupposes a human creator.12 The USCO and federal courts have consistently interpreted this statutory silence not as an ambiguity, but as an implicit adoption of the long-standing, human-centric understanding established in cases like

*Burrow-Giles*.12 The legal system's reaction to generative AI, therefore, can be understood as a robust "doctrinal immune response." Faced with a novel technological entity capable of producing expressive works, the system has not mutated but has instead reinforced its core identity, vigorously reasserting the human authorship doctrine to defend the philosophical and economic purpose of copyright law: to provide incentives for human creativity.8 This strong, defensive posture suggests that any future arguments for machine authorship will face immense doctrinal resistance. The path to copyrightability for works made with AI lies not in supplanting the human, but in meticulously documenting the human's role as the master of the AI tool.

  

### **The USCO's Modern Stance: A Rejection of Machine Authorship**

  

In response to the rapid development of generative AI, the U.S. Copyright Office launched a broad initiative in 2023 to study its implications.14 The resulting multi-part report, particularly Part 2 on the Copyrightability of AI-Generated Works, represents the definitive administrative position on the matter. The Office's primary conclusion is that "existing principles of copyright law are flexible enough to apply to this new technology".14 This statement signals a clear policy preference for applying established legal doctrines rather than seeking new legislation to create sui generis rights for AI-generated material.

The core of the USCO's guidance is its finding that copyright can protect AI-generated outputs "only where a human author has determined sufficient expressive elements".14 This principle is the central pivot upon which all subsequent analysis turns. The Office explicitly rejects the notion that a machine can be an author, stating that extending protection to material whose expression is determined by a machine would "undermine rather than further the constitutional goals of copyright".14 To enforce this principle, the USCO has issued registration guidance that imposes a duty on applicants to disclose the inclusion of AI-generated content in any submitted work. Applicants must provide a clear explanation of the human author's contributions and disclaim any copyright in the portions of the work that were "generated by AI".8 This procedural mandate is not merely administrative; it transforms the human/machine distinction into a material fact that is legally essential for a valid copyright registration.

While the United States has solidified its human-only stance, this position is not universal. Other jurisdictions have shown greater flexibility, creating a potential for significant friction in the global digital marketplace. The United Kingdom, for example, explicitly recognizes "computer-generated" works in its copyright statute, assigning authorship to "the person by whom the arrangements necessary for the creation of the work are undertaken".10 Similarly, a court in China has granted copyright protection to an AI-generated image, reasoning that the user's intellectual investment in the prompt and selection process was sufficient to constitute authorship.18 This divergence in legal philosophy will inevitably lead to differing outcomes for identical creative processes. A work generated through a specific workflow in the U.S. may be relegated to the public domain, while the same work created via the same process in the U.K. or China could be protected intellectual property. This fragmentation complicates international licensing, enforcement, and investment for any platform operating on a global scale and underscores the need for any copyright-aware tool to be designed with jurisdictional adaptability in mind.3

  

### **Judicial Affirmation: The Thaler v. Perlmutter Line of Cases**

  

The USCO's administrative position has been unequivocally affirmed by the federal judiciary. The landmark case in this area is *Thaler v. Perlmutter*, in which computer scientist Stephen Thaler sought to register a copyright for an image he claimed was created "autonomously" by his AI system, the "Creativity Machine".10 The USCO refused registration, and Thaler sued.

In August 2023, the U.S. District Court for the District of Columbia granted summary judgment to the Copyright Office, holding that "human authorship is an essential part of a valid copyright claim".7 The D.C. Circuit Court of Appeals affirmed this decision in March 2025, providing a thorough analysis that solidifies the human authorship requirement in U.S. law.12 The court's reasoning was twofold. First, it found that the text of the Copyright Act, "taken as a whole," makes clear that authors must be human.12 Second, and perhaps more importantly, the court addressed the underlying policy rationale for copyright. It dismissed Thaler's argument that denying copyright to AI works would disincentivize creativity, noting that the human authorship requirement still incentivizes humans to create works

*with the assistance* of AI.12 The court pointed out that machines, unlike humans, do not respond to the economic incentives that copyright provides, and therefore, extending protection to them would not serve the constitutional purpose of promoting "the Progress of Science and useful Arts".8

This ruling places AI-generated works in the same legal category as other works created by non-human actors. Courts have previously rejected copyright claims for a book purportedly dictated by a "non-human spiritual being" and for photographs taken by a monkey in the famous "monkey selfie" case, *Naruto v. Slater*.7 The

*Thaler* decision confirms that AI, for all its sophistication, is viewed by the law as another non-human agent incapable of authorship. The legal question is therefore no longer *whether* a human is required, but *what level* of human involvement is sufficient to claim authorship of a work that incorporates AI-generated material.

  

## **Part II: Formalizing the Conditions for an "AI-Assisted Copyrightable Work"**

  

Having established that human authorship is a non-negotiable prerequisite for copyright, the analysis must now shift from the "what" to the "how." The central task is to deconstruct the USCO's guidance into a set of formal, logical conditions that can distinguish a copyrightable act of human creation from an uncopyrightable act of machine generation. This requires identifying the specific human interventions that the law recognizes as sufficiently creative and understanding why other actions, such as the mere crafting of prompts, are deemed insufficient.

  

### **The Spectrum of Human Involvement: AI as Tool vs. AI as Author**

  

The copyrightability of works involving AI exists on a spectrum defined by the degree of human creative control.8 At one end of this spectrum, AI functions as a simple, assistive tool, much like a word processor's spell-checker or a photo editor's color-correction filter. In these cases, where the human author maintains full control over the expressive elements of the work, the use of AI has no bearing on the work's copyrightability.16 The human author creates a work, and the AI merely refines or assists in its execution.

At the other extreme lies a work "autonomously" created by an AI system, where a human simply provides a prompt and the machine generates a complex and complete work in response.9 As established in

*Thaler*, such a work lacks human authorship and is not copyrightable; it falls immediately into the public domain.12

The legally complex and commercially critical territory lies in the middle of this spectrum: hybrid works that incorporate substantial AI-generated material but are also shaped by a human hand. For these works, the USCO has made clear that copyrightability must be determined through a case-by-case inquiry that scrutinizes the "quantum of human creative contribution".16 The dispositive question is whether a human exercised sufficient creative control over the final expression of the work.

  

### **Copyrightable Human Interventions: The "Sufficient Creative Control" Test**

  

The USCO's guidance and registration decisions have identified three primary categories of human intervention that may be sufficient to meet the standard for authorship, even when the raw material is generated by an AI. These interventions represent a fundamental shift in the locus of legally significant creativity. In traditional authorship, the creative act is primarily one of conception and initial expression. In the context of generative AI, however, the USCO explicitly rejects the initial conception (the prompt) as a basis for authorship and instead locates copyrightable creativity in the *post-generation* acts of curation, modification, and arrangement of the AI's output.16 This effectively redefines the "author" in this context as the "curator-in-chief" or "master editor" of the machine's raw material. A data schema designed to assess copyrightability must therefore be architected to capture these specific curatorial actions with high fidelity.

The three recognized categories of copyrightable intervention are:

1.  **Creative Selection and Arrangement:** A human may claim authorship in a compilation if they creatively select from a range of AI-generated outputs and arrange them in a sufficiently original way. For example, in the case of the graphic novel *Zarya of the Dawn*, the USCO granted copyright in the human-authored text and the creative arrangement of the AI-generated images on the page, but refused to register the individual images themselves.9 The copyright protects the human's contribution—the selection and coordination—but does not extend to the underlying AI-generated elements, which remain in the public domain.9
2.  **Material Modification:** A human can claim authorship in the new expression they add by making significant, creative modifications to an AI-generated output. This is legally analogous to creating a derivative work based on a public domain photograph. The human author can copyright their creative additions, but not the pre-existing material generated by the AI.16 The USCO notes that some AI tools which allow a user to "select and regenerate regions of an \[AI-generated\] image with a modified prompt" may provide the user with sufficient control over "the selection and placement of individual creative elements" to support a claim of authorship in the modified result.16
3.  **Embedding in a Larger Human Work:** When AI-generated material is incorporated as a component of a larger, predominantly human-authored work, the copyright in the overall work remains intact. Examples include using AI to generate background artwork for a film, a specific sound effect for a musical track, or a descriptive paragraph in a novel.14 In these cases, the AI-generated portion should be disclaimed during copyright registration if it represents an "appreciable portion of the work as a whole," but its inclusion does not invalidate the copyright in the human-authored components.8

  

### **The Status of Prompts: Uncopyrightable Instructions**

  

The USCO has taken a definitive and restrictive stance on the role of user prompts. It has concluded that guiding an AI system with prompts, even through the sophisticated practice of "prompt engineering," does not generally meet the threshold of creativity required to establish authorship in the resulting output.7

The legal reasoning for this position is twofold. First, the Office analogizes prompts to unprotectable "ideas" or "instructions".16 Under the fundamental idea-expression dichotomy of copyright law, protection extends only to the expression of an idea, not the idea itself.22 A prompt, in this view, is like a set of instructions given to a human artist; the client who commissions the work by describing their idea is not considered the author—the artist who translates that idea into a fixed, tangible expression is.7

Second, this legal conclusion is buttressed by a technical reality of current generative AI systems: their unpredictability. These systems are often described as a "black box," as even expert researchers have a limited ability to predict the specific output that will result from a given input.7 Because a user cannot exercise fine-grained control over the expressive details of the output, they cannot be said to be the "mastermind" who "formed" the work in the way the law requires.9 The AI system's own internal architecture and training data play a determinative role in the final expression.

This reasoning, however, implicitly contains the seeds of its own potential future obsolescence. The USCO's conclusion is predicated on the *current* state of technology and its inherent lack of user control. The Office itself has acknowledged that, in theory, AI systems could evolve to a point where they "allow users to exert such a high degree of control over the output that the system's role becomes purely mechanical".21 This creates a direct causal link between technological advancement and legal status. As AI tools become more deterministic and provide users with more direct control over expressive elements, the legal argument that a prompt (or a series of interactive prompts) can constitute authorship will become substantially stronger. A forward-looking data schema should therefore not treat all AI models as a monolith. It should include fields to capture the specific model used and, if available, a metric of its known "determinism" or "controllability." This would allow a copyright assessment tool to adapt its logic over time, future-proofing the system against the inevitable co-evolution of technology and law.

  

## **Part III: Cross-Referencing with Remix Culture Doctrines: Fair Use and Transformative Works**

  

The creation of AI-assisted works often involves the use of pre-existing material, either as training data for the model or as sampled elements within a new composition. This practice places such works at the intersection of copyright doctrines that have long governed remix and mashup cultures, primarily the doctrine of fair use and its central component, transformative use. Formalizing these complex, case-by-case analyses is essential for any tool that aims to provide guidance on copyright risk.

  

### **The Fair Use Formalization: A Four-Factor Logical Model**

  

Fair use is a statutory defense to copyright infringement codified in Section 107 of the Copyright Act. It permits the unlicensed use of copyrighted works in certain circumstances, balancing the rights of copyright holders with the public interest in freedom of expression and innovation. A court assesses a fair use claim by weighing four non-exclusive factors.23

1.  **The Purpose and Character of the Use:** This factor examines why and how the work was used. Key considerations include whether the use is commercial or for nonprofit educational purposes, with commercial use weighing against fair use.25 The most critical part of this inquiry, however, is whether the use is "transformative"—a concept so central it warrants its own detailed analysis in the next section.
2.  **The Nature of the Copyrighted Work:** This factor considers the characteristics of the work that was used. The law affords greater protection to highly creative and fictional works (like novels and films) than to factual works (like news articles or technical manuals). Consequently, using a creative work is less likely to be deemed fair use.25 Additionally, the use of an unpublished work weighs heavily against a finding of fair use, as it infringes on the author's right of first publication.
3.  **The Amount and Substantiality of the Portion Used:** This factor assesses both the quantity and quality of the material taken. A court will consider what percentage of the original work was used (quantitative analysis) and whether the portion taken constitutes the "heart of the work" (qualitative analysis).25 Copying a small but critically important part of a work can weigh more heavily against fair use than copying a larger but less significant portion.
4.  **The Effect of the Use Upon the Potential Market for or Value of the Copyrighted Work:** Often described as the most important factor, this inquiry examines the economic impact of the use on the original work.27 The analysis considers not only whether the new work acts as a direct market substitute for the original, but also whether it harms potential derivative markets, such as licensing opportunities.23 This is a particularly contentious issue in the context of AI, where the use of works for training data could usurp a nascent licensing market for that specific purpose.27

  

### **The Transformative Use Test: The Impact of Warhol v. Goldsmith**

  

For decades, the analysis of the first fair use factor has been dominated by the concept of transformative use, which asks whether the new work "adds new expression, meaning, or message" to the original.28 Classic examples of transformative use include parody, which uses an original work to comment on or criticize that work itself, as established in

*Campbell v. Acuff-Rose Music, Inc.*.23

However, the Supreme Court's 2023 decision in *Andy Warhol Foundation for the Visual Arts, Inc. v. Goldsmith* significantly reframed and narrowed the transformative use inquiry, particularly for commercial uses.23 The case involved an Andy Warhol silkscreen of the musician Prince, which was based on a photograph by Lynn Goldsmith. The Warhol Foundation licensed its image to a magazine for a cover story about Prince. The Court held that this was not a fair use.

The critical pivot in *Warhol* was a shift in focus from whether the new work added a new "meaning or message" to whether it served a different *purpose* from the original. The Court reasoned that because both Goldsmith's original photograph and Warhol's licensed image served the same essential purpose—a commercial portrait of Prince for use in a magazine—the first factor weighed against fair use, even if Warhol's work was aesthetically different and conveyed a different message about celebrity.23

This "purpose" test creates a significant new hurdle for many common applications of generative AI. Before *Warhol*, one could argue that an AI-generated image "in the style of" a famous artist was transformative because the AI's unique process and digital aesthetic added a new meaning. After *Warhol*, the primary question is whether the new work serves a similar commercial purpose. An AI-generated landscape sold as a fine art print serves the same purpose as a human-photographed landscape sold as a fine art print. This precedent directly targets the market viability of AI art that competes with human artists in the same market niche. To successfully claim fair use, creators of AI-assisted works will increasingly need to demonstrate that their use serves a fundamentally different purpose, such as criticism, commentary, or research, rather than simply offering an aesthetic variation for the same market.32

This distinction between the *process* of AI training and the *output* of an AI model is critical. A growing legal consensus suggests that the process of using copyrighted works as *inputs* to train an AI is a highly transformative fair use. The purpose—to enable a machine to learn statistical patterns from data—is fundamentally different from the original expressive purpose of the works.34 However, if that same trained model produces an

*output* that is substantially similar to, or serves as a market substitute for, one of its training inputs, that output is likely infringing and not a fair use.30 This creates a legal paradox where the act of training is permissible, but it creates a tool whose use may be impermissible. The infringement exists in a latent state until an output is generated and evaluated against the market. Therefore, a copyright assessment tool cannot issue a blanket "fair use" certification; it must analyze the use of copyrighted material at each stage of the creative lifecycle independently.

  

### **Table 1: Logical Conditions for Fair Use and Transformative Status**

  

To translate the abstract four-factor test into an operational model for a software tool, each factor can be broken down into measurable parameters. This allows for a weighted analysis that can generate a "risk score" for a proposed use of copyrighted material, transforming a subjective legal defense into a concrete risk-management feature.

  

|  |  |  |  |  |
| :-: | :-: | :-: | :-: | :-: |
| Factor | Parameter to Measure | Condition Favoring Fair Use | Condition Disfavoring Fair Use | Relevant Sources |
| \*\*1. Purpose & Character\*\* | Use.Purpose (Enum: Commercial, Education, Parody, Criticism, Research, News) | Use.Purpose is Parody, Criticism, Research, News, Education | Use.Purpose is Commercial | 25 |
|   | Use.TransformativeScore (Float: 0-1, based on \*Warhol\* purpose test) | High score (fundamentally different purpose, e.g., data analysis vs. aesthetic enjoyment) | Low score (substitutive purpose, e.g., magazine portrait vs. magazine portrait) | 23 |
| \*\*2. Nature of Work\*\* | Source.Nature (Enum: Factual, Creative) | Source.Nature is Factual/Informational | Source.Nature is Highly Creative/Fictional | 25 |
|   | Source.PublicationStatus (Enum: Published, Unpublished) | Source.PublicationStatus is Published | Source.PublicationStatus is Unpublished | 25 |
| \*\*3. Amount Used\*\* | Use.AmountQuantitative (Float: 0-1, percentage of work used) | Low percentage | High percentage | 26 |
|   | Use.AmountQualitative (Boolean: "Heart of the work" taken) | False | True | 28 |
| \*\*4. Market Effect\*\* | Use.MarketEffect.Substitution (Boolean: Is it a direct market replacement?) | False | True | 23 |
|   | Use.MarketEffect.LicensingHarm (Boolean: Does it harm an existing or potential licensing market?) | False | True (disrupts an established or emerging licensing market, e.g., for AI training data) | 27 |

  

## **Part IV: Defining the Boundaries: Minimum Expression and Maximum Appropriation**

  

To be practically useful, an AI-assisted creation tool must provide clear guidance on the legal boundaries of creation. This requires formalizing two critical thresholds: the minimum amount of human creativity required to generate a copyrightable work, and the maximum amount of another's work that can be appropriated without triggering infringement. These boundaries are defined by the doctrines of originality and *de minimis* use, respectively.

  

### **Minimum Copyrightable Expression: The "Modicum of Creativity" Standard**

  

For a work to be eligible for copyright protection, it must be an "original work of authorship".22 The legal standard for originality consists of two distinct requirements:

1.  **Independent Creation:** The work must be independently created by the author, meaning it cannot be copied from another work.40
2.  **A Modicum of Creativity:** The work must possess "at least a modicum of creativity".22 The Supreme Court has described this as requiring a "spark" of creativity, emphasizing that the bar is intentionally set very low.41

This low threshold is balanced by the fundamental principle of the idea-expression dichotomy: copyright protects the expression of an idea, but never the idea, procedure, process, system, concept, or discovery itself.22 This principle leads to several specific categories of material that are deemed to lack the requisite creativity and are therefore uncopyrightable. These include:

  - Names, titles, short phrases, and slogans.22
  - Familiar symbols or designs.
  - Mere variations of typographic ornamentation, lettering, or coloring.
  - Mere listings of ingredients or contents.41

For an AI-assisted work, this means that the human contribution must rise above these excluded categories. A human author who simply provides a title, a short phrase, or a basic instruction to an AI will not have contributed sufficient original expression to be considered an author of the output. However, a human who creatively selects and arranges AI-generated paragraphs into an original narrative, or who materially modifies an AI-generated image with their own artistic choices, will likely have contributed the necessary "modicum of creativity" to claim copyright in their contributions.

  

### **Maximum Sampleable Work: The De Minimis Doctrine**

  

At the other end of the spectrum is the question of appropriation. The *de minimis* doctrine, from the Latin maxim *de minimis non curat lex* ("the law does not concern itself with trifles"), provides that a technical act of copying may be so trivial or insignificant that it does not rise to the level of a legally actionable infringement.42 This doctrine is distinct from fair use, though it is related to the third fair use factor (amount and substantiality). A finding of

*de minimis* use means no infringement has occurred in the first place.

Courts typically apply a two-part test to determine if a use is *de minimis*:

1.  **Quantitative Analysis:** This considers the raw amount of the original work that was copied. Examples of uses found to be quantitatively small include a pinball machine appearing in the background of a movie for a few seconds or fleeting, out-of-focus illustrations.42
2.  **Qualitative Analysis:** This is often the more important inquiry. It asks whether the copied portion, regardless of its size, is qualitatively significant or constitutes the "heart" of the original work.45 A key element of this analysis in many circuits is whether an "average audience would recognize the appropriation".45 If the copied element is not recognizable to an ordinary observer, the use is more likely to be considered  
    *de minimis*.

The application of this doctrine is most contentious and fragmented in the area of digital music sampling, where a significant circuit split creates different legal standards across the country.

  - **The 6th Circuit's Bright-Line Rule:** In *Bridgeport Music, Inc. v. Dimension Films*, the Sixth Circuit Court of Appeals established a strict, bright-line rule for sound recordings. The court held that any digital sampling of a copyrighted sound recording, no matter how brief or altered, constitutes infringement. The court's blunt directive was: "Get a license or do not sample".39 Under this standard, the maximum sampleable amount of a sound recording without a license is effectively zero.
  - **The 9th Circuit's Qualitative Approach:** In contrast, the Ninth Circuit, in cases like *VMG Salsoul, LLC v. Ciccone*, has adopted a qualitative approach consistent with the "average audience" test. The court held that a fleeting, 0.23-second sample of a horn hit was *de minimis* because it was not recognizable to the ordinary listener.45 This standard allows for the possibility of legally permissible, unlicensed sampling of sound recordings, provided the use is truly trivial in both quantity and quality.

This circuit split means that any tool providing guidance on sampling must account for jurisdictional variance. A conservative approach would advise users to treat any digital sample of a sound recording as requiring a license, while a more permissive, risk-tolerant approach could incorporate the Ninth Circuit's recognizability test.

  

### **Table 2: Guidelines for Minimum Expression and De Minimis Use**

  

This table translates the legal thresholds for originality and *de minimis* use into practical rules and risk assessments that can be implemented within a creative tool's user interface and internal logic.

  

|  |  |  |  |  |
| :-: | :-: | :-: | :-: | :-: |
| Guideline Category | Rule / Test | Tool Implementation / User Guidance | Risk Level | Relevant Sources |
| \*\*Minimum Expression\*\* | Is the human contribution more than a short phrase, name, title, or simple geometric shape? | "Your contribution '\\\[text\\\]' is likely too brief to be protected by copyright on its own. To secure copyright, consider elaborating on this idea or combining it with other creative elements." | N/A (Not Copyrightable) | 22 |
|   | Does the human contribution involve creative selection, coordination, or arrangement of elements? | "By selecting and arranging these 5 AI-generated images into a unique sequence, you have likely created a new, copyrightable compilation. Your copyright protects the arrangement, not the individual images." | Low | 16 |
| \*\*De Minimis Use (Visual)\*\* | Is the sampled visual work fleeting (e.g., \\\< 3 seconds), out of focus, and not central to the new work's theme or narrative? | "The background image appears for less than 3 seconds and is not the focus of the scene. The risk of an infringement claim is likely low under the \*de minimis\* doctrine." | Low | 42 |
| \*\*De Minimis Use (Audio - Conservative / 6th Circuit Rule)\*\* | Is any part of a copyrighted \*sound recording\* being digitally sampled without a license? | "\*\*HIGH RISK WARNING:\*\* You are digitally sampling a sound recording. In some jurisdictions, any unlicensed sampling, regardless of length, is considered copyright infringement. A license is strongly recommended." | High | 39 |
| \*\*De Minimis Use (Audio - Permissive / 9th Circuit Rule)\*\* | Is the sampled audio quantitatively and qualitatively insignificant? Would an average listener recognize its source? | "\*\*MODERATE RISK:\*\* The sampled audio is less than one second and has been significantly altered. It is unlikely to be recognizable to an average listener. While this may be considered \*de minimis\* use in some jurisdictions, a risk of legal challenge remains." | Moderate | 39 |

  

## **Part V: The Unified Data Schema for Copyright Provenance and Status**

  

The culmination of this legal analysis is the development of a formal data schema designed to capture and track the copyright status of an AI-assisted work throughout its creation. Traditional metadata standards like IPTC are well-suited for describing the attributes of a finished creative asset but are insufficient for the dynamic, layered, and iterative process inherent in AI-assisted creation.48 A new model is required.

  

### **Design Principles: Beyond Static Metadata**

  

The proposed schema is architected not as a static record, but as a dynamic, auditable log of the entire creative process—a "Copyright Provenance Ledger." Its design is guided by the following principles:

1.  **Process-Oriented:** The schema's primary function is to record the *process* of creation, not just the final product. As the legal analysis has shown, the sequence and nature of human interventions are the dispositive factors in determining copyrightability.
2.  **Atomicity and Immutability:** Each creative act—a prompt, an AI generation, a human modification, a selection—is recorded as a discrete, atomic "contribution." This creates an immutable ledger that can be audited to determine the provenance of any element in the final work.
3.  **Inspiration from Modern Data Standards:** The design draws inspiration from technical standards like the Coalition for Content Provenance and Authenticity (C2PA), which focuses on tracking the origin and history of digital media, including edits and AI generation.51 It also incorporates concepts from version control systems, which excel at tracking changes over time.
4.  **Enabling Automated Analysis:** The structure is explicitly designed to support algorithmic analysis. By logging legally significant data points (e.g., contributor type, contribution type, source material status), the system can automatically calculate risk scores and provide real-time feedback to the user.

  

### **The Core Schema: Tables and Fields**

  

The schema is relational, comprising four interconnected tables that work together to model the creative ecosystem. This structure separates the actors (Contributors), the actions (Contributions), the raw materials (Assets), and the final composite product (Works). This separation allows the system to algorithmically trace the provenance of every pixel, word, or note in the final work back to its origin—a human prompt, an AI generation, a human modification, or a third-party sample. This traceability is what enables the calculation of sophisticated, legally-grounded metrics like a HumanAuthorshipScore and a FairUseRiskScore, providing the precise and actionable guidance required for a modern creative tool.

  

### **Table 3: The Unified Data Schema for Copyright Provenance and Status**

  
  

#### **Table 3.1: Works Table (The Final Product)**

  

This table represents the final, composite work that is the output of the creative process.

|  |  |  |
| :-: | :-: | :-: |
| Field Name | Data Type | Description |
| WorkID | UUID | Primary key for the final composite work. Uniquely identifies this specific creative endeavor. |
| Title | Text | The human-assigned title of the work. |
| FinalCreationTimestamp | Timestamp | Timestamp marking the completion or export of the final version of the work. |
| OverallCopyrightStatus | Enum (Copyrightable, Public Domain, Mixed-Status) | A system-determined overall status, calculated based on the aggregation of all contributions and assets. "Mixed-Status" indicates the work contains both protectable human authorship and unprotectable elements (e.g., AI-generated material, third-party samples). |
| HumanAuthorshipScore | Float (0.0 to 1.0) | A calculated score representing the proportion of the final work attributable to protectable human creative actions (e.g., modification, selection, arrangement) versus unprotectable actions (e.g., prompting) or AI generation. A higher score indicates a stronger claim to copyright. |
| FairUseRiskScore | Float (0.0 to 1.0) | A calculated risk score based on the automated analysis of all incorporated third-party assets using the logic from Table 1. A higher score indicates a greater risk that the use of third-party material would not be considered fair use. |
| Jurisdiction | Text | The legal jurisdiction under which the work was created (e.g., "USA", "GBR", "CHN"). Essential for applying the correct legal rules (e.g., for \*de minimis\* use). |

  

#### **Table 3.2: Contributions Table (The Creative Ledger)**

  

This is the core of the schema, logging every single creative event in chronological order to build an auditable chain of provenance.

|  |  |  |
| :-: | :-: | :-: |
| Field Name | Data Type | Description |
| ContributionID | UUID | Primary key for each discrete creative action. |
| WorkID | UUID | Foreign key linking this action to the overall Works table. |
| ParentContributionID | UUID | Foreign key to the previous contribution this one modifies. This linkage creates the historical chain of edits and transformations. A NULL value indicates an initial action. |
| ContributorID | UUID | Foreign key to the Contributors table, identifying who (or what) performed this action. |
| ContributionTimestamp | Timestamp | The precise time the action was performed. |
| ContributionType | Enum (Human-Creation, Human-Modification, Human-Selection, Human-Arrangement, Human-Prompt, AI-Generation) | The nature of the action. This is the most critical field for legal analysis, directly mapping to the copyrightable interventions identified by the USCO. |
| ContributionData | JSONB | A flexible field to store the specific data of the action. For a Human-Prompt, this would be the text of the prompt. For a Human-Modification, it could store coordinates and transformation data. For a Human-Selection, it would list the AssetIDs that were chosen. |

  

#### **Table 3.3: Contributors Table (Human and AI Actors)**

  

This table identifies every actor, human or machine, that participates in the creation of the work.

  

|  |  |  |
| :-: | :-: | :-: |
| Field Name | Data Type | Description |
| ContributorID | UUID | Primary key for the contributor. |
| ContributorType | Enum (Human, AI) | A simple but legally crucial flag distinguishing between human users and AI systems. |
| HumanIdentifier | Text | For human contributors, a unique identifier such as a user account ID or a persistent author identifier like an ORCID.53 |
| AIModelIdentifier | Text | For AI contributors, the specific name and version of the model used (e.g., "Midjourney-v6.0", "Claude-3-Opus-20240229"). This is vital for tracking the capabilities of the tool used. |
| AIControllabilityScore | Float (0.0 to 1.0) | A metric representing the known determinism or fine-grained controllability of the AI model. A higher score indicates the user has more direct control over the output's expressive elements, which may become legally significant in the future.21 |

  

#### **Table 3.4: Assets Table (The Raw Materials)**

  

This table catalogs every discrete piece of content—whether created, generated, or imported—that is part of the work.

|  |  |  |
| :-: | :-: | :-: |
| Field Name | Data Type | Description |
| AssetID | UUID | Primary key for each discrete piece of content (e.g., an image, a block of text, an audio clip). |
| ContributionID | UUID | Foreign key to the Contributions table entry that created or imported this asset. This links every piece of content to its origin. |
| AssetHash | SHA256 | A cryptographic hash of the asset's binary content, ensuring data integrity and providing a unique fingerprint for the content. |
| AssetType | Enum (Text, Image, Audio, Video) | The media type of the asset. |
| SourceAssetID | UUID | If this asset is a modification or derivative of another asset, this field points to the original source asset, creating a lineage. |
| OriginalCopyrightStatus | Enum (Human-Authored, AI-Generated, Third-Party-Copyrighted, Public-Domain) | The copyright status of the asset at the moment of its creation or ingestion into the system. This is a critical input for the FairUseRiskScore calculation. |
| ThirdPartyLicense | Text | If the asset is from a third party, this field stores the details of its license (e.g., "Creative Commons CC-BY-SA 4.0", "Getty Images Royalty-Free License \\\#12345"). |

  

## **Conclusion and Recommendations**

  
  

### **Summary of Findings**

  

The legal framework for copyright in the United States, when confronted with generative AI, has demonstrated a powerful adherence to its foundational principles. The analysis confirms that human authorship is the absolute and indispensable prerequisite for copyright protection. The USCO and federal courts have consistently held that works generated autonomously by machines are not copyrightable. For hybrid works created through human-AI collaboration, copyrightability is not determined by the user's initial idea or prompt, but rather by the quantum of creative control the human exercises over the final expressive output. Legally cognizable contributions are found in the post-generation acts of creative selection, arrangement, and material modification of AI-generated content.

Simultaneously, the doctrines governing the use of pre-existing works have been clarified and sharpened. The Supreme Court's decision in *Andy Warhol Foundation v. Goldsmith* has narrowed the scope of transformative fair use for commercial works, shifting the focus from aesthetic change to the ultimate purpose of the use. This places many common "in the style of" AI generations on precarious legal ground if they compete in the same market as the original works. Finally, the *de minimis* doctrine provides a narrow safe harbor for truly trivial copying, but a significant circuit split in music sampling cases highlights the jurisdictional risks inherent in appropriation.

  

### **Strategic Recommendations for Implementation**

  

Based on these findings, the following strategic recommendations are provided for the successful development and deployment of an AI-assisted creative tool that is both powerful for users and legally robust.

1.  **Adopt a Provenance-Led Architecture:** The tool's core architecture must be built around the proposed ledger-style data schema. This is not an optional feature but a foundational requirement. An immutable and auditable record of the entire creative process is the only reliable way to generate the evidence needed to support a claim of human authorship and to accurately assess copyright risks.
2.  **Implement a Dynamic Risk Analysis Engine:** The tool should leverage the data captured in the schema to power a real-time analysis engine. This engine should continuously calculate and display the HumanAuthorshipScore and FairUseRiskScore to the user. This transforms the tool from a simple content generator into an intelligent co-pilot that provides active, legally-informed feedback, guiding creators toward copyrightable outcomes and away from high-risk activities.
3.  **Educate Users Through an Interactive Interface:** The user interface should be designed to make the underlying legal principles transparent and understandable. Using the guidelines from Table 2, the tool should provide clear, context-sensitive warnings and explanations. For example, when a user attempts to digitally sample a sound recording, a pop-up should explain the high risk associated with this action under the 6th Circuit's *Bridgeport* rule. This educational component empowers users to make informed decisions about their creative choices.
4.  **Prepare for Jurisdictional Variance:** While this report focuses on U.S. law, the global nature of digital content creation necessitates a multi-jurisdictional approach. The schema's Jurisdiction field is a crucial first step. The product roadmap should include the development of separate rule sets for other major legal regimes, such as the European Union and the United Kingdom, to provide accurate guidance to a global user base.
5.  **Monitor Legal and Technological Evolution:** The intersection of AI and copyright is one of the most dynamic areas of law. The company must dedicate legal and technical resources to continuously monitor new case law, evolving administrative guidance from the USCO, and significant advancements in AI technology. The logic of the risk analysis engine and the parameters of the data schema (such as the AIControllabilityScore) must be updated regularly to reflect the changing landscape, ensuring the tool remains relevant and reliable.

#### **Works cited**

1.  Who Owns the Output? Bridging Law and Technology in LLMs Attribution - arXiv, accessed October 3, 2025, <https://arxiv.org/html/2504.01032v1>
2.  Authorship in AI-Generated Works: Exploring Originality in Text Prompts and AI Outputs Through Philosophical Foundations of Copyright and Collage Protection Francesca Mazzi - ATRIP, accessed October 3, 2025, <https://atrip.org/wp-content/uploads/2024/05/3rd-place-revised.pdf>
3.  Copyright and Generative AI | The Regulatory Review, accessed October 3, 2025, <https://www.theregreview.org/2025/06/07/seminar-copyright-and-generative-ai/>
4.  Artificial Intelligence Impacts on Copyright Law - RAND, accessed October 3, 2025, <https://www.rand.org/pubs/perspectives/PEA3243-1.html>
5.  Developing a Coherent National Strategy: Artificial Intelligence (AI) and Copyright Law, accessed October 3, 2025, <https://businesslawreview.uchicago.edu/online-archive/developing-coherent-national-strategy-artificial-intelligence-ai-and-copyright-law>
6.  DOES TRAINING AI VIOLATE COPYRIGHT LAW?, accessed October 3, 2025, <https://btlj.org/wp-content/uploads/2023/02/0003-36-4Quang.pdf>
7.  Copyright-and-Artificial-Intelligence-Part-2-Copyrightability-Report.pdf, accessed October 3, 2025, <https://www.copyright.gov/ai/Copyright-and-Artificial-Intelligence-Part-2-Copyrightability-Report.pdf>
8.  Copyrightability of AI-Generated Works, accessed October 3, 2025, <https://copyrightalliance.org/copyright-ai-generated-works/>
9.  Copyright Registration Guidance: Works ... - Federal Register, accessed October 3, 2025, <https://www.federalregister.gov/documents/2023/03/16/2023-05321/copyright-registration-guidance-works-containing-material-generated-by-artificial-intelligence>
10. Copyright Law in the Age of AI: Navigating Authorship, Infringement, and Creative Rights - New York State Bar Association, accessed October 3, 2025, <https://nysba.org/copyright-law-in-the-age-of-ai-navigating-authorship-infringement-and-creative-rights/>
11. Generative Artificial Intelligence and Copyright Law - Congress.gov, accessed October 3, 2025, <https://www.congress.gov/crs-product/LSB10922>
12. Appellate Court Affirms Human Authorship Requirement for Copyrighting AI-Generated Works | Insights | Skadden, Arps, Slate, Meagher & Flom LLP, accessed October 3, 2025, <https://www.skadden.com/insights/publications/2025/03/appellate-court-affirms-human-authorship>
13. D.C. Circuit Affirms Human Authorship Requirement for Copyright Protection - Lewis Rice, accessed October 3, 2025, <https://www.lewisrice.com/publications/d-c-circuit-affirms-human-authorship-requirement-for-copyright-protection/>
14. Copyright Office Releases Part 2 of Artificial Intelligence Report, accessed October 3, 2025, <https://www.copyright.gov/newsnet/2025/1060.html>
15. Copyright and Artificial Intelligence | U.S. Copyright Office, accessed October 3, 2025, <https://www.copyright.gov/ai/>
16. U.S. Copyright Office issues report on copyrightability of AI assisted and generated works, accessed October 3, 2025, <https://www.hoganlovells.com/en/publications/us-copyright-office-issues-report-on-copyrightability-of-ai-assisted-and-generated-works>
17. Copyright Office Releases Part 2 of Artificial Intelligence Report - Library of Congress, accessed October 3, 2025, <https://newsroom.loc.gov/news/copyright-office-releases-part-2-of-artificial-intelligence-report/s/f3959c36-d616-498d-b8f9-67641fd18bab>
18. AI, Copyright, and the Law: The Ongoing Battle Over Intellectual Property Rights - USC, accessed October 3, 2025, <https://sites.usc.edu/iptls/2025/02/04/ai-copyright-and-the-law-the-ongoing-battle-over-intellectual-property-rights/>
19. Copyright Infringement & Litigation: 15 Famous Cases Analyzed | Abounaja IP, accessed October 3, 2025, <https://abounaja.com/index.php/blog/copyright-infringement-cases>
20. Copyrightability of AI Outputs: U.S. Copyright Office Analyzes Human Authorship Requirement | Insights | Jones Day, accessed October 3, 2025, <https://www.jonesday.com/en/insights/2025/02/copyrightability-of-ai-outputs-us-copyright-office-analyzes-human-authorship-requirement>
21. Copyright Offices Rules AI-Works from Text Not Protected - The National Law Review, accessed October 3, 2025, <https://natlawreview.com/article/copyright-office-says-ai-generated-works-based-text-prompts-are-not-protected>
22. Copyright Basics - Copyright Information, accessed October 3, 2025, <https://copyright.psu.edu/copyright-basics/>
23. Copyrights Supreme Court Cases, accessed October 3, 2025, <https://supreme.justia.com/cases-by-topic/copyrights/>
24. Navigating Fair Use: A Journey Through Recent Case Law - | Ohio State University Libraries, accessed October 3, 2025, <https://library.osu.edu/news/navigating-fair-use-a-journey-through-recent-case-law>
25. Fair Use Defense to Copyright Infringement Lawsuits | Intellectual Property Law Center, accessed October 3, 2025, <https://www.justia.com/intellectual-property/copyright/fair-use/>
26. 17 U.S. Code § 107 - Limitations on exclusive rights: Fair use - Legal Information Institute, accessed October 3, 2025, <https://www.law.cornell.edu/uscode/text/17/107>
27. Court Issues First Decision on AI and Fair Use | Alerts and Articles | Insights | Ballard Spahr, accessed October 3, 2025, <https://www.ballardspahr.com/insights/alerts-and-articles/2025/02/court-issues-first-decision-on-ai-and-fair-use>
28. Fair Use: What Is Transformative? - Nolo, accessed October 3, 2025, <https://www.nolo.com/legal-encyclopedia/fair-use-what-transformative.html>
29. First of its Kind Decision Finds AI Training is Not Fair Use - Copyright Alliance, accessed October 3, 2025, <https://copyrightalliance.org/ai-training-not-fair-use/>
30. Copyright Office Weighs In on AI Training and Fair Use, accessed October 3, 2025, <https://www.skadden.com/insights/publications/2025/05/copyright-office-report>
31. Transformative use - Wikipedia, accessed October 3, 2025, <https://en.wikipedia.org/wiki/Transformative_use>
32. Artificial Intelligence and Transformative Use After Warhol, accessed October 3, 2025, <https://scholarlycommons.law.wlu.edu/wlulr-online/vol81/iss1/2/>
33. "LIMITS OF ALGORITHMIC FAIR USE" by Jacob Alhadeff, Cooper Cuene et al., accessed October 3, 2025, <https://digitalcommons.law.uw.edu/wjlta/vol19/iss1/1/>
34. Fair Use and AI Training: Two Recent Decisions Highlight the Complexity of This Issue, accessed October 3, 2025, <https://www.skadden.com/insights/publications/2025/07/fair-use-and-ai-training>
35. Two U.S. Courts Address Fair Use in Generative AI Training Cases | Insights | Jones Day, accessed October 3, 2025, <https://www.jonesday.com/en/insights/2025/06/two-us-courts-address-fair-use-in-genai-training-cases>
36. Training Generative AI Models on Copyrighted Works Is Fair Use, accessed October 3, 2025, <https://www.arl.org/blog/training-generative-ai-models-on-copyrighted-works-is-fair-use/>
37. Copyright Implications and Legal Responses to AI Training: A Chinese Perspective - MDPI, accessed October 3, 2025, <https://www.mdpi.com/2075-471X/14/4/43>
38. Foundation Models and Fair Use - Journal Article - Stanford Law School, accessed October 3, 2025, <https://law.stanford.edu/publications/foundation-models-and-fair-use/>
39. The Song Remains the Same: A Review of the Legalities of Music ..., accessed October 3, 2025, <https://www.wipo.int/web/wipo-magazine/articles/the-song-remains-the-same-a-review-of-the-legalities-of-music-sampling-37091>
40. Requirements for Copyright Protection, accessed October 3, 2025, <https://copyrightalliance.org/education/copyright-law-explained/copyright-basics/requirements-for-copyright-protection/>
41. What is Copyright?, accessed October 3, 2025, <https://www.copyright.gov/what-is-copyright/>
42. The De Minimis Doctrine: When Is Copying Too Trivial? - Lutzker ..., accessed October 3, 2025, <https://www.lutzker.com/the-de-minimis-doctrine-when-is-copying-too-trivial/>
43. De Minimis & Copyright Infringement : Where To Draw The Line? - IP and Legal Filings, accessed October 3, 2025, <https://www.ipandlegalfilings.com/de-minimis-copyright-infringement-where-to-draw-the-line/>
44. De Minimis Use - Entertainment Law - USLegal, accessed October 3, 2025, <https://entertainmentlaw.uslegal.com/intellectual-property/copyright/de-minimis-use/>
45. The deminimis defense to copyright infringement Introduction - Vondran Legal, accessed October 3, 2025, <https://www.vondranlegal.com/the-deminimis-defense-to-copyright-infringement-introduction>
46. De Minimis Copyright Infringement in Music - Talks On Law, accessed October 3, 2025, <https://www.talksonlaw.com/blog/a-split-on-de-minimis-copyright-infringement-in-music>
47. Fair Use and an Attribution-Oriented Approach to Music Sampling - Yale Law School Legal Scholarship Repository, accessed October 3, 2025, <https://openyls.law.yale.edu/bitstreams/25470cc8-3ce6-4f37-ba69-38704d4b30ad/download>
48. Introduction to Metadata: Rights Metadata Made Simple, accessed October 3, 2025, <https://www.getty.edu/publications/intrometadata/rights-metadata/>
49. Copyright's critical mess: music metadata - Wolters Kluwer, accessed October 3, 2025, <https://legalblogs.wolterskluwer.com/copyright-blog/copyrights-critical-mess-music-metadata/>
50. Photo Metadata IPTC, accessed October 3, 2025, <https://iptc.org/standards/photo-metadata/>
51. C2PA | Verifying Media Content Sources, accessed October 3, 2025, <https://c2pa.org/>
52. Provenance Research - Denver Art Museum, accessed October 3, 2025, <https://www.denverartmuseum.org/en/provenance-research>
53. ACM Policy on Authorship, accessed October 3, 2025, <https://www.acm.org/publications/policies/new-acm-policy-on-authorship>
