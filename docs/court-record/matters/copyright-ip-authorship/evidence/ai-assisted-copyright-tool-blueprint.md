# **Operationalizing Human Authorship: A Legal and Technical Framework for Copyright in the Age of AI**

  
  

## **I. The Human Authorship Mandate: A Legal and Architectural Framework for AI-Assisted Creativity**

  

The development of any tool intended to facilitate the creation of copyrightable works with the assistance of artificial intelligence must begin not with a technical specification, but with a deep and rigorous interpretation of the governing legal doctrine. The United States Copyright Office (USCO) and federal courts have been unequivocal: human authorship is the *sine qua non* of copyrightability.1 This principle, far from being a recent contrivance for the AI era, is a foundational tenet of U.S. copyright law, consistently upheld and recently reaffirmed in landmark decisions such as

*Thaler v. Perlmutter*, which concluded that copyright law protects only works of human creation.2 The proposed system's architecture, therefore, cannot treat legal compliance as an add-on or a feature. Instead, the legal requirements must serve as the immutable blueprint from which all technical decisions flow. The system's very design must function as an operationalized legal argument, preemptively constructing the case for human authorship through its normative workflow.

  

### **1.1 Deconstructing the USCO's Stance: Beyond AI-Generated vs. AI-Assisted**

  

The USCO has carefully articulated a critical distinction that forms the basis of its regulatory approach. It differentiates between the use of AI as a subordinate "tool" to assist or enhance human creativity—akin to a camera, a word processor, or sophisticated photo-editing software—and the use of AI as the autonomous "author" of a work.1 Works created by humans with the

*assistance* of AI may be copyrightable, but works *generated* by AI without sufficient human creative input are not.1 The primary architectural objective of the proposed platform is to manifest this legal distinction in code and data. It must be designed from the ground up to frame the AI as a powerful, but ultimately subordinate, instrument in the hands of a human creator.

A cornerstone of this framework is the USCO's position on user prompts. The Office has clarified that prompts, regardless of their detail or complexity, are generally considered uncopyrightable instructions that convey an idea, not the fixed, tangible expression of that idea.1 The USCO notes that prompts "do not control the way that idea is expressed," analogizing them to instructions given to a commissioned artist who retains ultimate creative control.1 This is because generative AI models introduce a significant degree of unpredictability and interpretation, meaning the user does not have sufficient control over the final expression to be considered its author.8 Consequently, the system must be architected to treat prompts as legally insignificant from an authorship perspective. They are the uncopyrightable instructions that initiate a creative process, not the copyrightable act of creation itself. The AI's output, in turn, is treated as raw material, devoid of authorship until a human imbues it with the requisite creative contribution.

  

### **1.2 The Anatomy of Copyrightable Contribution: Modification, Arrangement, and Expressive Input**

  

To build a tool that successfully navigates the USCO's requirements, it is essential to understand precisely which forms of human intervention are recognized as conferring authorship. The USCO's guidance and reports outline three primary categories of copyrightable contribution in the context of AI-assisted works.

First, **Material Modification** is a key pathway to establishing authorship. A human who takes AI-generated output and significantly modifies it can claim copyright in their creative contributions, provided those modifications meet the originality standard on their own.1 The work as a whole is not copyrightable, but the human-authored modifications are. This legal requirement translates directly into a critical technical mandate: the system must be capable of meticulously capturing, measuring, and documenting these human modifications as distinct, auditable events.

Second, the USCO recognizes authorship in the **Creative Selection and Arrangement** of AI-generated materials. A human can create a copyrightable work by selecting from a range of AI outputs and arranging them in a sufficiently creative way, such that "the resulting work as a whole constitutes an original work of authorship".1 This is consistent with the long-standing protection for compilations. For example, selecting three images from a set of ten AI-generated options and arranging them into a triptych is a creative act. Simply selecting a single output from a generative process, however, is not considered a creative act.8 The system's design must therefore log not only the final arrangement but the

*act of selection* itself—recording which assets were chosen from the available pool of AI-generated raw material.

Third, the concept of **Expressive Inputs** provides a more nuanced route to copyrightability. This applies when a human inputs their own pre-existing, copyrightable work into an AI system and directs the system to modify it. If the human's original expression remains perceptible in the final output, they can claim copyright in that perceptible portion of the work, similar to how an author of a derivative work owns the copyright in their new contributions.1 This necessitates that the system be able to ingest and track the provenance of user-imported assets, distinguishing them from assets generated

*de novo* by the AI.

  

### **1.3 From Legal Theory to System Architecture: Why Copyright Law Dictates a Provenance-First Design**

  

The legal framework established by the USCO places a significant evidentiary burden on the copyright applicant. When registering a work containing AI-generated material, the applicant must disclose this fact and provide a brief description of the human-authored contributions, effectively disclaiming the portions generated by AI.1 This disclosure requirement fundamentally invalidates the architecture of traditional creative tools, which are designed to save the final state of a work, not the process of its creation. For a user of a conventional tool, accurately disclaiming AI-generated portions and proving the extent of human modification after the fact is difficult, if not impossible.

This legal burden dictates that a compliant system must adopt a "provenance-first" architecture. The proposed tool's design correctly inverts the traditional workflow. Instead of creating content and then attempting to retroactively assemble a legal justification for its copyrightability, the system's normative workflow is engineered to *inherently generate the justification* as an inseparable byproduct of the creative process. Every legally significant act—every prompt, every AI generation, and, most critically, every human modification, selection, and arrangement—is captured as a discrete, timestamped event in an immutable ledger. This approach transforms the act of creation into the act of evidence generation. The system's primary output is not just the creative work, but the legally defensible proof of its human-authored origins.

