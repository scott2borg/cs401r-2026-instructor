---
lecture: L08
title: Model Development II — RAG
date: Tuesday, September 29, 2026
week: 5
arc: Build
reading_due: "Model Development — Retrieval-Augmented Generation section"
lab_due: "Lab 2 due Sat Oct 3"
slides_target: 16
---

# L08: Model Development II — RAG
**Tuesday, September 29, 2026 | CS 401R: Engineering Production AI Systems | Fall 2026**

> Retrieval-Augmented Generation architecture, chunking strategies, embedding models, vector databases, reranking, and RAG evaluation. When RAG beats fine-tuning and when it doesn't. NorthStar Offer Generation system design.

**Reading Due:** *Model Development* — "Retrieval-Augmented Generation" section

---

## Slide 1 — Title
**Layout:** Left dark panel + right RAG pipeline diagram

**Content:**
- Model Development II: Retrieval-Augmented Generation (RAG)
- CS 401R · Lecture 08 · Tuesday, September 29, 2026
- Architecture · Chunking · Embedding · Reranking · Evaluation

**Figure:** *RAG pipeline end-to-end diagram.* Horizontal pipeline: User Query (left) → Query Embedding → Vector Search → Top-K Document Retrieval → Context Assembly → Foundation Model (LLM) → Generated Response (right). Three data stores shown above the pipeline: Document Corpus (S3), Vector Index (OpenSearch/FAISS), Metadata Store. Arrows show which stage reads from each store. Clean, light background, color-coded by pipeline stage.

**Notes:** "RAG is the most commonly deployed LLM architecture in enterprise settings — more common than fine-tuning, more practical than prompt engineering alone for knowledge-intensive tasks. Today we build the full picture: why it works, how to engineer it, and how to evaluate it." Check Lab 2 status quickly — due in 4 days.

---

## Slide 2 — Why RAG? The Fundamental Problem It Solves
**Layout:** LLM knowledge limitation diagram + RAG solution

**Content:**
**The Problem with Foundation Models for Enterprise Use:**
1. **Knowledge cutoff:** LLMs know nothing after their training cutoff — NorthStar's current product catalog, today's promotions, and last week's policy updates don't exist in the model
2. **No private data:** LLMs have never seen NorthStar's customer history, purchase behavior, or loyalty status
3. **Hallucination:** When a foundation model doesn't know something, it often makes it up — confidently
4. **Retraining is expensive:** Updating model weights for new knowledge requires full fine-tuning at high cost

**RAG's Answer:**
- Don't put knowledge in the model — put it in a retrieval system
- At inference time, retrieve the relevant knowledge and include it in the prompt
- The model's job: reason over the retrieved context, not memorize facts
- New knowledge? Update the retrieval index — no model retraining required

**Figure:** *Knowledge gap illustration.* Two-panel figure. Left panel: LLM attempting to answer "What is NorthStar's current return policy?" — a large question mark, a "Knowledge cutoff: 2024" label, and a "Hallucinated answer" badge in red. Right panel: RAG system with the same question — retrieval arrow pointing to policy_docs/, relevant policy text extracted, and an accurate answer generated. Before/after contrast is immediate and clear.

**Notes:** "The killer app for RAG in NorthStar is the Offer Generation system. The model needs to know which products this customer is interested in. What's available in the catalog? What promotions are running? None of that is in the model's weights. All of it is in the retrieval index. RAG is the architecture that bridges that gap."

---

## Slide 3 — RAG vs. Fine-Tuning: The Decision Framework
**Layout:** Decision matrix with four quadrants

**Content:**
**When to use RAG:**
- Knowledge is in discrete documents (product catalog, policy docs, FAQs)
- Knowledge changes frequently (new products, updated policies, daily promotions)
- Knowledge needs to be transparent (you want to cite the source document)
- Personalization requires customer-specific data at inference time

**When to use Fine-Tuning:**
- The model needs to behave differently (different tone, format, or reasoning style)
- Task-specific capability doesn't exist in the base model (specialized classification)
- You have thousands of labeled input/output examples

**When to use both (RAG + Fine-Tuning):**
- Fine-tune for behavior and format; RAG for knowledge and personalization
- Common in advanced enterprise deployments

