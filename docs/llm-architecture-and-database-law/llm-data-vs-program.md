# **Isolating the Influence of Data in Large Language Models: A Data-Centric Comparative Analysis**

## **1. Introduction: Separating Data from Program in Large Language Models**

The remarkable capabilities of Large Language Models (LLMs) stem from a complex interplay between their architectural design, the algorithms that govern their learning, and the vast quantities of data upon which they are trained. This report focuses on a critical, yet often intertwined, aspect of LLM analysis: the "data portion." The central premise is to explore methodologies for comparing LLMs by isolating the impact of their data, particularly when their underlying "program" – the model architecture and core operational parameters – is held constant. This endeavor necessitates a conceptual separation of data and program, a distinction that becomes clearer if LLMs are not treated as homoiconic systems.

### **1.1. The Concept of Homoiconicity and Its Relevance to LLMs**

Homoiconicity, a term originating from programming language theory, describes a property where a language's code and data share the same structural representation.1 The canonical example is Lisp, where code is represented as lists, which are also the language's primary data structure. This equivalence facilitates powerful metaprogramming capabilities, as code can be manipulated as easily as data.1

However, the application of "homoiconicity" to LLMs is not straightforward and often debated. While LLMs process and generate text (data), and their behavior is encoded in parameters (analogous to a program), the internal and external representations are typically distinct. For instance, the textual input data is vastly different from the numerical weight matrices that constitute the "program." Calvin Mooers, who coined the term, defined it as the external and internal forms of the language being the same.2 This strict definition rarely applies to contemporary LLMs. Critiques of the term highlight the confusion surrounding its various interpretations, such as "code as data" being too broad or the erroneous comparison of program structure to syntax.2 It is often more precise to discuss specific properties, such as the ease of parsing or the nature of internal representations, rather than relying on the ambiguous label of homoiconicity.2