This leads to a critical realization about the nature of the user interface itself. The proposal to render AI-generated output as read-only and programmatically funnel the user into a mandatory "Modification" or "Curation" mode is a profound design choice. This transforms the UI from a passive canvas into an active compliance mechanism. It does not merely permit users to perform copyrightable actions; it actively prevents them from committing uncopyrightable ones, such as simply generating and exporting raw AI output. This enforced "human-in-the-loop" workflow ensures that any work marked "complete" within the system has, by definition, passed a minimum threshold of human creative intervention that directly aligns with USCO guidance.12 The UI, in this context, becomes a set of regulatory guardrails, guiding the creator toward a legally defensible final product.

  

## **II. The Copyright Provenance Ledger: An Immutable Record of Creative Acts**

  

At the core of the proposed system lies the Copyright Provenance Ledger, a data schema designed to serve as the immutable, auditable, and non-repudiable record of a work's creation. This ledger is not merely a database; it is the technical embodiment of the legal strategy, translating the abstract principles of human authorship into a structured, verifiable format. Its design is rooted in the concept of data provenance, which provides a documented trail accounting for a data object's origin, creation, and transformation, thereby establishing trust, reliability, and an auditable history.14 By applying this concept to intellectual property, the ledger creates a verifiable chain of custody for every creative element, from initial prompt to final, human-refined expression.16

  

### **2.1 Schema Deep Dive: Formalizing the Works, Contributors, Assets, and Contributions Model**

  

The proposed ledger is structured around four principal entities: Works, Contributors, Assets, and Contributions. To move from concept to implementation, this structure must be formalized into a detailed data schema. This schema serves as the blueprint for the system's persistence layer and provides the necessary granularity to capture legally significant events.

  - **Works:** Represents the final, composite creative project. It acts as the top-level container, linking together all associated contributors, assets, and contributions. It also houses the system-calculated HumanAuthorshipScore, providing a real-time metric of the strength of the copyright claim.
  - **Contributors:** A catalog of every actor, both human and AI, that participates in the creative process. This entity is crucial for attribution, clearly distinguishing between the human author and the AI tools used. It logs specific model names and versions (e.g., Google Gemini 2.5 Pro), which is essential for the disclaimer required by the USCO.
  - **Assets:** An inventory of every discrete piece of content, whether generated by an AI or imported by the user. Each asset is assigned a unique identifier and is cryptographically hashed to ensure its integrity. This allows the system to track the origin of every sentence, image, or sound clip within the final work.
  - **Contributions:** This is the core transactional log of the ledger. It records every single creative act in chronological order as a discrete event. Each entry details who performed the act (Contributor), when it occurred (Timestamp), what type of act it was (e.g., Human-Modification), and what it relates to (e.g., which Asset was modified). This chronological, event-based log provides the granular evidence needed to substantiate a claim of human authorship.

To enhance interoperability and align with established best practices, this schema should be designed to be compatible with the W3C's PROV Ontology (PROV-O), a global standard for representing provenance data.18 In this mapping, a

Contributor would correspond to a prov:Agent, Assets and Works would be prov:Entity subtypes, and a Contribution would be a prov:Activity. Adopting this standard would ground the system in a robust, well-understood model for provenance interchange.

The following table provides a detailed data dictionary for the Copyright Provenance Ledger, serving as a concrete blueprint for its implementation.

|  |  |  |  |  |  |
| :-: | :-: | :-: | :-: | :-: | :-: |
| Table Name | Field Name | Data Type | Description/Purpose | Relationships/Constraints | Example |
| \*\*Works\*\* | WorkID | UUID | Primary key for the creative project. |   | f47ac10b-58cc-4372-a567-0e02b2c3d479 |
|   | Title | String | The title of the final work. |   | "Midnight Train" |
|   | AuthorID | UUID | Foreign key to the primary human author in Contributors. | FK -\\\> Contributors.ContributorID | ... |
|   | CompletionDate | Timestamp | Date the work was marked as complete. |   | 2025-10-26T10:00:00Z |
|   | HumanAuthorshipScore | Float | System-calculated score based on ledger events. | Calculated field; non-editable. | 87.5 |
| \*\*Contributors\*\* | ContributorID | UUID | Primary key for any actor (human or AI). |   | a1b2c3d4-e5f6-7890-1234-567890abcdef |
|   | Type | Enum | 'HUMAN' or 'AI'. |   | 'AI' |
|   | Name | String | Human name or AI model name. |   | 'Google Gemini 2.5 Pro' |
|   | Version | String | AI model version, if applicable. |   | 'v1.2025.10.03' |
| \*\*Assets\*\* | AssetID | UUID | Primary key for a discrete piece of content. |   | b5c6d7e8-f9g0-1234-5678-90abcdef1234 |
|   | AssetHash | String (SHA-256) | Cryptographic hash of the asset's content. | Unique, Indexed. | e3b0c442... |
|   | Type | Enum | 'AI\\\_GENERATED\\\_TEXT', 'USER\\\_IMPORTED\\\_IMAGE', etc. |   | 'AI\\\_GENERATED\\\_TEXT' |
|   | Content | Text/BLOB Pointer | The actual content or a reference to it. |   | "It was a dark and stormy night..." |
|   | OriginContributionID | UUID | Foreign key to the Contribution that created this asset. | FK -\\\> Contributions.ContributionID | ... |
| \*\*Contributions\*\* | ContributionID | UUID | Primary key for a single creative event. |   | c9d8e7f6-g5h4-3210-fedc-ba9876543210 |
|   | WorkID | UUID | Foreign key to the parent Work. | FK -\\\> Works.WorkID | ... |
|   | ContributorID | UUID | Foreign key to the Contributor who performed the act. | FK -\\\> Contributors.ContributorID | ... |
|   | Timestamp | Timestamp | Precise time of the event. | Indexed. | 2025-10-26T09:15:30Z |
|   | Type | Enum | 'Human-Prompt', 'AI-Generation', 'Human-Modification', 'Human-Selection', 'Human-Arrangement'. |   | 'Human-Modification' |
|   | ParentContributionID | UUID | Foreign key linking this event to a previous one (e.g., a modification linked to the AI generation it modifies). | Self-referential FK. | ... |
|   | ContributionData | JSON/Text | Data specific to the event type (e.g., the prompt text, a diff object, an array of selected AssetIDs). |   | {"diff": "+-...", "algorithm": "myers"} |

  