**NorthStar Offer Generation:**
- Uses RAG (not fine-tuning): knowledge changes daily (promotions), requires customer-specific context, source transparency preferred
- Could add fine-tuning later: to improve offer tone and retail-specific language

**Figure:** *2×2 decision quadrant.* X-axis: "Knowledge changes frequently" (No → Yes). Y-axis: "Task-specific behavior needed" (No → Yes). Four quadrants: Prompt Engineering only (low-low), Fine-Tuning (high-low), RAG (low-high), RAG + Fine-Tuning (high-high). NorthStar Offer Generation placed in the "RAG" quadrant. Amazon, Netflix, and Bloomberg examples placed in appropriate quadrants.

**Notes:** "The most common mistake: teams fine-tune a model on their knowledge corpus when RAG would have been faster, cheaper, and more maintainable. Fine-tuning encodes knowledge in the model's weights — which means you need to fine-tune again when that knowledge changes. RAG externalizes knowledge — you update the index, not the model." For NorthStar, the product catalog has 12,000 SKUs that change frequently. RAG is clearly the right choice.

---

## Slide 4 — Document Processing: Chunking Strategies
**Layout:** Chunking strategy comparison with NorthStar examples

**Content:**
**The Chunking Problem:** Documents must be split into retrievable chunks. Chunk too large: slow retrieval, too much irrelevant context. Chunk too small: lose semantic coherence; retrieval misses the relevant piece.

**Chunking Strategies:**

**1. Fixed-Size Chunking (naïve baseline):**
- Split every N tokens (e.g., 512 tokens), with stride overlap
- Fast, simple, works for homogeneous documents
- NorthStar use: customer FAQs (short, uniform documents)

**2. Semantic Chunking:**
- Split at natural boundaries (paragraphs, sections, sentences)
- Preserves semantic coherence; varying chunk sizes
- NorthStar use: return policy documents (structured, hierarchical)

**3. Document-Aware Chunking:**
- Use document structure (headers, bullets, tables) to define chunks
- Best for structured content; preserves context hierarchy
- NorthStar use: product catalog (each SKU = one chunk with all attributes)

**4. Hierarchical Chunking:**
- Multiple layers: summary chunk + detail chunks
- Retrieve summary first; expand to details if needed
- NorthStar use: product category summaries + individual product details

**Figure:** *Chunking strategy visual comparison.* Four panels, each showing a sample document being split. Fixed-size: even cuts at token boundaries, some cuts mid-sentence (highlighted in red). Semantic: natural paragraph breaks. Document-aware: structured by header hierarchy. Hierarchical: two-level tree (summary → details). Each panel shows: chunk count, average chunk size, and a "Semantic coherence" rating (low/medium/high). NorthStar recommended approach labeled for each document type.

**Notes:** "Chunking strategy is one of the highest-leverage decisions in RAG system design. A poor chunking strategy can undermine retrieval, even with a great embedding model. The rule: match your chunking strategy to your document structure. Product catalog entries are naturally chunked by SKU — one chunk per product. Policy documents are naturally chunked by section."

---

## Slide 5 — Embedding Models: Turning Text into Searchable Vectors
**Layout:** Embedding model comparison with NorthStar recommendation

**Content:**
**What is an Embedding?**
A dense numerical vector (e.g., 1,536 dimensions) that represents the semantic meaning of a piece of text. Similar meanings → similar vectors (close in high-dimensional space).

**Embedding Model Options:**

| Model | Provider | Dimensions | Cost | Quality |
|-------|----------|-----------|------|---------|
| text-embedding-3-small | OpenAI | 1,536 | Low | Good |
| text-embedding-3-large | OpenAI | 3,072 | Medium | Excellent |
| amazon.titan-embed-text-v2 | AWS Bedrock | 1,024 | Low | Good |
| cohere.embed-english-v3 | Bedrock/Cohere | 1,024 | Medium | Good |
| all-MiniLM-L6-v2 | HuggingFace (open) | 384 | Free | Acceptable |

**NorthStar recommendation:** `amazon.titan-embed-text-v2` — native Bedrock integration, low cost, good quality for retail content, no data leaves AWS.

