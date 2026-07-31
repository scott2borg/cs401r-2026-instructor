# L08: Model Development II — RAG — Figures

## Slide 1 — Title

**Figure:** *RAG pipeline end-to-end diagram.* Horizontal pipeline: User Query (left) → Query Embedding → Vector Search → Top-K Document Retrieval → Context Assembly → Foundation Model (LLM) → Generated Response (right). Three data stores shown above the pipeline: Document Corpus (S3), Vector Index (OpenSearch/FAISS), Metadata Store. Arrows show which stage reads from each store. Clean, light background, color-coded by pipeline stage.

---

## Slide 2 — Why RAG? The Fundamental Problem It Solves

**Figure:** *Knowledge gap illustration.* Two-panel figure. Left panel: LLM attempting to answer "What is NorthStar's current return policy?" — a large question mark, a "Knowledge cutoff: 2024" label, and a "Hallucinated answer" badge in red. Right panel: RAG system with the same question — retrieval arrow pointing to policy_docs/, relevant policy text extracted, and an accurate answer generated. Before/after contrast is immediate and clear.

---

## Slide 3 — RAG vs. Fine-Tuning: The Decision Framework

**Figure:** *2×2 decision quadrant.* X-axis: "Knowledge changes frequently" (No → Yes). Y-axis: "Task-specific behavior needed" (No → Yes). Four quadrants: Prompt Engineering only (low-low), Fine-Tuning (high-low), RAG (low-high), RAG + Fine-Tuning (high-high). NorthStar Offer Generation placed in the "RAG" quadrant. Amazon, Netflix, and Bloomberg examples placed in appropriate quadrants.

---

## Slide 4 — Document Processing: Chunking Strategies

**Figure:** *Chunking strategy visual comparison.* Four panels, each showing a sample document being split. Fixed-size: even cuts at token boundaries, some cuts mid-sentence (highlighted in red). Semantic: natural paragraph breaks. Document-aware: structured by header hierarchy. Hierarchical: two-level tree (summary → details). Each panel shows: chunk count, average chunk size, and a "Semantic coherence" rating (low/medium/high). NorthStar recommended approach labeled for each document type.

---

## Slide 5 — Embedding Models: Turning Text into Searchable Vectors

**Figure:** *Embedding space visualization.* A 2D t-SNE projection of product descriptions from the NorthStar catalog. Products from the same category cluster together (Electronics cluster in blue, Apparel in teal, Home in amber). A user query "looking for comfortable running shoes" shown as a star marker, positioned close to the Apparel cluster. Arrows show the closest product descriptions (top-3 nearest neighbors). The visual makes the "semantic similarity = spatial proximity" concept concrete.

---

## Slide 6 — Vector Search: The Retrieval Engine

**Figure:** *OpenSearch vector search architecture.* Left: Query text → Titan Embed → query vector. Center: OpenSearch k-NN index (shown as a 3D cube with dots representing indexed product vectors). Search returns top-K closest vectors. Right: retrieved product descriptions + metadata. Below: metadata filter showing in_stock=true filter applied before k-NN search. AWS service icons throughout.

---

## Slide 7 — Reranking: Improving Retrieval Precision

**Figure:** *Retrieval precision comparison.* Two side-by-side result sets for query "return policy for electronics purchased online." Left (without reranking): top-3 results include 2 irrelevant results. Right (with reranking): top-3 results are all highly relevant. Precision score shown: Before reranking: 33%, After reranking: 100%. Bar charts below show precision@3 across 100 queries for both approaches.

---

## Slide 8 — RAG Evaluation: The Hard Part

**Figure:** *RAGAS evaluation scorecard.* A dashboard showing NorthStar RAG system evaluation results: Recall@5 = 0.84, Precision@3 = 0.71, Faithfulness = 0.89, Answer Relevancy = 0.82, Contextual Precision = 0.77. Each metric is shown as a gauge. Below: comparison between "Baseline RAG (no reranking)" and "Enhanced RAG (with reranking + hybrid search)" showing improvement across all metrics. Clean, metrics-dashboard aesthetic.

---

## Slide 9 — NorthStar Offer Generation: Full System Design

**Figure:** *NorthStar Offer Generation complete architecture.* Full pipeline diagram showing all components: Feature Store → customer context box → Query Construction block → OpenSearch Vector Index (product catalog + promotions) → Reranker → Context Assembler → Bedrock LLM → Offer JSON output. Churn Model endpoint shown as a gate on the left (only triggers offer generation when p_churn > 0.4). AWS service icons throughout. This is the actual system architecture.

---

## Slide 10 — Prompt Engineering for RAG: Context Assembly

**Figure:** *Filled-in prompt example.* The template above, with real NorthStar values filled in: customer is Gold tier, 47 days since last purchase, top categories: Electronics/Apparel, churn probability: 63%. Retrieved products: three specific items from the electronics catalog. Active promotion: "15% off Electronics through October 15." Below the filled prompt: the generated output ("Hi valued customer, we noticed it's been a while — here's a special offer just for you..."). The before/after shows the prompt engineering working.

---

## Slide 11 — Operational Considerations for RAG Systems

**Figure:** *RAG production operations dashboard.* Four panels: (1) Index freshness gauge — "Last indexed: 2 hours ago" (green), (2) E2E latency P95 time series — stable at ~2.3s with one spike to 6s, (3) Daily cost breakdown — embedding + inference + storage = $4.20/day, (4) Guardrail trigger rate — 3% of responses exceeded word limit, 0.1% triggered content filter. This is what Lab 6 monitoring would show for the RAG system.

---

## Slide 12 — AWS Bedrock: The RAG Infrastructure

**Figure:** *Bedrock Knowledge Bases architecture.* Managed AWS diagram showing: S3 source documents → auto-ingestion → Titan Embed → OpenSearch Serverless index (AWS managed) → retrieval API → Claude model → response. All within the AWS ecosystem. Comparison panel beside it shows "Custom RAG Pipeline" with the same components but more boxes and arrows (more complexity, more control).

---

## Slide 13 — Common RAG Failure Modes

**Figure:** *Six-row failure mode table.* Same format as other anti-patterns slides. Detection method column added: "Symptom: precision@3 < 50%" (failure 1), "Symptom: offers reference discontinued products" (failure 2), etc. Quick visual identification of each failure pattern.

---

## Slide 14 — RAG in the AISDLC: Where Does It Fit?

**Figure:** *AISDLC 8-stage pipeline with RAG-specific annotations.* Standard 8-stage pipeline from L02, but each stage has a small callout box with the RAG-specific implementation note. Stage 3 callout: "Chunking + Embedding = Data Preparation for RAG." Stage 6 callout: "RAGAS metrics are your gate criteria." Stage 8 callout: "Monitor index freshness + faithfulness." Color-coded in teal (RAG system color).

---

## Slide 15 — RAG vs. Fine-Tuning Performance: Research Results

**Figure:** *Bar chart comparison.* Three task types on the x-axis: Knowledge-Intensive (Q&A), Style/Format, Classification. For each task type: three bars—RAG-only, Fine-tuning-only, RAG + Fine-tuning. Colors: RAG=teal, Fine-tuning=navy, Combined=gold. Shows: RAG wins on knowledge tasks; Fine-tuning wins on style; Combined wins on all. Data labeled clearly as "Illustrative benchmark results."

---

## Slide 16 — Key Takeaways + What's Next

**Figure:** *Five-takeaway summary + Lab timeline.* Standard format. Lab 2 countdown in red (2 days). Lab 3 preview in teal.