### **2.2 Establishing Trust and Non-Repudiation: Git-Based Immutability and Cryptographic Hashing**

  

The legal utility of the ledger is entirely dependent on its integrity. The record of creative acts must be both tamper-evident and chronologically sound. The proposal to build the system on a local-first, plain-text model directly on Git—the "Scribe" model—is a highly pragmatic and elegant engineering decision. This approach leverages Git's core architecture as a distributed version control system to provide the necessary trust and non-repudiation. Each creative act or save state can be structured as a Git commit. By its nature, every Git commit is cryptographically hashed (SHA-1) and linked to its parent commit(s), forming a directed acyclic graph. This creates an inherently transparent, timestamped, and cryptographically secured audit trail. Any attempt to alter a past event would change its hash, which would in turn invalidate the hashes of all subsequent commits, making tampering immediately obvious.

This approach effectively provides the most critical features of a blockchain for this specific use case—immutability, cryptographic verification, and a distributed history—without the associated complexity, cost, and scalability challenges of implementing a full Distributed Ledger Technology (DLT) solution.16 While DLT offers benefits in decentralized, trustless environments, the context of a creator tool (often single-user or small-team) makes the built-in integrity of Git a more than sufficient, and far more achievable, foundation.

To complement this, every discrete Asset stored in the ledger will be independently hashed using a strong algorithm like SHA-256.15 This creates a unique, verifiable fingerprint for each piece of content, independent of the Git commit history. This allows the system to prove, for instance, that the specific block of AI-generated text being modified at a later stage is identical to the one originally generated, ensuring the integrity of the entire creative chain of custody.

  

### **2.3 The "HumanAuthorshipScore": A Framework for Quantifying Creative Input**

  

While the law requires a "quantum of human creative contribution," it provides no quantitative measure for what is sufficient.3 This ambiguity is a major source of uncertainty for creators. The proposed

HumanAuthorshipScore is a direct attempt to address this ambiguity, not by creating a new legal standard, but by providing a transparent, data-driven feedback mechanism for the user. It is crucial to understand that the score's primary value is not as a definitive legal metric for a court, but as a real-time UX element that "nudges" the user toward creating a more legally defensible work. It gamifies the process of adding sufficient human authorship, translating the vague legal standard of "more than de minimis" into a clear, actionable UI element, such as a progress bar that moves from red to green as more creative contributions are logged.

The challenge lies in designing a methodology that is both defensible and transparent.22 The score cannot measure aesthetic quality, but it can and must measure the quantity and nature of legally recognized human interventions as recorded in the

Contributions ledger. A potential framework for the score would be a transparent, weighted calculation based on auditable events. For instance:

In this model:

  - The weights () would be assigned based on the relative importance of each type of creative act as interpreted from USCO guidance.
  - Modification\_Events could be quantified by a function of the character count of diffs (additions, deletions, and substitutions).
  - Selection\_Events could be weighted by the ratio of items selected to items generated (e.g., selecting 1 of 10 items is a more significant creative choice than selecting 1 of 2).
  - Arrangement\_Events could be measured by the number of discrete compositional changes (e.g., reordering paragraphs, repositioning images).
  - ExpressiveInput\_Events would grant a baseline score for incorporating pre-existing human-authored work.

The legal defensibility of this score hinges entirely on its **transparency and traceability**. The final Copyright Provenance Report must not simply state the score; it must explicitly show *how* the score was calculated, linking each component of the formula directly back to the specific, timestamped human actions in the ledger.8

  

## **III. Enforcing Copyrightability by Design: The Human-in-the-Loop Workflow**

  

Translating legal theory into a functional software tool requires moving beyond data structures to the dynamic realm of user interaction. The system's workflow and user interface must be meticulously designed to enforce the "human-in-the-loop" model that is central to establishing copyrightability for AI-assisted works.12 This means the UI is not just a creative space but a regulatory environment that guides the user's actions toward legally significant outcomes.

  

### **3.1 The User Interface as a Legal Instrument**

  

The most critical workflow design choice is the implementation of **Mandatory Post-Generation Curation**. As proposed, the system will not permit the direct use or export of raw AI-generated output. Immediately following an AI-Generation event in the ledger, the UI must funnel the user into a distinct "Curation Mode." In this mode, the AI-generated asset is presented as read-only raw material. To proceed, the user is required to perform and log at least one legally recognized creative action: Human-Modification, Human-Selection, or Human-Arrangement.10 This workflow is not optional; it is the sole pathway to transforming the raw material into a component of a "complete" work.

This enforced sequence serves a crucial legal purpose. It programmatically prevents a user from mistakenly creating an uncopyrightable work by simply accepting the first AI output. Furthermore, it directly addresses the "sweat of the brow" fallacy, which the Supreme Court rejected in *Feist Publications, Inc., v. Rural Telephone Service Co.*.11 Copyright does not protect effort alone. A user might expend significant effort in crafting prompts or iteratively regenerating outputs, but the USCO has clarified that this does not constitute authorship.1 The system's workflow correctly de-emphasizes the pre-generation phase. By design, the "real work" from a copyright perspective begins

*after* the AI has produced its output. By logging discrete acts of modification, selection, and arrangement, the system builds an evidentiary case based on the types of creative labor the law recognizes, not the types it has rejected.