**The embedding consistency rule:** Use the same embedding model at indexing time AND query time. Changing the embedding model requires rebuilding the entire vector index.

**Figure:** *Embedding space visualization.* A 2D t-SNE projection of product descriptions from the NorthStar catalog. Products from the same category cluster together (Electronics cluster in blue, Apparel in teal, Home in amber). A user query "looking for comfortable running shoes" shown as a star marker, positioned close to the Apparel cluster. Arrows show the closest product descriptions (top-3 nearest neighbors). The visual makes the "semantic similarity = spatial proximity" concept concrete.

**Notes:** "The embedding space visualization is the intuition pump for RAG. Two texts that mean similar things end up near each other in this space. When the user asks about running shoes, we find the vectors nearest to that query — those are the most semantically similar products in the catalog." Titan Embed on Bedrock is the right choice for NorthStar: no data leaves AWS, minimal latency for AWS-native systems, and the price is appropriate for the volume of embeddings needed.

---

## Slide 6 — Vector Search: The Retrieval Engine
**Layout:** Vector index architecture with search mechanics

**Content:**
**The Vector Store Options:**

| Service | Type | NorthStar Fit |
|---------|------|--------------|
| AWS OpenSearch (k-NN plugin) | Managed, AWS-native | ✅ Best for NorthStar — AWS-integrated, scalable, metadata filtering |
| Pinecone | Managed, third-party | Good but adds vendor dependency |
| pgvector (PostgreSQL) | Self-managed | Good for lower scale; higher operational burden |
| FAISS (in-memory) | Open source, local | Fine for prototyping; not production-grade |
| Chroma | Open source | Good for development; limited scale |

**NorthStar Vector Index Design (OpenSearch):**
- Index: `northstar-product-catalog`
  - Fields: `product_id`, `embedding` (1,024 dims), `category`, `price`, `in_stock`, `description`
  - k-NN search with metadata filter: `in_stock = true AND category = "Footwear"`
- Index: `northstar-policy-docs`
  - Fields: `chunk_id`, `doc_name`, `section`, `embedding`, `chunk_text`

**Retrieval mechanics:** Query embedded → k-NN search returns top-K (typically 5-20) → results reranked → top-3 sent to LLM

**Figure:** *OpenSearch vector search architecture.* Left: Query text → Titan Embed → query vector. Center: OpenSearch k-NN index (shown as a 3D cube with dots representing indexed product vectors). Search returns top-K closest vectors. Right: retrieved product descriptions + metadata. Below: metadata filter showing in_stock=true filter applied before k-NN search. AWS service icons throughout.

**Notes:** "AWS OpenSearch with the k-NN plugin is the production-grade choice for NorthStar. It's fully managed, integrates with IAM, sits inside your VPC, and supports hybrid search (combining semantic k-NN with traditional keyword BM25). The optional Lab 3 bonus task involves setting up this vector index."

---

## Slide 7 — Reranking: Improving Retrieval Precision
**Layout:** Reranking architecture with precision comparison

**Content:**
**Why Reranking?**
First-stage retrieval (k-NN embedding search) optimizes for semantic similarity, which is approximately but not exactly the same as relevance. Reranking applies a more accurate (but slower) relevance scoring to the top-K candidates.

**Reranking Approach:**
1. First stage: k-NN retrieval returns top-20 candidates (fast, approximate)
2. Reranker: cross-encoder model scores each candidate against the query (slower, more accurate)
3. Output: top-3 highest-relevance candidates passed to the LLM

**Reranking Models:**
- Cohere Rerank (available on Bedrock) — strong performance, easy integration
- Cross-encoder models (HuggingFace) — open source, self-hosted
- BM25 hybrid reranker — combines embedding similarity with keyword overlap

**When to add reranking:**
- Retrieval quality is the bottleneck (high recall, low precision)
- Latency budget permits the additional round-trip (adds 50-200ms)
- NorthStar: reranking recommended for policy document retrieval (complex queries)

**Figure:** *Retrieval precision comparison.* Two side-by-side result sets for query "return policy for electronics purchased online." Left (without reranking): top-3 results include 2 irrelevant results. Right (with reranking): top-3 results are all highly relevant. Precision score shown: Before reranking: 33%, After reranking: 100%. Bar charts below show precision@3 across 100 queries for both approaches.