For the purpose of this analysis, LLMs are generally considered non-homoiconic in the strict sense. This distinction is crucial because it supports the conceptual separability of the "program" (the model's architecture, its pre-trained weights representing learned knowledge and capabilities) and the "data" (the specific datasets used for further fine-tuning or instruction tuning that adapt or specialize the pre-existing program). This separation allows for investigations into how varying the data portion, while keeping the program constant, affects LLM performance and behavior.

### **1.2. The Challenge of Instruction-Data Separation in LLMs**

A significant challenge in analyzing the data aspect of LLMs is their inherent difficulty in explicitly separating instructions from the data they are meant to process.3 Instruction-tuned LLMs, for example, are trained to follow commands, but they can be vulnerable to manipulations like indirect prompt injections, where data intended for processing is misinterpreted as an instruction.3 This lack of clear demarcation complicates the study of how a "data portion" influences an LLM, as the model's interpretation of that data can be confounded by its tendency to execute parts of it.

Research has introduced formal measures and empirical benchmarks, such as the SEP dataset, to quantify this phenomenon.3 The empirical separation score (sepc(g)) measures how often a model processes a "probe" string as data versus executing it as an instruction.3 Studies using this framework have revealed that current LLMs, regardless of size or purported capability, generally fail to achieve high instruction-data separation.3 For instance, even advanced models like GPT-4 have shown low separation scores in naive setups, and mitigation techniques like prompt engineering or fine-tuning often either fail to substantially improve separation or come at the cost of reduced model utility.3 An interesting observation is that smaller models sometimes exhibit higher separation, potentially because they lack the capacity for task superposition that allows larger models to attempt to execute both the main task and the probe instruction.4

This inherent blending of instruction and data within the LLM's processing paradigm means that when comparing different "data portions" (e.g., fine-tuning datasets), the "program" (the base LLM) might not treat these data portions purely as passive information. Instead, it might interpret embedded instructions or cues differently across datasets, influencing its behavior in ways that are not solely attributable to the factual content of the data. This underscores the complexity of isolating the pure impact of a data portion. If the model cannot reliably distinguish between what it should *do* and what it should *process*, then the "data portion" is not merely data but a mix of data and implicit (or explicit) instructions. This necessitates careful consideration in experimental design and interpretation when comparing LLMs based on their data inputs.

## **2. Characterizing the "Data Portion" of Large Language Models**

To systematically compare LLMs based on their data, it is essential to first characterize what constitutes the "data portion." This involves distinguishing between different types of data used in an LLM's lifecycle and understanding the properties of datasets used for specific training phases, particularly fine-tuning.

### **2.1. Pre-training Data vs. Fine-tuning Data**

The data an LLM encounters can be broadly categorized into pre-training data and fine-tuning data, each serving a distinct purpose and possessing different characteristics.

  - **Pre-training Data:** This forms the foundational knowledge base of an LLM. It consists of massive and diverse datasets, often scraped from the internet, encompassing books, articles, websites, code repositories, and other textual sources.6 The scale can be enormous; for example, Llama 2 was trained on 2 trillion tokens, 40% more than its predecessor, Llama 1.9 GPT-4 is reported to have digested trillions of words.10 The goal of pre-training is to enable the model to learn general language understanding, syntax, semantics, and a broad range of world knowledge through objectives like next-word prediction.11 The quality and diversity of this pre-training data significantly impact the model's ability to handle nuance, its general knowledge, and its propensity for bias.10 However, pre-training datasets for state-of-the-art models are often proprietary and closed-source, making direct comparisons and replicability challenging.6
  - **Fine-tuning Data (Instruction-Tuning Data):** After pre-training, LLMs are often fine-tuned on smaller, more specialized datasets to adapt them to specific tasks, align them with human preferences, or instill particular behaviors like instruction following.6 Fine-tuning data typically consists of (instruction, output) pairs or prompt-response examples.11 Examples include datasets for chatbot applications (like Llama-2-chat, fine-tuned on over 1 million human annotations 9), domain-specific tasks (e.g., medical or financial data 7), or general instruction following (e.g., databricks-dolly-15k, Alpaca). The focus of the user query – comparing LLMs with the same underlying program based on data differences – primarily pertains to variations in these fine-tuning datasets.

The distinction is critical: the pre-trained model represents the "fixed program" in the context of the user's query, while the fine-tuning dataset is the variable "data portion" whose impact is being assessed. The inherent knowledge and capabilities are largely established during pre-training, while fine-tuning shapes how these capabilities are expressed and applied.17

### **2.2. Comparative Analysis of Key Instruction-Tuning Datasets**

Instruction-tuning datasets are concrete examples of "data portions" used to modify a base LLM's behavior. Understanding their characteristics is fundamental to hypothesizing and interpreting performance differences when a consistent base model is fine-tuned on them. These datasets vary in size, generation methodology, task diversity, and licensing, all of which can influence the resulting model.

Table 1 provides a comparative overview of several prominent instruction-tuning datasets.

  

|  |  |  |  |  |  |  |  |
| :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: |
| \*\*Dataset Name\*\* | \*\*Size (Examples)\*\* | \*\*Primary Source(s)\*\* | \*\*Generation Style\*\* | \*\*Key Task Focus\*\* | \*\*Licensing\*\* | \*\*Notable Strengths/Weaknesses/Biases\*\* | \*\*Relevant Snippets\*\* |
| \*\*databricks-dolly-15k\*\* | \\\~15,000 | Human (Databricks employees), Wikipedia for context | Expert-written, crowd-sourced | Brainstorming, classification, closed QA, generation, info extraction, open QA, summarization | CC BY-SA 3.0 (Commercial use permitted) | Human-generated, diverse tasks. Limitations: Wikipedia bias, potential annotator bias/errors, non-native English speakers. Quality issues identified (factual inaccuracies, vague prompts). | 15 |
| \*\*Alpaca (Stanford)\*\* | 52,000 | GPT-3 (text-davinci-003) | Self-Instruct variant | General instruction following | CC BY-NC 4.0 (Research only) | Low-cost generation, diverse instructions. Original had quality issues (empty outputs, US-centric). Cleaned versions exist. | 24 |
| \*\*AlpacaDataCleaned\*\* | \\\~50,000 (ongoing curation) | GPT-3, GPT-4-LLM dataset | Curated Self-Instruct | General instruction following | (Likely inherits original Alpaca's non-commercial if based on it, or depends on GPT-4-LLM source) | Addresses original Alpaca's quality issues (empty outputs, unclear instructions). Aims for higher quality. | 25 |
| \*\*LIMA (Less Is More for Alignment)\*\* | 1,000 | Human (authors), Community Q\\\&A (Stack Exchange, wikiHow), Reddit (r/WritingPrompts) | Carefully curated, stylistically aligned expert-written & community Q\\\&A | Diverse, complex queries, helpful AI assistant style | CC BY-NC-SA (or stricter if source data is stricter) | High quality, diverse prompts, demonstrates "less is more" for alignment. Small size, non-commercial. | 17 |
| \*\*OpenAssistant-OASST1\*\* | \\\~161,000 messages (varies by export) | Human (crowdsourced volunteers) | Conversational, human feedback ranked | Dialogue, instruction following, assistant-style interaction | Apache 2.0 | Large, multilingual, human-generated and ranked conversations. Quality can vary with crowdsourcing. | 34 |
| \*\*FLAN (Fine-tuned Language Net)\*\* | Varies by version (e.g., Flan 2022 includes \\\>60 datasets, \\\>40k examples for some tasks) | Existing NLP datasets (e.g., P3) | Templated from existing NLP tasks | Broad NLP tasks (QA, NLI, summarization, translation, etc.) | Apache 2.0 (for code/templates, dataset licenses vary by source) | Massive task diversity, improves zero/few-shot generalization. Performance on open-ended instruction following can be poor if not mixed. | 11 |
| \*\*P3 (Public Pool of Prompts)\*\* | 2,052 English prompts applied to 170 English NLP datasets | Existing annotated NLP datasets | Templated from existing NLP tasks | Broad NLP tasks | (Varies by source dataset) | Large collection of prompts, enables task transformation. | 11 |
| \*\*Self-Instruct\*\* | Variable (framework to generate data, e.g., 52k for original Alpaca) | LLM-generated (e.g., GPT-3) | Seed instructions expanded by LLM, outputs generated by LLM | General instruction following | (Depends on LLM used and seed data) | Scalable data generation. Quality depends heavily on seed data and generation model; can be noisy. | 11 |
| \*\*ShareGPT\*\* | \\\~90,000 conversations (common version) | User-shared ChatGPT conversations | Real-world user interactions with ChatGPT | Dialogue, instruction following | (Content is user-generated, often non-commercial use advised) | Real-world conversational data. Can contain noise, PII, and reflect biases of ChatGPT and its users. | 34 |

The evolution of these datasets reveals a maturing understanding of what constitutes an effective "data portion" for fine-tuning. Initially, the challenge was obtaining any instruction data. This led to the use of LLMs themselves to scale generation, as seen with Self-Instruct and the original Alpaca dataset.11 However, this approach often introduced quality issues, such as factual errors, nonsensical instructions, or biases inherent in the generating LLM.15 Consequently, a trend emerged towards higher quality data, either through meticulous human curation of smaller datasets (as exemplified by LIMA, which posits that 1,000 high-quality examples can be highly effective 18) or through extensive cleaning and filtering of larger, potentially noisier datasets (e.g., efforts to clean the Alpaca dataset 25 or analyses of databricks-dolly-15k highlighting areas for improvement 15). This progression underscores that the methodology of creating and refining the "data portion" is as crucial as the raw data itself. The mere fact that data is "human-generated" does not guarantee its superiority over "AI-generated" data if the latter undergoes more rigorous quality control and curation.

Furthermore, the licensing and intended use of these datasets carry significant practical weight. Datasets like Alpaca, with its research-only license 28, confine the direct applicability of models fine-tuned on them to academic circles. Conversely, datasets with commercially permissive licenses, such as databricks-dolly-15k 22, allow for broader deployment and study of the resulting "data-conditioned programs" in real-world applications. These practical constraints inevitably shape the ecosystem of comparable models and influence which "data portions" become most influential in the wider LLM landscape.

## **3. Evaluating Performance and Behavioral Differences Attributable to Data**

Once the "program" (base LLM) is fixed, variations in the "data portion" (fine-tuning dataset) can lead to measurable differences in performance and behavior. This section explores these impacts, focusing on data quality, diversity, scale, and attribution techniques.

### **3.1. Impact of Dataset Quality, Diversity, and Scale on LLM Behavior**

The characteristics of the fine-tuning data profoundly influence the resulting LLM's capabilities and tendencies.

  - **Data Quality:** The adage "garbage in, garbage out" is particularly pertinent to LLM fine-tuning.36 High-quality, clean, and well-curated data is consistently linked to superior model performance, accuracy, and reliability.7 Conversely, faulty data—manifesting as factual inaccuracies, incomplete or vague prompts, spelling errors, biases, Personally Identifiable Information (PII), or toxic content—can severely compromise model performance, leading to the propagation of misinformation, reinforcement of harmful stereotypes, or unreliable outputs.15 For example, analysis of the human-annotated databricks-dolly-15k dataset revealed instances of factual errors (e.g., incorrect inventors or capitals) and vague prompts, despite significant human effort in its curation.15 Similarly, the original Alpaca dataset, generated by GPT-3, suffered from issues like empty outputs and unclear instructions, which necessitated cleaning efforts to improve its utility.25 Tools and methodologies for detecting and mitigating such data issues are crucial for effective fine-tuning.15
  - **Data Diversity:** Training on broader and more diverse datasets enables LLMs to better handle nuance, generalize to unseen tasks, and reduce the likelihood of hallucinations.10 The LIMA paper, for instance, emphasizes the importance of prompt diversity alongside high-quality responses for effective alignment with limited data.17 A lack of diversity in training data is a primary source of bias, potentially leading to discriminatory outputs and the reinforcement of societal stereotypes related to gender, race, or culture.12 Ensuring that fine-tuning datasets represent a wide range of topics, linguistic styles, and demographic perspectives is essential for developing more equitable and robust LLMs.
  - **Data Scale:** The role of data scale differs between pre-training and fine-tuning.

<!-- end list -->

  - For **pre-training**, massive scale is generally considered beneficial for building a broad knowledge base and learning complex language patterns.8
  - For **fine-tuning**, particularly instruction tuning, the "Less Is More for Alignment" (LIMA) hypothesis suggests that a relatively small amount of high-quality, diverse data can be highly effective in teaching a pre-trained model to follow instructions and adopt a desired interaction style.17 The LIMA model itself was fine-tuned on only 1,000 curated examples. The Tulu project, which evaluated LLaMa models fine-tuned on various instruction datasets, also indicated that some datasets can even hurt performance in specific areas, implying that the quality and relevance of fine-tuning data can be more critical than sheer volume.34 However, other research suggests that larger fine-tuning datasets can still offer benefits if data quality and diversity are maintained.32 This indicates a nuanced relationship where the informational efficiency and directive clarity of the fine-tuning data may be paramount, especially when the goal is to shape the behavior of an already knowledgeable pre-trained model. The function of the "data portion" shifts: pre-training data builds broad knowledge, while fine-tuning data directs and refines that knowledge for specific interaction patterns or tasks.

<!-- end list -->

  - **Impact on Bias:** Biases present in training data are inevitably learned and perpetuated by LLMs.7 If a fine-tuning dataset contains gender, racial, or cultural stereotypes, the resulting model is likely to reflect and potentially amplify these biases in its outputs.12 Mitigating such biases requires careful curation of fine-tuning data to ensure diversity and representativeness, alongside other techniques like counterfactual data augmentation or bias detection tools.7

The prevalence of quality issues even in human-curated datasets, such as databricks-dolly-15k 15, highlights that "human-generated" is not an automatic guarantee of "high-quality." Rigorous cleaning, analysis, and curation are essential for any "data portion," regardless of its origin (human or AI-generated), before it can be reliably used for training or comparative evaluation. This adds a layer of complexity when characterizing and comparing data portions, as the raw generation method (e.g., human vs. AI) becomes less critical than the subsequent quality control processes applied.

### **3.2. Techniques for Data Attribution and Tracing Data Influence (Brief Overview)**

Data attribution methods aim to identify and measure the contribution of specific training data instances to a model's outputs or behavior.37 Understanding which parts of a "data portion" are most influential can provide deeper insights into why different datasets lead to varying performance outcomes.

Attribution can be broadly categorized based on when source information is accessed:

  - **Training-time attribution:** Focuses on how the data used to train or fine-tune the model influences its learned parameters and subsequent behavior. This is most relevant to the user's query about comparing "data portions" used to adapt a fixed base model.
  - **Inference-time attribution:** Often associated with Retrieval Augmented Generation (RAG) systems, this aims to trace a model's specific output back to external documents retrieved during inference.37 While distinct, the underlying principles of identifying influential pieces of text can be informative.

Key methods for data attribution include:

  - **Gradient-based methods (e.g., Influence Functions):** These techniques use model gradients to estimate the impact of training samples on model predictions or loss.38 While theoretically grounded, they are often computationally expensive and challenging to scale for LLMs with billions of parameters.38
  - **In-Context Probing (ICP):** This involves prompting an LLM to assess the quality or influence of a training data sample within the context of a task.38 ICP has emerged as a potentially fast and cost-effective proxy for gradient-based methods for data selection, especially when the training data and the target task share similarities in type and content.39 It does not require access to model parameters, making it suitable for black-box models.39
  - **Sentence-Level Attribution for RAG:** Proposed methods include a pre-attribution step to classify sentences based on whether they require zero, one, or multiple references, allowing for more targeted and efficient attribution.37 This approach focuses on verifying the truthfulness of generated sentences by linking them to reliable source sentences.

The development of computationally cheaper proxy methods for data attribution, such as ICP 38, is pivotal for enabling more fine-grained analysis of "data portions" in LLMs. If such methods can reliably identify influential training examples within a fine-tuning dataset, comparisons between different data portions can move beyond aggregate performance metrics to understand *which specific examples* drive observed behavioral differences. This offers a more nuanced understanding than simply concluding that "Dataset A is better than Dataset B."

However, the current limitations of methods like ICP—such as their dependence on task and content similarity between the probe and the data being assessed, and potential issues with group effects when evaluating multiple in-context demonstrations 39—mean that comprehensively attributing influence from diverse, multifaceted fine-tuning datasets remains a complex challenge. A typical instruction-tuning dataset often encompasses a variety of tasks and styles 20, and its overall influence might not be uniformly attributable using a single ICP approach without careful, task-specific application.

### **3.3. Case Studies: Performance Variations in LLMs Fine-Tuned on Different Datasets**

Empirical studies fine-tuning consistent base LLMs on different instruction datasets provide direct evidence of how "data portions" impact performance and behavior.

  - **The Tulu Study (Allen Institute for AI):** This comprehensive study fine-tuned LLaMa-1 models (7B, 13B, 65B) on 12 different instruction-tuning datasets, including well-known ones like Alpaca, databricks-dolly-15k, LIMA, OpenAssistant-OASST1, Self-Instruct, and FLAN, as well as various mixtures.34 Key findings include:

<!-- end list -->

  - No single dataset or mixture yielded the best performance across all evaluation categories (factual knowledge, reasoning, multilinguality, coding, safety). This highlights the specialized nature of different data portions.
  - The quality of the base model is crucial. Subsequent experiments showed that Llama-2 models fine-tuned on the same "Human+GPT" (Tulu) mix significantly outperformed their LLaMa-1 counterparts (e.g., Tulu-2 LLaMa-2 7B achieved an average performance of 46.5 on six benchmarks, compared to 38.8 for Tulu LLaMa-1 7B).34
  - Certain datasets could negatively impact performance in specific areas. For example, datasets with a strong English focus tended to degrade multilingual capabilities. Datasets lacking chain-of-thought examples performed poorly on reasoning tasks that relied on such prompting for evaluation.34
  - Data quality was a significant factor; datasets generated using weaker LLMs (like early Self-Instruct versions) led to poorer outcomes compared to those distilled from more capable models like GPT-4 (e.g., GPT4-Alpaca, ShareGPT).34

<!-- end list -->

  - **Instruction Modelling (IM) vs. Instruction Tuning (IT):** A study explored a novel fine-tuning method called Instruction Modelling (IM), which applies the loss function to both the instruction/prompt and the output, rather than solely to the output as in standard Instruction Tuning (IT).32 Using Llama-7B as the base model, experiments were conducted across various instruction datasets, including subsets of Flan V2, Dolly, Stanford Alpaca, Code Alpaca, and LIMA.

<!-- end list -->

  - IM was found to significantly boost performance on benchmarks like AlpacaEval 1.0, with over 100% improvement in the most advantageous cases.32
  - The effectiveness of IM was particularly pronounced for datasets characterized by lengthy instructions paired with brief outputs (e.g., Code Alpaca) or when using a small number of training examples, aligning with the Superficial Alignment Hypothesis (SAH) that LMs require minimal data for effective instruction tuning if pre-trained capabilities are strong.32
  - Graphical analysis in the paper 32 illustrates varying percentage improvements on AlpacaEval 1.0 when Llama-7B was trained with IM on datasets such as LIMA (1k examples, \~120% improvement), Stanford Alpaca (52k examples, \~25-30% improvement), and Code Alpaca (20k examples, \~70-80% improvement). This suggests an interaction between the dataset's characteristics and the fine-tuning methodology.

<!-- end list -->

  - **Llama2-MedTuned:** Researchers developed Llama2-MedTuned by fine-tuning Llama 2 models on a novel medical instruction dataset created by amalgamating various publicly available medical datasets and reformatting them using an Alpaca-style prompting strategy.43 This demonstrates how a general-purpose base model can be adapted to a specialized domain (medicine) through a carefully constructed "data portion."
  - **The LIMA Paper as a Case Study:** The original LIMA research itself serves as a compelling case study.17 By fine-tuning a LLaMa 65B model on just 1,000 carefully curated examples (the LIMA dataset), the resulting model demonstrated remarkably strong performance, often comparable or preferred to models fine-tuned on much larger datasets like Alpaca (52,000 examples) or even those trained with reinforcement learning from human feedback (RLHF) like DaVinci003.18

These studies collectively underscore that the choice of the fine-tuning "data portion" has a direct, measurable, and often substantial impact on the resulting LLM's skills, factual accuracy, reasoning abilities, safety, and overall behavior. The finding that "base model quality is extremely important" 34 implies that the "fixed program" (the base LLM) establishes a strong foundation for achievable performance. The "data portion" (the fine-tuning dataset) then modulates and directs these inherent capabilities. However, it cannot entirely compensate for fundamental limitations or fully replicate the strengths of a superior base model. This suggests that the base model's architecture and, crucially, its own pre-training data (an earlier, larger "data portion") determine its *capacity to learn effectively* from the subsequent fine-tuning data. Thus, when comparing the effects of different fine-tuning data portions, the selection of the base "program" is itself a critical variable that shapes the observable outcomes.

Furthermore, the varying effectiveness of a fine-tuning dataset depending on the fine-tuning *methodology* (e.g., IM vs. IT 32) introduces another layer of complexity. It suggests that comparisons of "data portions" might also need to account for the specific "sub-program" or process through which that data is integrated into the main model. Dataset A might appear superior to Dataset B under standard instruction tuning, but their relative performance could shift if a different fine-tuning technique like Instruction Modelling is employed, especially if their structural characteristics (like instruction-to-output length ratios) differ significantly.

Table 2 summarizes illustrative performance variations from some of these studies.

  

|  |  |  |  |  |
| :-: | :-: | :-: | :-: | :-: |
| \*\*Base LLM\*\* | \*\*Fine-tuning Dataset/Mix\*\* | \*\*Key Evaluation Benchmark(s)\*\* | \*\*Reported Performance/Observation\*\* | \*\*Source Study Snippet\*\* |
| LLaMa-1 7B | Tulu (Human+GPT mix) | Avg. Perf. on 6 benchmarks (MMLU, TriviaQA, HumanEval, GSM8K, TyDiQA-GoldP, BBH) | 38.8 | 34 |
| Llama-2 7B | Tulu-2 (Human+GPT mix) | Avg. Perf. on 6 benchmarks (as above) | 46.5 (significant improvement over LLaMa-1 base) | 34 |
| Llama-2 13B | Tulu-2 (Human+GPT mix) | Avg. Perf. on 6 benchmarks (as above) | 52.9 | 34 |
| Llama-7B | Stanford Alpaca (52k examples) | AlpacaEval 1.0 (% improvement with IM vs. IT) | Approx. 25-30% | 32 |
| Llama-7B | LIMA (1k examples) | AlpacaEval 1.0 (% improvement with IM vs. IT) | Approx. 120% | 32 |
| Llama-7B | Code Alpaca (20k examples) | AlpacaEval 1.0 (% improvement with IM vs. IT) | Approx. 70-80% | 32 |
| LLaMa 65B | LIMA (1k examples) | Human preference vs. GPT-4 | LIMA equivalent or preferred in 43% of cases | 18 |
| LLaMa 65B | LIMA (1k examples) | Human preference vs. Alpaca 65B (52k examples) | LIMA generally outperformed Alpaca | 18 |
| LLaMa models | ShareGPT / GPT4-Alpaca | ToxiGen (toxicity reduction) | Best performing datasets for reducing toxicity | 34 |
| LLaMa models | ShareGPT / GPT4-Alpaca | TruthfulQA (truthfulness & informativeness) | Effective at improving truthfulness (distillation from GPT-4) | 34 |
| LLaMa models | Self-Instruct / Unnatural Instructions | TruthfulQA / Reasoning Tasks | Poorer performance, potentially detrimental due to lower quality generation | 34 |

## **4. Challenges and Future Directions in Data-Centric LLM Analysis**

While isolating and comparing the "data portion" of LLMs offers valuable insights, this endeavor is fraught with practical and conceptual challenges. Understanding these limitations is key to interpreting current findings and guiding future research.

### **4.1. Practical Challenges in Isolating and Comparing Data Portions**

Several factors complicate the straightforward comparison of data portions in LLMs:

  - **Instruction-Data Separation Failures:** As previously discussed (Section 1.2), LLMs inherently struggle to maintain a clear distinction between instructions to be executed and data to be processed.3 This means that any "data portion" provided during fine-tuning might be partially interpreted as implicit instructions by the "program" (the base LLM), confounding a pure analysis of the data's informational content. The model's behavior might shift not just because of new facts or examples in the data, but because of how it interprets the *structure* or *phrasing* within that data as commands.
  - **Complexity of Real-World (Enterprise) Data:** Much of the research on fine-tuning datasets and their impact relies on publicly available benchmarks or datasets derived from web data. However, real-world enterprise data often presents unique challenges that limit the generalizability of these findings.44 Enterprise datasets can be characterized by:

<!-- end list -->

  - **Large table sizes and high dimensionality:** Far exceeding typical benchmark scales.44
  - **Sparsity:** Many missing values.44
  - **Non-descriptive schemas and values:** Column names or data entries may lack intuitive meaning, unlike curated public datasets.44
  - **Complex tasks:** Often involving multiple steps or compound operations rather than isolated academic tasks.44
  - **Need for internal knowledge:** Tasks may require domain-specific or proprietary knowledge that is absent from the LLM's public pre-training data.44 The effectiveness of a given "data portion" (e.g., a fine-tuning dataset) is thus highly relative to the "parametric knowledge" already encoded in the LLM's "program" from its pre-training phase. If a task requires internal knowledge that the base model fundamentally lacks because it was not part of its pre-training corpus 44, then even a well-designed fine-tuning data portion might be insufficient to elicit the desired performance. This highlights an unavoidable interaction between the pre-training data (an integral part of the "program") and the fine-tuning data portion being evaluated.

<!-- end list -->

  - **Cost and Resources for Experimentation:** Rigorous comparison of data portions necessitates multiple fine-tuning runs of large models, followed by comprehensive evaluations across diverse benchmarks. This process is computationally intensive and expensive, posing a barrier to exhaustive exploration.45
  - **Defining a "Consistent Underlying Program":** While fixing the model architecture (e.g., Llama 2 7B) is a primary step, ensuring true consistency in the "program" can be challenging. Subtle differences in the base model's pre-training data (if not fully transparent or open), minor variations in its training hyperparameters, or even the specific checkpoint used can introduce confounding variables that are not part of the "data portion" being intentionally varied.
  - **Nuances in Evaluation:** Measuring LLM performance is complex. Beyond standard accuracy metrics, factors like generation latency, user engagement, qualitative aspects of response quality (coherence, relevance, safety), and operational costs must be considered.46 Human evaluation is often indispensable for assessing nuanced behaviors, but it is subjective, costly, and time-consuming.46 The difficulty in robustly evaluating LLMs, especially for generative or interactive tasks, means that "performance/behavior comparisons" of data portions are themselves constrained by the limitations of available evaluation methodologies. A data portion might appear superior on one automated metric but inferior on another, or its qualitative differences might be challenging to capture systematically without extensive human oversight. This can lead to situations where the "better" data portion is context-dependent based on the specific application's priorities.

### **4.2. The Role of Ablation Studies in Understanding Data Contributions**

Ablation studies, a common experimental technique in machine learning, involve systematically removing or modifying components of a system to understand their individual contributions to the overall performance.48 This methodology can be adapted to dissect the influence of various aspects of a "data portion."

  - **Application to Data Components:** Instead of just comparing entire, monolithic fine-tuning datasets, ablation studies can be designed to investigate the impact of specific characteristics or subsets within a data portion. For example, one could perform "feature ablation" by removing certain types of tasks (e.g., creative writing vs. closed QA from the databricks-dolly-15k dataset), data sources, or quality-filtered subsets from a fine-tuning mix.48 This allows for a more granular understanding of how different elements of a complex data portion contribute to the observed changes in model behavior or performance.
  - **Illustrative Examples:** The research on SwallowCode and SwallowMath provides a clear example of data-focused ablation.49 The authors developed a multi-stage pipeline to rewrite and refine public code and math data. Their ablation studies confirmed that each stage of this data transformation process—including syntax validation, style filtering, and LLM-based rewriting—incrementally contributed to the performance improvements observed in downstream code generation and mathematical reasoning tasks. This demonstrates how systematic modifications to a "data portion" can be evaluated for their specific impact.
  - **LLMs in Service of Ablation Studies:** An interesting development is the use of LLMs themselves to facilitate the design and execution of ablation studies for other machine learning systems. Tools like AblationMage leverage LLMs to help researchers design ablation trials, generate the necessary code artifacts, and even assist in analyzing and presenting the results.48 This creates a meta-level consideration: LLMs (as a "program") are being employed as tools to analyze the impact of "data portions" on other "programs." If LLMs can effectively suggest ablation strategies for general ML code, they might also be prompted to devise ways to ablate features or components of a *dataset* to better understand its influence on an LLM fine-tuning process, potentially accelerating data-centric research.

Ablation studies on the constituent parts of fine-tuning datasets—such as specific task categories, data sources, or subsets filtered by quality metrics—can offer a more nuanced understanding than simply comparing entire datasets. For instance, one could fine-tune a base model on the databricks-dolly-15k dataset and then on versions of this dataset where "creative writing" examples or "closed QA" examples are systematically removed. By comparing performance on relevant benchmarks, researchers could isolate the contribution of these specific data sub-portions to particular skills. This approach moves towards a more compositional understanding of how "data portions" shape LLM behavior.

### **4.3. Concluding Remarks and Recommendations for Data-Focused LLM Evaluation**

The analysis presented indicates that it is indeed feasible and highly valuable to compare Large Language Models by holding the "program" (the base model architecture and pre-trained weights) constant while varying the "data portion" (primarily the fine-tuning or instruction-tuning dataset). Such comparisons reveal that the characteristics of the data—its quality, diversity, scale, and the methods used for its curation and application—have a profound and measurable impact on the resulting model's performance, behavior, and biases.

To advance this line of inquiry and foster more rigorous, reproducible, and insightful data-centric LLM evaluation, several considerations and recommendations emerge:

1.  **Clarity in Definitions and Experimental Setup:**

<!-- end list -->

  - Researchers must clearly define what constitutes the "fixed program" (e.g., specific base model, version, and checkpoint) and meticulously document the "data portions" being compared (e.g., dataset sources, preprocessing steps, versions, size, and composition).
  - The specific performance and behavioral aspects under evaluation should be explicitly stated, along with the metrics used.

<!-- end list -->

1.  **Standardized Reporting and Openness:**

<!-- end list -->

  - Encouraging detailed reporting of fine-tuning procedures (hyperparameters, methodologies like IT vs. IM) is crucial for reproducibility.
  - Promoting the use of open base models and publicly available fine-tuning datasets, where possible, facilitates broader comparative analysis by the research community.

<!-- end list -->

1.  **Advancements in Methodology:**

<!-- end list -->

  - **Instruction-Data Separation:** Continued research into developing more robust mechanisms, potentially at an architectural level, for LLMs to clearly distinguish between instructions and data is essential for cleaner data impact studies.3
  - **Data Attribution:** Further development of scalable and reliable data attribution techniques for LLMs will allow for finer-grained analysis of which specific elements within a data portion drive observed outcomes.38
  - **Evaluation Protocols:** Creation of more diverse, high-quality, and well-annotated benchmark datasets specifically designed for data-centric LLM comparisons is needed. Evaluation must also increasingly incorporate metrics for safety, bias, and fairness alongside traditional performance measures.12

<!-- end list -->

1.  Towards a Science of Data Engineering for LLMs:  
    The ultimate ambition of comparing "data portions" is to move beyond empirical trial-and-error towards a more principled understanding of "data engineering for LLMs." This involves developing predictive models of how specific data characteristics influence model behavior, enabling more systematic and effective dataset design.6 Systematically comparing data portions and their effects is a critical step in transforming the "art of using data into science".6
2.  Centrality of Ethical Considerations:  
    The ethical implications of "data portions"—including the propagation of biases, ensuring fairness, and promoting equitable representation—must be integral to any comparative evaluation framework.12 Performance metrics alone are insufficient; a data portion that yields high benchmark scores but simultaneously amplifies harmful societal biases or generates toxic content is ultimately detrimental. Therefore, "behavior comparisons" must extend to these critical ethical dimensions.

In conclusion, while the "program" of an LLM provides its foundational capabilities, the "data portion" used for its refinement plays a decisive role in shaping its ultimate utility and behavior. A continued focus on data-centric analysis, supported by rigorous methodologies and a commitment to openness, will be paramount in advancing the development of more capable, reliable, and responsible Large Language Models.

#### **Works cited**

1.  Fuga: A Homoiconic Object-Oriented Programming Language - UNI ..., accessed June 9, 2025, <https://scholarworks.uni.edu/cgi/viewcontent.cgi?article=1891&context=hpt>
2.  Don't say “Homoiconic” – Expressions of Change, accessed June 9, 2025, <https://www.expressionsofchange.org/dont-say-homoiconic/>
3.  Can LLMs Separate Instructions From Data? And What Do We Even ..., accessed June 9, 2025, <https://arxiv.org/abs/2403.06833>
4.  Can LLMs Separate Instructions From Data? And What Do We Even Mean By That?, accessed June 9, 2025, <https://openreview.net/forum?id=8EtSBX41mt>
5.  Can LLMs Separate Instructions From Data? And What Do We Even Mean By That? - arXiv, accessed June 9, 2025, <https://arxiv.org/html/2403.06833v3>
6.  Data-Centric AI in the Age of Large Language Models - ACL Anthology, accessed June 9, 2025, <https://aclanthology.org/2024.findings-emnlp.695.pdf>
7.  Understanding LLM Training Data: A Comprehensive Guide - Uniphore, accessed June 9, 2025, <https://www.uniphore.com/glossary/llm-training-data/>
8.  The Difference Between Large Language Models (LLMs) and Traditional Machine Learning Models - Xeven Solutions, accessed June 9, 2025, <https://www.xevensolutions.com/blog/difference-between-llms-and-traditional-ml-models/>
9.  Comparative Analysis: Llama vs. Llama2 Performance - GoML, accessed June 9, 2025, <https://www.goml.io/blog/comparative-analysis-llama-vs-llama2-performance>
10. LLM Model Comparison: Choosing the Right AI Partner in 2025, accessed June 9, 2025, <https://tensorwave.com/blog/llm-model-comparison>
11. Instruction Tuning for Large Language Models: A Survey - arXiv, accessed June 9, 2025, <https://arxiv.org/html/2308.10792v5>
12. Understanding and Mitigating Bias in Large Language Models (LLMs) | Digital Bricks, accessed June 9, 2025, <https://www.digitalbricks.ai/blog-posts/understanding-and-mitigating-bias-in-large-language-models-llms>
13. Mining LLM Pretraining Data: Topics, Skills, and Cognitive Patterns - Hugging Face, accessed June 9, 2025, <https://huggingface.co/blog/KnutJaegersberg/mining-llm-pretraining-data>
14. LLMs vs. SLMs: The Differences in Large & Small Language Models | Splunk, accessed June 9, 2025, <https://www.splunk.com/en_us/blog/learn/language-models-slm-vs-llm.html>
15. How to detect bad data in your instruction tuning dataset (for better ..., accessed June 9, 2025, <https://cleanlab.ai/blog/filter-llm-tuning-data/>
16. Fine-tuning and Utilization Methods of Domain-specific LLMs - arXiv, accessed June 9, 2025, <https://arxiv.org/pdf/2401.02981>
17. NeurIPS Poster LIMA: Less Is More for Alignment, accessed June 9, 2025, <https://neurips.cc/virtual/2023/poster/72022>
18. LIMA: Less Is More for Alignment - OpenReview, accessed June 9, 2025, <https://openreview.net/pdf?id=KBMOKmX2he>
19. databricks dolly 15k - Kaggle, accessed June 9, 2025, <https://www.kaggle.com/datasets/databricks/databricks-dolly-15k>
20. databricks/databricks-dolly-15k · Datasets at Hugging Face, accessed June 9, 2025, <https://huggingface.co/datasets/databricks/databricks-dolly-15k>
21. databricks/dolly-v2-12b - Hugging Face, accessed June 9, 2025, <https://huggingface.co/databricks/dolly-v2-12b>
22. databricks dolly 15k - Kaggle, accessed June 9, 2025, <https://www.kaggle.com/datasets/yousefsaeedian/databricksdatabricks-dolly-15k>
23. Databricks Dolly 15k Dataset - Papers With Code, accessed June 9, 2025, <https://paperswithcode.com/dataset/databricks-dolly-15k>
24. Fine-tuning Llama-2: The Definitive Guide | Entry Point AI, accessed June 9, 2025, <https://www.entrypointai.com/blog/fine-tune-llama-2/>
25. gururise/AlpacaDataCleaned: Alpaca dataset from Stanford, cleaned and curated - GitHub, accessed June 9, 2025, <https://github.com/gururise/AlpacaDataCleaned>
26. tatsu-lab/alpaca · Datasets at Hugging Face, accessed June 9, 2025, <https://huggingface.co/datasets/tatsu-lab/alpaca>
27. alpaca\_dataset — torchtune 0.5 documentation, accessed June 9, 2025, <https://docs.pytorch.org/torchtune/0.5/generated/torchtune.datasets.alpaca_dataset.html>
28. tatsu-lab/stanford\_alpaca: Code and documentation to train Stanford's Alpaca models, and generate the data. - GitHub, accessed June 9, 2025, <https://github.com/tatsu-lab/stanford_alpaca>
29. LIMA Dataset - Papers With Code, accessed June 9, 2025, <https://paperswithcode.com/dataset/lima>
30. Models - Hugging Face, accessed June 9, 2025, [https://huggingface.co/models?dataset=dataset%3AGAIR%2Flima](https://huggingface.co/models?dataset=dataset:GAIR/lima)
31. GAIR/lima · Datasets at Hugging Face, accessed June 9, 2025, <https://huggingface.co/datasets/GAIR/lima>
32. Instruction Tuning With Loss Over Instructions - NIPS papers, accessed June 9, 2025, <https://proceedings.neurips.cc/paper_files/paper/2024/file/7ffb43adf37b3eeaba559098bc084cc6-Paper-Conference.pdf>
33. LIMA: Less Is More for Alignment, accessed June 9, 2025, <https://arxiv.org/pdf/2305.11206>
34. How Far Can Camels Go? Exploring the State of Instruction Tuning on Open Resources, accessed June 9, 2025, <https://openreview.net/forum?id=w4zZNC4ZaV>
35. Comparison of different instruction tuning datasets, showing that... - ResearchGate, accessed June 9, 2025, <https://www.researchgate.net/figure/Comparison-of-different-instruction-tuning-datasets-showing-that-different_tbl2_371413775>
36. How to improve dataset quality for LLM fine-tuning \[+code guide\] | SuperAnnotate, accessed June 9, 2025, <https://www.superannotate.com/blog/how-to-improve-llm-fine-tuning-dataset-quality>
37. Think Before You Attribute: Improving the Performance of LLMs Attribution Systems - arXiv, accessed June 9, 2025, <https://arxiv.org/html/2505.12621v1>
38. arxiv.org, accessed June 9, 2025, <https://arxiv.org/html/2407.12259v2>
39. On the Feasibility of In-Context Probing for Data ... - ACL Anthology, accessed June 9, 2025, <https://aclanthology.org/2025.findings-naacl.286.pdf>
40. Improving the Performance of LLMs Attribution Systems - arXiv, accessed June 9, 2025, <https://www.arxiv.org/pdf/2505.12621>
41. \[Literature Review\] On the Feasibility of In-Context Probing for Data Attribution - Moonlight, accessed June 9, 2025, <https://www.themoonlight.io/en/review/on-the-feasibility-of-in-context-probing-for-data-attribution>
42. \[2505.12621\] Think Before You Attribute: Improving the Performance of LLMs Attribution Systems - arXiv, accessed June 9, 2025, <https://arxiv.org/abs/2505.12621>
43. Exploring the effectiveness of instruction tuning in biomedical language processing - PMC, accessed June 9, 2025, <https://pmc.ncbi.nlm.nih.gov/articles/PMC12040708/>
44. Unveiling Challenges for LLMs in Enterprise Data Engineering - arXiv, accessed June 9, 2025, <https://arxiv.org/html/2504.10950v1>
45. How Effective are LLMs for Data Science Coding? A Controlled Experiment (MSR 2025 - Technical Papers), accessed June 9, 2025, <https://2025.msrconf.org/details/msr-2025-technical-papers/14/How-Effective-are-LLMs-for-Data-Science-Coding-A-Controlled-Experiment>
46. Beyond prompts: A data-driven approach to LLM optimization - Statsig, accessed June 9, 2025, <https://www.statsig.com/blog/llm-optimization-online-experimentation>
47. LLM Model Size Comparison: Key Insights & Metrics - BytePlus, accessed June 9, 2025, <https://www.byteplus.com/en/topic/456729>
48. Utilizing Large Language Models for Ablation Studies in Machine Learning and Deep Learning - DiVA portal, accessed June 9, 2025, <https://www.diva-portal.org/smash/get/diva2:1941572/FULLTEXT01.pdf>
49. Rewriting Pre-Training Data Boosts LLM Performance in Math and Code - arXiv, accessed June 9, 2025, <https://arxiv.org/abs/2505.02881>