To reinforce this, the UI should also provide a transparent "provenance view" or "history panel." This feature would visualize the ledger's contents in a human-readable format, showing the chain of prompts, generations, and modifications that led to the current state of the work. This not only empowers the user with a clear understanding of their creative process but also constantly reminds them of the evidence being generated in the background.

  

### **3.2 Logging the "Quantum of Creativity": Capturing Granular User Interactions**

  

The entire system hinges on the ability to capture the "quantum of creativity" in a granular, event-driven manner. Every significant user interaction must be translated into an immutable entry in the Contributions ledger. This requires a robust logging architecture that captures events on the client side and transmits them to the backend for validation and persistence.26 The system must have a clear and consistent definition of what constitutes a "significant," loggable interaction. This set of events must include, at a minimum:

  - **Human-Prompt:** The submission of a prompt to an AI model, logged with the full text of the prompt.
  - **AI-Generation:** The receipt of a response from an AI model, logged with a reference to the newly created Asset.
  - **Human-Modification:** A "save" event triggered in the editor after a user has altered an asset. The ContributionData for this event must contain the details of the changes.
  - **Human-Selection:** The act of a user choosing one or more assets from a set of AI-generated options. The ContributionData should log the AssetIDs of the selected items as well as the AssetIDs of the items that were rejected.
  - **Human-Arrangement:** An event triggered when a user reorders, repositions, or resizes assets within a larger composition. The ContributionData would store the new compositional metadata.

This granular logging creates more than just a legal record; it generates a valuable data asset. The detailed, structured log of prompts, AI outputs, and the specific human modifications made to those outputs forms a high-quality, paired dataset. This dataset of "raw AI output" -\> "human-refined output" could be used in the future to fine-tune generative models to better align with human creative preferences, creating a powerful feedback loop and a significant competitive advantage. The legal compliance tool thus doubles as a research and development platform.

  

### **3.3 Diffing Algorithms and Interaction Metrics: Technical Approaches to Measuring "Material Alteration"**

  

For the Human-Modification events to have legal weight, the system must be able to technically quantify the extent of the alteration. For textual works, this can be achieved using standard diffing algorithms. The Myers difference algorithm, for example, is highly efficient at identifying the shortest sequence of insertions and deletions to transform one text into another and is a suitable starting point.28 The output of this algorithm—the "diff"—can be stored in the

ContributionData field of the ledger entry.

However, to create a more robust measure of "material alteration," the system should explore more sophisticated techniques beyond simple character-level diffs. **Semantic diffing** could analyze changes in meaning, while **stylistic analysis** could detect changes in tone, voice, or complexity. For instance, changing "The house was big" to "The imposing edifice dominated the skyline" is a far more creative modification than fixing a typo, and a sophisticated analysis could reflect that difference.

Quantifying modifications for non-textual media like images and audio presents a greater challenge, as pixel- or waveform-level diffs are often meaningless in a creative context.29 The solution is to log the specific, high-level user actions performed through the UI's tools. Each of these actions is a discrete

Human-Modification event. For example:

  - **For Images:** Logging events like ApplyFilter (with filter name and parameters), AdjustColorBalance (with RGB values), Crop (with new dimensions), or AddLayer.
  - **For Audio:** Logging events like SpliceClip (with timestamps), ApplyReverb (with effect parameters), AdjustVolume (with decibel change), or ChangeTempo.

In each case, the ContributionData would store a structured object describing the action and its specific parameters, providing a clear record of the user's creative choices.

  

## **IV. Technical Implementation Blueprint: Building a Resilient and Scalable Platform with Jules and Nx**

  

The proposed technical architecture provides a sound and modern foundation for building the Copyright Provenance Ledger tool. The plan to use the AI agent Jules within a structured Nx monorepo is an innovative approach that can accelerate development, provided it is managed with appropriate human oversight. This section provides a critical analysis of the proposed stack and implementation plan, offering expert commentary on its strengths and best practices for execution.

  

### **4.1 The Strategic Advantage of a Monorepo: Leveraging Nx**

  

The decision to use an Nx monorepo is a strategically sound choice for a project of this nature.31 A monorepo, a single repository containing multiple distinct projects, is ideally suited for managing the interconnected components of this system: the React frontend (

/apps/webapp), the Node.js backend (/apps/api), and the core, framework-agnostic copyright-ledger package (/packages/copyright-ledger). This structure facilitates seamless code sharing, such as sharing data types and validation logic between the frontend and backend, which promotes consistency and dramatically reduces boilerplate code.31

Nx, as a build system, adds a layer of intelligent tooling on top of the monorepo structure. Features like "affected commands" ensure that when a change is made, only the projects directly impacted by that change are re-tested and re-built. Nx's computational caching can share build artifacts across the development team and CI/CD pipelines, significantly speeding up development cycles.34 This efficiency is particularly valuable when development is being driven by an AI agent like Jules, which can generate code rapidly.

Furthermore, the choice of a polyglot monorepo is a critical decision for future-proofing the platform. While the initial MVP focuses on text, future expansion to support images, audio, or video will likely require specialized tools and languages (e.g., Python for image analysis, Rust for high-performance media processing). An Nx monorepo is designed to be technology-agnostic, with a rich plugin ecosystem that supports many languages and frameworks.31 This architecture allows new services written in different languages to be seamlessly integrated into the same repository, sharing configurations and types with the existing applications. This initial architectural choice enables a clear and manageable path for future expansion.

  

### **4.2 Phase-by-Phase Implementation Analysis: A Critical Review of the Jules-Driven Plan**

  