**Notes:** "Reranking is the second-most impactful improvement you can make to a RAG system after fixing your chunking strategy. The embedding model is great at semantic similarity but struggles with nuanced relevance questions. The cross-encoder is much better at relevance but too slow to run on the whole index — so you run it only on the top-K candidates."

---

## Slide 8 — RAG Evaluation: The Hard Part
**Layout:** Evaluation framework with metrics

**Content:**
**RAG Evaluation is Harder Than Model Evaluation:**
- For classification: ground truth is unambiguous (churn or not)
- For RAG: ground truth requires human judgment ("is this answer accurate and helpful?")

**The RAG Evaluation Framework (RAGAS or similar):**

**Component 1: Retrieval Quality**
- **Recall@K:** Was the relevant document in the top-K retrieved results?
- **Precision@K:** How many of the top-K results were actually relevant?
- Requires: a ground-truth dataset of queries paired with relevant documents

**Component 2: Generation Quality**
- **Faithfulness:** Is the generated answer grounded in the retrieved context (no hallucination)?
- **Answer Relevancy:** Does the answer actually address the question?
- **Contextual Precision:** Did the model use only the relevant parts of the retrieved context?

**NorthStar Evaluation Dataset (Lab 3 optional):**
- 50 test queries for offer generation (e.g., "suggest a retention offer for a customer who hasn't purchased Electronics in 90 days")
- Ground-truth relevant documents identified per query
- Human ratings on answer quality (1-5 scale, 3 raters)

**Figure:** *RAGAS evaluation scorecard.* A dashboard showing NorthStar RAG system evaluation results: Recall@5 = 0.84, Precision@3 = 0.71, Faithfulness = 0.89, Answer Relevancy = 0.82, Contextual Precision = 0.77. Each metric is shown as a gauge. Below: comparison between "Baseline RAG (no reranking)" and "Enhanced RAG (with reranking + hybrid search)" showing improvement across all metrics. Clean, metrics-dashboard aesthetic.

**Notes:** "RAG evaluation is where most teams do the least rigorous work. They test a handful of queries manually and declare the system 'working.' What you need is a systematic evaluation dataset, reproducible metrics, and the ability to compare configurations. The RAGAS framework (available as an open-source Python library) provides all of this."

---

## Slide 9 — NorthStar Offer Generation: Full System Design
**Layout:** Complete offer generation architecture diagram

**Content:**
**NorthStar Offer Generation Pipeline:**

**Inputs at inference time:**
- Customer ID → Feature Store lookup → customer history (recency, frequency, preferences)
- Churn probability → from churn model endpoint (if p_churn > 0.4 → trigger retention offer)
- Request context → customer service channel (email, app notification, agent response)

**RAG pipeline:**
1. Query construction: "Customer [ID] preferences: [Electronics, Apparel], last purchase 47 days ago, Gold tier"
2. Retrieval: top-5 matching products from catalog index + current promotions
3. Reranking: cross-encoder reranks by relevance to customer profile
4. Context assembly: customer profile + top-3 products + applicable promotions
5. LLM generation: Bedrock (Claude or Titan) generates personalized offer text

**Output:** Structured offer JSON with offer_text, recommended_products[], discount_code, channel

**Figure:** *NorthStar Offer Generation complete architecture.* Full pipeline diagram showing all components: Feature Store → customer context box → Query Construction block → OpenSearch Vector Index (product catalog + promotions) → Reranker → Context Assembler → Bedrock LLM → Offer JSON output. Churn Model endpoint shown as a gate on the left (only triggers offer generation when p_churn > 0.4). AWS service icons throughout. This is the actual system architecture.

**Notes:** "The integration between the churn model (Lab 3) and the offer generation system (Labs 5+) is the architectural connection point that makes NorthStar a platform rather than three isolated systems. The churn model triggers the offer system. The offer system uses the customer's feature profile from the same Feature Store. This integration is why platform architecture matters."

---

## Slide 10 — Prompt Engineering for RAG: Context Assembly
**Layout:** Prompt template with NorthStar example

**Content:**
**The RAG Prompt Structure:**