The proposed four-phase implementation plan is logical and well-structured, prioritizing the most critical components first.

  - **Phase 1: The Monorepo and MVP Core:** The initial prompt to Jules to scaffold the Nx monorepo, create the React/Node.js applications, and implement the core ledger schema is a clear, discrete, and achievable task. The selection of a local-first database like SQLite is an excellent choice for the MVP, aligning perfectly with the local-first philosophy of the "Scribe" model and minimizing initial infrastructure complexity.36
  - **Phase 2: Building the Provenance-Aware Editor:** Integrating the Monaco Editor into a React application is a well-trodden path, simplified by mature libraries like @monaco-editor/react.39 The prompt correctly specifies the fundamental workflow: a user submits a prompt, the backend service handles the API call to the generative model, a series of  
    Contribution and Asset entries are created in the ledger, and the AI response is displayed in a read-only view, awaiting human intervention.
  - **Phase 3: Implementing the Human Authorship Workflow:** This phase is the functional heart of the application, and the prompt correctly identifies the core requirement: performing a diff on every save event to capture Human-Modification. To ensure a responsive user experience, this implementation should include client-side debouncing of save events to prevent an excessive number of ledger entries during rapid typing. Additionally, the diff calculation itself, if it becomes computationally intensive, should be offloaded to a Web Worker to avoid blocking the main UI thread.
  - **Phase 4: Integration and Final Output:** Creating a dedicated API gateway in the backend to manage and log all external calls to services like Gemini and SudoWrite is a standard best practice for security and observability. The final "Export" function is the culmination of the entire process. The prompt correctly specifies the two essential outputs: the finished creative work and the machine-generated Copyright Provenance Report.

The plan to use Jules as an AI workforce is a powerful force multiplier. However, its success is contingent on adopting a "human-in-the-loop" development process. Jules should be treated as an extremely fast and capable junior developer that requires precise, unambiguous instructions and whose output must be rigorously reviewed, modified, and approved by a senior human architect. The human provides the strategic and legal interpretation, while Jules executes the well-defined coding tasks. This meta-level human-AI collaboration mirrors the very workflow the tool itself is designed to enable.

  

### **4.3 Component Selection and Integration: Best Practices**

  

The selected technology stack is modern, robust, and well-suited for the project's goals.

  - **Frontend (React/JSX):** React's component-based architecture is ideal for building the complex, interactive UI required for a creative tool. Its vast ecosystem provides libraries for virtually any required functionality.
  - **Backend (Node.js/Express):** Node.js offers excellent performance for the I/O-bound tasks typical of a web backend, such as handling API requests and database queries. Express provides a minimalist and flexible framework for building the API service.
  - **Editor (Monaco Editor):** As the editor that powers VS Code, Monaco provides a world-class, feature-rich editing experience out of the box. Its extensive API will be invaluable for tracking granular user interactions like text selections, cursor movements, and other events that could potentially be logged as part of the provenance trail.
  - **Persistence (SQLite/File-based):** The choice of a local-first persistence layer for the MVP is strategically astute. It simplifies development, enhances user privacy and data ownership, and enables offline functionality. For future versions requiring collaboration and cloud backup, this foundation can be extended with synchronization services that sync the local SQLite database or file-based ledger with a central server.

  

## **V. The Final Deliverable: The Legally Defensible Copyright Provenance Report**

  

The ultimate deliverable of the tool is not the creative work itself, but the legally defensible proof of its creation. The Copyright Provenance Report is the culmination of the entire process, translating the granular, technical data from the ledger into a clear, human-readable document designed specifically for submission with a USCO copyright application. Its structure and content must directly address the disclosure and authorship requirements set forth by the Office.

  

### **5.1 Structuring the Report for USCO Submission**

  

The report should be automatically generated and formatted to be as clear and unambiguous as possible for a USCO examiner. It will consist of two primary sections, preceded by standard header information.

**Header Information:**

  - **Author Name:** Full legal name of the human author.
  - **Contact Information:** Email and mailing address.
  - **Work Title:** The title of the work being registered.
  - **Completion Date:** The timestamp when the work was marked as complete in the system.

Section 1: AI-Generated Content Disclaimer

This section is non-negotiable and directly addresses the USCO's disclosure requirement.1 The tool will programmatically generate a precise and exhaustive list of all content within the work that was produced by an AI model and is therefore being disclaimed for copyright purposes. Each entry will be specific and verifiable, linking back to the ledger.

  

Example:

The following content included in this work was generated by an artificial intelligence model and is not claimed as part of this copyright registration:

  - The text content of Asset ID b5c6d7e8-f9g0-1234-5678-90abcdef1234, generated by the Google Gemini 2.5 Pro model (Version v1.2025.10.03) on 2025-10-26 at 09:10:15Z.
  - The initial draft of the image content of Asset ID c3d4e5f6-g7h8-9012-3456-7890abcdef12, generated by the Midjourney model (Version 6.0) on 2025-10-26 at 11:22:05Z.

Section 2: Statement of Human Authorship

This section makes the affirmative case for copyrightability by detailing the human author's creative contributions. It translates the raw event data from the ledger into a compelling narrative. It will begin with a quantitative summary, followed by a detailed, chronological log.

Example Summary:

The human author, \[Author Name\], is the sole author of the copyrightable content in this work. The author's contributions include the performance of 87 material modifications to AI-generated text, 5 acts of creative selection from AI-generated image sets, and 1 act of creative arrangement of selected images into a final composition.

*Example Detailed Log Entry:*

  - **Timestamp:** 2025-10-26T09:15:30Z
  - **Contribution Type:** Human-Modification
  - **Target Asset ID:** b5c6d7e8-f9g0-1234-5678-90abcdef1234
  - **Description:** The author performed substantial edits to the AI-generated text, resulting in the addition of 50 words and the deletion of 12 words. These modifications included rewriting dialogue for character voice and adding a new concluding paragraph to alter the narrative's thematic resolution.