```
System: You are NorthStar Retail's customer retention specialist. Generate 
personalized, warm retention offers. Be specific — reference actual products 
the customer has shown interest in. Keep offers under 100 words.

Customer Profile:
- Customer tier: {loyalty_tier}
- Days since last purchase: {recency_days}
- Primary categories: {top_categories}
- Churn probability: {p_churn:.0%}

Relevant Products (retrieved):
{retrieved_products}

Active Promotions:
{active_promotions}

Generate a personalized retention offer for this customer:
```

**Prompt Engineering Rules for RAG:**
1. System prompt defines role and constraints (tone, length, format)
2. Customer profile is structured data from Feature Store
3. Retrieved context is verbatim from the vector index (cited, not summarized)
4. Instruction is specific and constrained (format, length, focus)

**Figure:** *Filled-in prompt example.* The template above, with real NorthStar values filled in: customer is Gold tier, 47 days since last purchase, top categories: Electronics/Apparel, churn probability: 63%. Retrieved products: three specific items from the electronics catalog. Active promotion: "15% off Electronics through October 15." Below the filled prompt: the generated output ("Hi valued customer, we noticed it's been a while — here's a special offer just for you..."). The before/after shows the prompt engineering working.

**Notes:** "The quality of your RAG system is determined by three things in roughly equal measure: the quality of your retrieval, the quality of your context assembly, and the quality of your prompt. A great retrieval system paired with a poorly structured prompt will generate mediocre offers. All three must be engineered carefully."

---

## Slide 11 — Operational Considerations for RAG Systems
**Layout:** Production operations requirements table

**Content:**
**What RAG Systems Need in Production (beyond the model):**

**Index Management:**
- Index update schedule: how often does the product catalog change? → schedule daily reindexing
- Index versioning: if you change chunking strategy, you need a new index (old index stays until migration)
- Index health monitoring: missing documents, failed embeddings, stale data

**Latency Architecture:**
- Retrieval P95 latency target: < 100ms (OpenSearch k-NN, well-indexed)
- Reranking P95: < 200ms
- LLM generation P95: 500-3,000ms (depends on model and output length)
- End-to-end P95 target: < 4,000ms for NorthStar (acceptable for email offers; tighter for real-time agent)

**Cost Management:**
- Embedding cost: ~$0.0001/1K tokens (Titan Embed) × daily reindexing volume
- LLM inference cost: ~$0.003-0.015/1K output tokens depending on model
- Vector index storage: OpenSearch instance cost ~$0.10/hour for small cluster

**Guardrails:**
- Output length limits (max 100 words for offers)
- Content filtering (no hallucinated prices or discount codes)
- Fallback: if retrieval returns no results, use rule-based offer template

**Figure:** *RAG production operations dashboard.* Four panels: (1) Index freshness gauge — "Last indexed: 2 hours ago" (green), (2) E2E latency P95 time series — stable at ~2.3s with one spike to 6s, (3) Daily cost breakdown — embedding + inference + storage = $4.20/day, (4) Guardrail trigger rate — 3% of responses exceeded word limit, 0.1% triggered content filter. This is what Lab 6 monitoring would show for the RAG system.

**Notes:** "The latency budget for the offer generation system is more permissive than for a real-time customer service agent — offers are generated asynchronously and sent via email. If you're building an agent that needs to respond in a live chat conversation, your latency targets are 10× tighter. The architecture choices (which embedding model, which retrieval store, whether to use reranking) flow from the latency budget."

---

## Slide 12 — AWS Bedrock: The RAG Infrastructure
**Layout:** Bedrock Knowledge Bases architecture diagram

**Content:**
**AWS Bedrock Knowledge Bases:**
Fully managed RAG pipeline in AWS — no need to build each component separately.

**What Bedrock Knowledge Bases provides:**
- Document ingestion and chunking (S3 source)
- Embedding generation (Titan Embed, Cohere)
- Vector storage (OpenSearch Serverless managed by AWS)
- Retrieval API (query → retrieve → return top-K chunks)
- Foundation model integration (Claude, Titan, Mistral on Bedrock)