This structure transforms the legal ambiguity inherent in AI-assisted creation into a clear factual declaration. It shifts the conversation with a copyright examiner from a subjective debate over "sufficient human authorship" to a review of objective, auditable facts. The applicant's claim is no longer a vague assertion like "I modified it a lot," but a verifiable statement supported by a precise, timestamped log of creative actions.

  

### **5.2 Automating the Narrative of Creation**

  

A core technical challenge and a significant value proposition of the system is its ability to perform this "data-to-text" translation. The backend must contain logic to iterate through the Contributions ledger for a given Work and synthesize the event data into the prose-based narrative required for the report. This automated generation ensures consistency, accuracy, and completeness, removing the risk of human error in the legally critical disclosure process.

  

### **5.3 Beyond Registration: The Report as a Multi-Purpose IP Asset**

  

While its primary purpose is for USCO registration, the Copyright Provenance Report serves as a vital intellectual property asset in numerous other contexts. It provides verifiable proof of ownership and a clear demarcation of protectable versus unprotectable content, which is invaluable in:

  - **Licensing Negotiations:** Demonstrating to potential licensees the precise scope of the copyright they are acquiring.
  - **Infringement Disputes:** Providing clear, contemporaneous evidence of human authorship to support a claim of infringement.
  - **Due Diligence:** Serving as a key document in mergers, acquisitions, or investment rounds where the value of creative IP assets must be verified.

  

## **VI. Strategic Analysis and Future Trajectory**

  

The proposed tool represents a sophisticated and timely response to a critical challenge at the intersection of technology and law. Its success will depend not only on its technical execution but also on a clear-eyed understanding of its strategic position, potential challenges, and path for future growth.

  

### **6.1 Addressing Potential Challenges**

  

While the design is robust, several challenges must be proactively addressed:

  - **User Experience Friction:** The legally necessary, enforced "human-in-the-loop" workflow introduces friction into a creative process that users may expect to be seamless. The primary challenge for the UI/UX design team will be to make this mandatory curation process feel intuitive, empowering, and value-additive, rather than like a cumbersome bureaucratic hurdle.
  - **Scalability of Granular Logging:** The strategy of logging every significant interaction will generate a substantial volume of data, especially for complex, long-form works. The system's data storage, indexing, and retrieval mechanisms must be highly efficient to prevent performance degradation. The local-first model mitigates this for individual users, but careful planning is required for cloud synchronization and long-term archival.
  - **Adaptability to Non-Textual Media:** The MVP's focus on text is a wise starting point. However, extending the system to images, audio, and video presents a significant future challenge. As discussed, quantifying "material modification" in these domains is far more complex than textual diffing and will require the development of specialized logging for a wide range of creative actions and tools.41 The polyglot monorepo architecture provides a foundation for this, but the implementation will be a major undertaking.

  

### **6.2 Market Positioning and Competitive Differentiation**

  

The tool is positioned to enter a nascent but rapidly growing market of professional and semi-professional creators, authors, artists, and small studios who are leveraging AI but are hampered by legal uncertainty.43 Its competitive differentiation is exceptionally strong because it addresses a fundamentally different problem than adjacent tools.

  - **vs. AI Content Detectors (e.g., Winston AI, Grammarly):** These tools analyze a finished product and attempt to *guess* whether it was AI-generated based on statistical patterns.46 They provide a probabilistic assessment. The proposed tool does not guess; it  
    *knows*. It provides deterministic proof of provenance because it was the environment of creation. Its output is evidence, not an estimate.
  - **vs. Content Provenance Standards (e.g., C2PA):** The Coalition for Content Provenance and Authenticity (C2PA) provides an open standard for embedding provenance metadata directly into media files.49 The proposed tool is not a competitor but a powerful complement. It can generate a C2PA manifest as one of its export formats, populating it with the rich, granular data from its own internal ledger, thereby creating a highly detailed and trustworthy "digital nutrition label."
  - **vs. Creative Workflow Tools (e.g., Ziflow, Workamajig):** These platforms are designed to manage the review and approval stages of a creative workflow, focusing on stakeholder feedback and project management.50 They lack the specific, legally-oriented focus on logging the granular acts of creation required to establish IP ownership.

The core value proposition of this tool is not content creation; it is **Certainty as a Service**. It competes not with other AI writing tools, but with the legal ambiguity and business risk that currently plague the AI-assisted creator economy. Its product is not words or images, but defensible proof of human authorship.

  

### **6.3 Roadmap for Evolution**

  

A phased approach to development will be critical for managing complexity and achieving market traction.

  - **Phase 1: MVP (Text-Based Focus):** Execute the four-phase plan as outlined, focusing exclusively on text-based creative works. The goal is to perfect the core ledger, workflow, and reporting engine.
  - **Phase 2: Multimedia Support:** Begin extending the platform to support image creation. This will involve integrating with image generation APIs and building a new set of UI tools and logging mechanisms for visual modifications (e.g., selection from a 2x2 grid, inpainting/outpainting, filter application, etc.).
  - **Phase 3: Collaboration Features:** Evolve the system from a single-user, local-first application to a multi-user, collaborative platform. This will require implementing a robust cloud synchronization layer for the provenance ledger and features for managing co-authorship and contribution rights.
  - **Phase 4: Integration Ecosystem:** Develop plugins and extensions for popular, existing creative tools (e.g., Adobe Photoshop, Final Cut Pro, VS Code). This would allow creators to use their preferred software while still benefiting from the automated provenance logging running in the background, dramatically expanding the tool's addressable market.
  - **Phase 5: Legal Adaptability:** The legal landscape surrounding AI and copyright is not static.52 The system must be designed for adaptability. The  
    HumanAuthorshipScore algorithm, the structure of the Provenance Report, and even the types of logged events may need to be updated in response to new USCO guidance or court rulings. The platform must be architected to accommodate these changes gracefully.