**NorthStar Knowledge Base configuration:**
```python
knowledge_base = BedrockKnowledgeBase(
    name="northstar-offer-knowledge-base",
    description="Product catalog and promotions for offer generation",
    data_sources=[
        S3DataSource("s3://northstar-raw/product_catalog/"),
        S3DataSource("s3://northstar-raw/promotions/"),
        S3DataSource("s3://northstar-raw/policy_docs/"),
    ],
    embedding_model="amazon.titan-embed-text-v2:0",
    chunking_strategy=HierarchicalChunking(parent_size=1500, child_size=300)
)
```

**Trade-off: Bedrock Knowledge Bases vs. custom RAG pipeline:**
- Bedrock KB: fast to build, AWS managed, less flexibility on chunking/retrieval
- Custom pipeline: full control, more engineering, more operational responsibility

**Figure:** *Bedrock Knowledge Bases architecture.* Managed AWS diagram showing: S3 source documents → auto-ingestion → Titan Embed → OpenSearch Serverless index (AWS managed) → retrieval API → Claude model → response. All within the AWS ecosystem. Comparison panel beside it shows "Custom RAG Pipeline" with the same components but more boxes and arrows (more complexity, more control).

**Notes:** "For Lab 3's optional RAG component, I recommend using Bedrock Knowledge Bases — it's the fastest path to a working RAG system and uses the same underlying architecture as a custom build. If your team project requires more control over chunking or retrieval, build a custom pipeline using the components from earlier in this lecture."

---

## Slide 13 — Common RAG Failure Modes
**Layout:** Six failure modes with detection and remediation

**Content:**
1. **Retrieved context is irrelevant:** Embedding model doesn't capture the query intent well. Fix: try a different embedding model; add metadata filtering; add a reranker.

2. **Retrieved context is outdated:** Product catalog was indexed 3 days ago; index not updated after product changes. Fix: automated daily reindexing; index freshness monitoring.

3. **Context window overflow:** Too many retrieved chunks exceed the LLM's context limit. Fix: reduce top-K; truncate chunks; summarize the context before passing it to the LLM.

4. **Hallucination despite retrieval:** Model ignores retrieved context and generates from prior knowledge. Fix: stronger grounding instructions in system prompt; use a faithfulness-oriented model.

5. **Slow retrieval degrading user experience:** Large index without proper indexing strategy. Fix: approximate nearest neighbor indexing (HNSW); reduce embedding dimensions; query caching.

6. **Inconsistent output format:** Model sometimes returns structured JSON, sometimes natural language. Fix: add output format instruction to the system prompt; JSON Schema validation with retry on failure.

**Figure:** *Six-row failure mode table.* Same format as other anti-patterns slides. Detection method column added: "Symptom: precision@3 < 50%" (failure 1), "Symptom: offers reference discontinued products" (failure 2), etc. Quick visual identification of each failure pattern.

**Notes:** "The most insidious failure is #4 — the LLM ignoring the retrieved context. This is harder to detect than retrieval failures because the answer looks fluent and confident. The faithfulness metric (from the RAGAS framework) specifically measures whether the generated answer is grounded in the retrieved context. Always track faithfulness, not just answer quality."

---

## Slide 14 — RAG in the AISDLC: Where Does It Fit?
**Layout:** AISDLC pipeline with RAG-specific stage notes

**Content:**
**The NorthStar Offer Generation AISDLC:**

**Stage 1 (Define Problem):** Success criteria for offer generation: click-through rate ≥ 8% on generated offers, customer complaint rate < 0.5% (measure through A/B testing)

**Stage 2 (Discover Data):** Three data sources needed: product catalog (12K SKUs available), promotions calendar (available), customer history (Feature Store from Lab 2)

**Stage 3 (Prepare Data):** Chunk product catalog by SKU, embed with Titan Embed, index in OpenSearch — this is the "data preparation" stage for a RAG system

**Stage 4 (Design Solution):** Architecture choice: Bedrock Knowledge Bases vs. custom pipeline; chunking strategy; embedding model; reranking decision

**Stage 5 (Develop):** Build the pipeline; run RAGAS evaluation; iterate on chunking and prompts

**Stage 6 (Evaluate):** Gate criteria: Recall@5 ≥ 0.80, Faithfulness ≥ 0.85, Answer Relevancy ≥ 0.80

**Stage 7 (Deploy):** Bedrock endpoint + monitoring; integration with churn model trigger

**Stage 8 (Monitor):** Index freshness, retrieval latency, faithfulness score degradation alerts

**Figure:** *AISDLC 8-stage pipeline with RAG-specific annotations.* Standard 8-stage pipeline from L02, but each stage has a small callout box with the RAG-specific implementation note. Stage 3 callout: "Chunking + Embedding = Data Preparation for RAG." Stage 6 callout: "RAGAS metrics are your gate criteria." Stage 8 callout: "Monitor index freshness + faithfulness." Color-coded in teal (RAG system color).

**Notes:** "Notice that the AISDLC applies to RAG systems just as it applies to traditional ML models. The artifacts are different (a vector index instead of a trained model artifact; RAGAS scores instead of AUC), but the process is the same: define criteria before you build, evaluate against those criteria, gate on results, monitor in production."

---

## Slide 15 — RAG vs. Fine-Tuning Performance: Research Results
**Layout:** Benchmark comparison with enterprise task categories

**Content:**
**Research Finding (OpenAI, 2023):** For knowledge-intensive tasks, RAG outperforms fine-tuning when:
- The knowledge is factual and locatable in documents
- The knowledge base changes frequently
- Retrieval can surface the relevant facts with high precision

**Fine-Tuning outperforms RAG when:**
- Task requires a specific output format or style (not knowledge)
- The task is a new capability (classification, extraction) not inherent in the base model
- Knowledge base is so large that retrieval becomes imprecise

**Enterprise benchmark (Gartner, 2024):**
- 73% of enterprise LLM deployments now use RAG
- Median RAG vs. no-RAG faithfulness improvement: +41%
- Fine-tuning adoption: 31% (many combined with RAG)

**The practical takeaway:** RAG first; add fine-tuning if RAG's output quality is insufficient after optimization.

**Figure:** *Bar chart comparison.* Three task types on the x-axis: Knowledge-Intensive (Q&A), Style/Format, Classification. For each task type: three bars—RAG-only, Fine-tuning-only, RAG + Fine-tuning. Colors: RAG=teal, Fine-tuning=navy, Combined=gold. Shows: RAG wins on knowledge tasks; Fine-tuning wins on style; Combined wins on all. Data labeled clearly as "Illustrative benchmark results."

**Notes:** "The 'RAG first' heuristic holds for most enterprise use cases. Fine-tuning is powerful but requires labeled data and retraining when the knowledge changes. RAG is more agile for enterprise environments where product catalogs, policies, and regulations change continuously."

---

## Slide 16 — Key Takeaways + What's Next
**Layout:** Takeaways + L09 preview + Lab deadlines

**Content:**
**Key Takeaways:**
1. RAG solves the fundamental LLM problem in enterprise settings: knowledge cutoff, no private data, hallucination — without the cost and rigidity of fine-tuning
2. Chunking strategy is the highest-leverage RAG decision: match chunking to document structure (SKU-level for products, section-level for policies)
3. Use the same embedding model at indexing time and query time — changing it requires rebuilding the entire vector index
4. RAG evaluation requires three dimensions: retrieval quality (Recall@K, Precision@K), generation quality (Faithfulness, Answer Relevancy), and end-to-end (business metric)
5. AWS Bedrock Knowledge Bases provides a production-grade managed RAG pipeline — appropriate for NorthStar and most enterprise use cases

**Next Session (Thu Oct 1):**
- Topic: Model Development III — Agents: orchestration, tool use, memory, failure modes, Morgan Stanley case study
- **Lab 3 assigned Thursday** — preview: train the XGBoost churn model from your Lab 2 Feature Store
- **Lab 2 due Saturday Oct 3** — final stretch!

**Figure:** *Five-takeaway summary + Lab timeline.* Standard format. Lab 2 countdown in red (2 days). Lab 3 preview in teal.

**Notes:** "Lab 2 is due Saturday. If you're not in good shape, office hours are today after class and Thursday before Lab 3 is assigned." Then preview: "Thursday we cover agents — the most architecturally complex of the three NorthStar AI systems. If you want a preview, read the agent section of the Model Development chapter."