This strategic trajectory has the potential to establish the tool not just as a product, but as a foundational piece of infrastructure for the creator economy. As AI-assisted works become increasingly common, the demand for verifiable proof of human authorship will grow. A "Copyright Provenance Report" generated by this system could become the industry standard—the equivalent of a CARFAX report for creative works—required for any significant IP transaction. This creates a powerful network effect: the more creators use the tool, the more the market will demand its reports, which in turn drives more creators to the platform, solidifying its position as a fundamental layer of trust.

#### **Works cited**

1.  Copyright Office Publishes Report on Copyrightability of AI-Generated Materials | Insights, accessed October 3, 2025, <https://www.skadden.com/insights/publications/2025/02/copyright-office-publishes-report>
2.  Copyright-and-Artificial-Intelligence-Part-2-Copyrightability-Report.pdf, accessed October 3, 2025, <https://www.copyright.gov/ai/Copyright-and-Artificial-Intelligence-Part-2-Copyrightability-Report.pdf>
3.  Copyright Law in the Age of AI: Navigating Authorship, Infringement ..., accessed October 3, 2025, <https://nysba.org/copyright-law-in-the-age-of-ai-navigating-authorship-infringement-and-creative-rights/>
4.  US Court Decides There is No Copyright in AI-Generated Works - What About Canada?, accessed October 3, 2025, <https://cassels.com/insights/us-court-decides-there-is-no-copyright-in-ai-generated-works-what-about-canada/>
5.  Human Authorship Required: AI Isn't an Author Under Copyright Act - IP Update, accessed October 3, 2025, <https://www.ipupdate.com/2025/03/human-authorship-required-ai-isnt-an-author-under-copyright-act/>
6.  Appellate Court Affirms Human Authorship Requirement for Copyrighting AI-Generated Works | Insights | Skadden, Arps, Slate, Meagher & Flom LLP, accessed October 3, 2025, <https://www.skadden.com/insights/publications/2025/03/appellate-court-affirms-human-authorship>
7.  U.S. Copyright Office issues report on copyrightability of AI assisted and generated works, accessed October 3, 2025, <https://www.hoganlovells.com/en/publications/us-copyright-office-issues-report-on-copyrightability-of-ai-assisted-and-generated-works>
8.  Copyrightability of AI Outputs: U.S. Copyright Office Analyzes Human Authorship Requirement | Insights | Jones Day, accessed October 3, 2025, <https://www.jonesday.com/en/insights/2025/02/copyrightability-of-ai-outputs-us-copyright-office-analyzes-human-authorship-requirement>
9.  Clarifying the Copyrightability of AI-Assisted Works | Foley & Lardner ..., accessed October 3, 2025, <https://www.foley.com/insights/publications/2025/02/clarifying-copyrightability-ai-assisted-works/>
10. Copyright Office Releases Part 2 of Artificial Intelligence Report, accessed October 3, 2025, <https://www.copyright.gov/newsnet/2025/1060.html>
11. Summary of the USCO Copyright and AI Report; Part 2: Copyrightability - Copyright Alliance, accessed October 3, 2025, <https://copyrightalliance.org/ai-report-part-2-copyrightability/>
12. Building Generative AI prompt chaining workflows with human in the ..., accessed October 3, 2025, <https://aws.amazon.com/blogs/machine-learning/building-generative-ai-prompt-chaining-workflows-with-human-in-the-loop/>
13. Human-in-the-Loop: Maintaining Control in an AI-Powered World - Sogolytics Blog, accessed October 3, 2025, <https://www.sogolytics.com/blog/human-in-the-loop-ai/>
14. Exploring Data Provenance: Ensuring Data Integrity and Authenticity - Astera Software, accessed October 3, 2025, <https://www.astera.com/type/blog/data-provenance/>
15. Digital Authenticity: Provenance and Verification in AI-Generated Media - Numbers Protocol, accessed October 3, 2025, <https://numbersprotocol.io/blog/digital-authenticity-provenance-and-verification-in-ai-generated-media>
16. Core structure of a provenance data model. Reprinted with permission... - ResearchGate, accessed October 3, 2025, <https://www.researchgate.net/figure/Core-structure-of-a-provenance-data-model-Reprinted-with-permission-from-Ref-14_fig1_360445341>
17. (PDF) A Design Model of Copyright Protection System Based on ..., accessed October 3, 2025, <https://www.researchgate.net/publication/364180624_A_Design_Model_of_Copyright_Protection_System_Based_on_Distributed_Ledger_Technology>
18. PROV-O: The PROV Ontology - The University of Manchester, accessed October 3, 2025, <https://pure.manchester.ac.uk/ws/files/31956469/FULL_TEXT.PDF>
19. PROV-O: The PROV Ontology | Request PDF - ResearchGate, accessed October 3, 2025, <https://www.researchgate.net/publication/320333535_PROV-O_The_PROV_Ontology>
20. Blockchain for Copyright Protection: Use Cases, Benefits and Challenges - A3Logics, accessed October 3, 2025, <https://www.a3logics.com/blog/blockchain-for-copyright-protection/>
21. LF Decentralized Trust - The open source foundation for decentralized technologies, accessed October 3, 2025, <https://www.lfdecentralizedtrust.org/>
22. Creative Thinking in Art and Design Education: A Systematic Review - MDPI, accessed October 3, 2025, <https://www.mdpi.com/2227-7102/14/2/192>
23. Scoping Review on Digital Creativity: Definition, Approaches, and Current Trends - MDPI, accessed October 3, 2025, <https://www.mdpi.com/2227-7102/15/2/202>
24. A Big Data Approach to Computational Creativity - arXiv, accessed October 3, 2025, <https://arxiv.org/pdf/1311.1213>
25. Humans in the Loop - Colorado Law Scholarly Commons, accessed October 3, 2025, <https://scholar.law.colorado.edu/context/faculty-articles/article/2586/viewcontent/Kaminski_Humans_in_the_Loop.pdf>
26. 11 Best Practices for Logging in Node.js | Better Stack Community, accessed October 3, 2025, <https://betterstack.com/community/guides/logging/nodejs-logging-best-practices/>
27. A Programmer's Guide to Logging Best Practices - Dash0, accessed October 3, 2025, <https://www.dash0.com/guides/logging-best-practices>
28. The 'Diffing' Algorithm Explained | by Tito Adeoye - Medium, accessed October 3, 2025, <https://medium.com/@titoadeoye/the-diffing-algorithm-explained-81d5b11ad9a1>
29. Quantifying the User Experience | Request PDF - ResearchGate, accessed October 3, 2025, <https://www.researchgate.net/publication/316600285_Quantifying_the_User_Experience>
30. User Experience Quantification Model from Online User Reviews - MDPI, accessed October 3, 2025, <https://www.mdpi.com/2076-3417/12/13/6700>
31. Monorepos | Nx, accessed October 3, 2025, <https://nx.dev/docs/concepts/decisions/why-monorepos>
32. Simplify code sharing and project structure with NX for React developers. - Shift Asia, accessed October 3, 2025, <https://shiftasia.com/community/monorepo-made-easy-using-nx-to-manage-react-applications/>
33. Are Nx Monorepo Configurations Really Complex? - Mayallo, accessed October 3, 2025, <https://mayallo.com/nx-monorepo-typescript-configurations/>
34. The Nx Node/React Stack part 1 - Environment - DEV Community, accessed October 3, 2025, <https://dev.to/ibrahimshamma99/nx-nodereact-the-enterprise-stack-part-1-the-environment-5f97>
35. Building a Scalable React Monorepo with NX and Shadcn/UI: A Complete Implementation Guide | by Sakshi Jaiswal | Medium, accessed October 3, 2025, <https://medium.com/@sakshijaiswal0310/building-a-scalable-react-monorepo-with-nx-and-shadcn-ui-a-complete-implementation-guide-96c2bb1b42e8>
36. Intro to Nx - NX Dev, accessed October 3, 2025, <https://nx.dev/getting-started/intro>
37. Monorepos - NX Dev, accessed October 3, 2025, <https://nx.dev/concepts/decisions/why-monorepos>
38. Getting Started with NX Integrated Mono Repo - YouTube, accessed October 3, 2025, <https://www.youtube.com/watch?v=OQQ1HbKm0EM>
39. Integrate Monaco Editor - Sandpack - CodeSandbox, accessed October 3, 2025, <https://sandpack.codesandbox.io/docs/guides/integrate-monaco-editor>
40. monaco-editor/react - NPM, accessed October 3, 2025, <https://www.npmjs.com/package/@monaco-editor/react>
41. The rise of algorithmic art | AI and Art Class Notes - Fiveable, accessed October 3, 2025, <https://fiveable.me/art-and-artificial-intelligence/unit-1/rise-algorithmic-art/study-guide/xyfDj04FJHf48rbU>
42. Algorithmic Art: The Formation of the Genre and Its Perception in Contemporary Society, accessed October 3, 2025, <https://www.researchgate.net/publication/393450373_Algorithmic_Art_The_Formation_of_the_Genre_and_Its_Perception_in_Contemporary_Society>
43. Authorship and Ownership Issues Raised by AI-Generated Works: A Comparative Analysis, accessed October 3, 2025, <https://www.mdpi.com/2075-471X/14/4/57>
44. Copyright Protection for AI-Generated Works: Exploring Originality and Ownership in a Digital Landscape | Asian Journal of International Law | Cambridge Core, accessed October 3, 2025, <https://www.cambridge.org/core/journals/asian-journal-of-international-law/article/copyright-protection-for-aigenerated-works-exploring-originality-and-ownership-in-a-digital-landscape/12B8B8D836AC9DDFFF4082F7859603E3>
45. The Intersection of AI and Copyright: Navigating the Legal Landscape of AI-Generated Art, accessed October 3, 2025, <https://uclawreview.org/2025/06/30/the-intersection-of-ai-and-copyright-navigating-the-legal-landscape-of-ai-generated-art/>
46. Free AI Detector | GPT-4, GPT-3, & ChatGPT AI Checker - Grammarly, accessed October 3, 2025, <https://www.grammarly.com/ai-detector>
47. The Most Trusted AI Detector | ChatGPT Detection Tool, accessed October 3, 2025, <https://gowinston.ai/>
48. AI Detector - Trusted AI Checker for ChatGPT, Copilot & Gemini - Scribbr, accessed October 3, 2025, <https://www.scribbr.com/ai-detector/>
49. C2PA | Verifying Media Content Sources, accessed October 3, 2025, <https://c2pa.org/>
50. Online Proofing Software for Creative & Marketing Teams, accessed October 3, 2025, <https://www.ziflow.com/>
51. Creative Workflow Management: Best Practices + Software Tools - Workamajig, accessed October 3, 2025, <https://www.workamajig.com/blog/creative-workflow-management-system>
52. Patent Landscape Report - Generative Artificial Intelligence (GenAI) - WIPO, accessed October 3, 2025, <https://www.wipo.int/web-publications/patent-landscape-report-generative-artificial-intelligence-genai/en/index.html>
53. AI and Copyright Law: U.S. Framework for Training, Copyrightability, and Digital Replicas, accessed October 3, 2025, <https://huggingface.co/blog/jonathanagustin/ai-copyright-analysis-2025>