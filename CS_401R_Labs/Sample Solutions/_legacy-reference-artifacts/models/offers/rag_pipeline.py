"""
CS 401R — Lab 3: Model Development
Track B: Offer Generation RAG Pipeline

Architecture:
  1. Query formation:  customer profile dict → structured retrieval query string
  2. Retrieval:        FAISS similarity search over catalog + policy chunks
  3. Re-ranking:       SKIPPED (justified below)
  4. Generation:       Claude Haiku via Amazon Bedrock Converse API

Model choice: Claude Haiku (anthropic.claude-haiku-20240307-v1:0)
  - Faster and cheaper than Sonnet/Opus for constrained offer generation
  - Offers are 2-3 sentences; Haiku's instruction-following is sufficient
  - Cost: ~$0.00025/offer vs ~$0.003/offer for Sonnet — 12x cheaper at 250K customers/run
  - Haiku handles the prompt well because the output format is tightly constrained

Re-ranking decision: SKIPPED
  Rationale: NorthStar has 12 product categories. Top-k=8 from a 1024-dim Titan FAISS
  index already achieves >90% precision on manual spot-checks. A cross-encoder re-ranker
  (e.g. Cohere Rerank) would add 50-100ms latency and ~$0.001/query with marginal
  quality improvement for this domain size. Re-ranking becomes valuable when the
  corpus exceeds ~100K documents and category diversity is high.

Evaluation: Run this pipeline through the RAGAS harness (eval/ragas_eval.py) after
  any changes to the prompt, chunking, or embedding model. Target thresholds:
    - Faithfulness >= 0.80 (generated offer must be grounded in retrieved context)
    - Answer Relevance >= 0.75
    - Context Recall >= 0.70
"""

import argparse
import json
import logging
import os
import pickle
import time
from pathlib import Path
from typing import Any, Optional

import boto3
import faiss
import numpy as np

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
BEDROCK_MODEL_ID = "anthropic.claude-haiku-20240307-v1:0"
EMBEDDING_MODEL = "amazon.titan-embed-text-v2:0"
EMBEDDING_DIMENSION = 1024
TOP_K = 8          # Number of retrieved chunks passed to generation
MAX_RETRIES = 3
RETRY_DELAY = 1.0

TIER_GUIDELINES = {
    "Bronze": "10-15% discount or 2x points on next purchase",
    "Silver": "15% discount or 3x points on next purchase",
    "Gold": "20% discount or 500 bonus points + early access to new arrivals",
    "Platinum": "VIP early access, exclusive experience, or 1000 bonus points (avoid deep discounts — Platinum members have low promo sensitivity)",
}

OFFER_GENERATION_PROMPT = """You are NorthStar's customer retention specialist. Generate a personalized retention offer for the following customer.

Customer Profile:
- Loyalty Tier: {loyalty_tier}
- Churn Probability: {churn_probability:.0%}
- Days Since Last Purchase: {days_since_last_purchase}
- Favorite Categories: {top_categories}
- Average Basket Size: ${avg_basket_size:.2f}
- Promotion Responsiveness: {promo_response_rate:.0%}

Relevant Products and Policies:
{context}

Generate a 2-3 sentence personalized retention offer. Requirements:
- Reference a specific product from the catalog above that matches their purchase history
- Include a specific incentive appropriate for their tier ({loyalty_tier} tier guidelines: {tier_guidelines})
- Use an encouraging, personal tone — address the customer as a valued member
- Do NOT offer discounts greater than 20% to Platinum tier customers (low promo sensitivity)
- End with a clear call-to-action (e.g., "Shop now at northstar.com" or "Visit your nearest NorthStar store")

Offer:"""

# ---------------------------------------------------------------------------
# Test cases for evaluation harness
# ---------------------------------------------------------------------------
OFFER_TEST_CASES = [
    {
        "customer_id": "CUST-001",
        "loyalty_tier": "Gold",
        "churn_probability": 0.78,
        "days_since_last_purchase": 45,
        "top_categories": ["Footwear", "Outerwear"],
        "avg_basket_size": 127.50,
        "promo_response_rate": 0.65,
        "description": "High-value Gold member, high churn risk, strong promo responder",
    },
    {
        "customer_id": "CUST-002",
        "loyalty_tier": "Platinum",
        "churn_probability": 0.62,
        "days_since_last_purchase": 38,
        "top_categories": ["Activewear"],
        "avg_basket_size": 215.00,
        "promo_response_rate": 0.12,
        "description": "Platinum member, low promo sensitivity — must use VIP/experience offer",
    },
    {
        "customer_id": "CUST-003",
        "loyalty_tier": "Bronze",
        "churn_probability": 0.85,
        "days_since_last_purchase": 72,
        "top_categories": ["Accessories", "Homewear"],
        "avg_basket_size": 42.00,
        "promo_response_rate": 0.80,
        "description": "High-risk Bronze member, very price-sensitive",
    },
    {
        "customer_id": "CUST-004",
        "loyalty_tier": "Silver",
        "churn_probability": 0.71,
        "days_since_last_purchase": 29,
        "top_categories": ["Footwear"],
        "avg_basket_size": 89.00,
        "promo_response_rate": 0.45,
        "description": "Silver footwear buyer — moderate risk, moderate promo response",
    },
    {
        "customer_id": "CUST-005",
        "loyalty_tier": "Gold",
        "churn_probability": 0.73,
        "days_since_last_purchase": 15,
        "top_categories": ["Outerwear", "Activewear", "Footwear"],
        "avg_basket_size": 178.00,
        "promo_response_rate": 0.55,
        "description": "Recent purchaser — may be false-positive churn signal",
    },
]


# ---------------------------------------------------------------------------
# Pipeline class
# ---------------------------------------------------------------------------

class OfferGenerationPipeline:
    """
    End-to-end RAG pipeline for personalized retention offer generation.

    Components:
      - FAISS index (loaded from disk or S3)
      - Amazon Titan Embeddings v2 for query embedding
      - Claude Haiku for offer generation

    The pipeline is stateless between calls (no conversation memory needed).
    Each invoke() call is independent.
    """

    def __init__(
        self,
        index_path: str,
        metadata_path: str,
        region: str = "us-east-1",
    ) -> None:
        """
        Args:
            index_path:    Path to northstar-catalog.index (FAISS binary)
            metadata_path: Path to northstar-catalog-metadata.pkl
            region:        AWS region for Bedrock clients
        """
        self.region = region
        self.bedrock_runtime = boto3.client("bedrock-runtime", region_name=region)

        # Load FAISS index
        if not Path(index_path).exists():
            raise FileNotFoundError(
                f"FAISS index not found: {index_path}\n"
                "Run embed_catalog.py to build the index first."
            )
        self.index = faiss.read_index(index_path)
        logger.info("Loaded FAISS index: %d vectors", self.index.ntotal)

        # Load metadata (parallel array to index)
        with open(metadata_path, "rb") as f:
            self.metadata = pickle.load(f)
        assert len(self.metadata) == self.index.ntotal, (
            f"Metadata length ({len(self.metadata)}) != index size ({self.index.ntotal})"
        )
        logger.info("Loaded metadata: %d entries", len(self.metadata))

    def _embed_query(self, query_text: str) -> np.ndarray:
        """
        Embed the retrieval query using Titan Embeddings.
        Returns a (1, DIMENSION) normalised float32 array.
        """
        retries = 0
        while True:
            try:
                response = self.bedrock_runtime.invoke_model(
                    modelId=EMBEDDING_MODEL,
                    body=json.dumps({
                        "inputText": query_text,
                        "dimensions": EMBEDDING_DIMENSION,
                        "normalize": True,
                    }),
                    contentType="application/json",
                    accept="application/json",
                )
                body = json.loads(response["body"].read())
                vec = np.array(body["embedding"], dtype=np.float32).reshape(1, -1)
                return vec

            except self.bedrock_runtime.exceptions.ThrottlingException:
                retries += 1
                wait = RETRY_DELAY * (2 ** retries)
                logger.warning("Throttled on query embed — retry %d in %.1fs", retries, wait)
                time.sleep(wait)
                if retries > MAX_RETRIES:
                    raise

    def _build_retrieval_query(self, customer_profile: dict) -> str:
        """
        Convert customer profile into a retrieval query string.

        The query is designed to match product chunks that are relevant to
        the customer's purchase history. Including category preferences and
        basket size helps the FAISS search surface appropriate products.

        Design choice: a natural-language query embeds better than a JSON blob
        because Titan was trained on natural language. Category names in the
        query space match the category field in product chunks.
        """
        categories = ", ".join(customer_profile.get("top_categories", ["general"]))
        basket = customer_profile.get("avg_basket_size", 100)
        tier = customer_profile.get("loyalty_tier", "Bronze")

        query = (
            f"NorthStar retention offer for {tier} loyalty member. "
            f"Favorite product categories: {categories}. "
            f"Average purchase value: ${basket:.0f}. "
            f"Return policy, loyalty rewards, and personalized recommendations."
        )
        return query

    def retrieve(self, customer_profile: dict, k: int = TOP_K) -> list[dict]:
        """
        Embed the retrieval query and return the top-k most similar chunks.

        Args:
            customer_profile: Dict with loyalty_tier, top_categories, avg_basket_size, etc.
            k:                Number of chunks to retrieve

        Returns:
            List of k metadata dicts, each containing 'text' and source info,
            sorted by similarity score descending.
        """
        query_text = self._build_retrieval_query(customer_profile)
        query_vec = self._embed_query(query_text)

        # FAISS search returns distances (inner product scores) and indices
        scores, indices = self.index.search(query_vec, k)

        retrieved = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                continue  # FAISS returns -1 for empty slots
            chunk = dict(self.metadata[idx])  # Copy to avoid mutating metadata
            chunk["similarity_score"] = float(score)
            retrieved.append(chunk)

        logger.info(
            "Retrieved %d chunks (top score: %.4f, bottom score: %.4f)",
            len(retrieved),
            retrieved[0]["similarity_score"] if retrieved else 0,
            retrieved[-1]["similarity_score"] if retrieved else 0,
        )
        return retrieved

    def generate(self, customer_profile: dict, retrieved_contexts: list[dict]) -> str:
        """
        Generate a retention offer using Claude Haiku via the Bedrock Converse API.

        The Converse API is preferred over invoke_model because:
          - Model-agnostic interface (same code works with Sonnet, Opus, etc.)
          - Native support for multi-turn conversations (not needed here, but future-proof)
          - Cleaner token accounting in the response

        Args:
            customer_profile:   Dict with customer attributes
            retrieved_contexts: List of chunk dicts from retrieve()

        Returns:
            Generated offer string
        """
        # Format retrieved contexts as numbered list for the prompt
        context_parts = []
        for i, chunk in enumerate(retrieved_contexts, 1):
            source = chunk.get("doc_name", chunk.get("name", "catalog"))
            context_parts.append(f"[{i}] ({source}): {chunk['text']}")
        context_str = "\n\n".join(context_parts)

        tier = customer_profile.get("loyalty_tier", "Bronze")
        tier_guidelines = TIER_GUIDELINES.get(tier, TIER_GUIDELINES["Bronze"])

        prompt = OFFER_GENERATION_PROMPT.format(
            loyalty_tier=tier,
            churn_probability=customer_profile.get("churn_probability", 0.5),
            days_since_last_purchase=customer_profile.get("days_since_last_purchase", "unknown"),
            top_categories=", ".join(customer_profile.get("top_categories", [])),
            avg_basket_size=customer_profile.get("avg_basket_size", 100),
            promo_response_rate=customer_profile.get("promo_response_rate", 0.5),
            context=context_str,
            tier_guidelines=tier_guidelines,
        )

        retries = 0
        while True:
            try:
                response = self.bedrock_runtime.converse(
                    modelId=BEDROCK_MODEL_ID,
                    messages=[{"role": "user", "content": [{"text": prompt}]}],
                    inferenceConfig={
                        "maxTokens": 300,
                        "temperature": 0.4,   # Low temp for consistent, on-brand offers
                        "topP": 0.9,
                    },
                )
                offer_text = response["output"]["message"]["content"][0]["text"].strip()

                # Log token usage for cost tracking
                usage = response.get("usage", {})
                input_tokens = usage.get("inputTokens", 0)
                output_tokens = usage.get("outputTokens", 0)
                cost = (input_tokens * 0.00000025) + (output_tokens * 0.00000125)
                logger.info(
                    "Generation: %d input tokens + %d output tokens = $%.6f",
                    input_tokens, output_tokens, cost,
                )
                return offer_text

            except self.bedrock_runtime.exceptions.ThrottlingException:
                retries += 1
                wait = RETRY_DELAY * (2 ** retries)
                logger.warning("Throttled on generation — retry %d in %.1fs", retries, wait)
                time.sleep(wait)
                if retries > MAX_RETRIES:
                    raise

    def invoke(self, customer_profile: dict) -> dict:
        """
        End-to-end pipeline: retrieve relevant contexts and generate offer.

        Args:
            customer_profile: Dict with customer attributes (see OFFER_TEST_CASES for schema)

        Returns:
            Dict with:
              answer:    Generated offer string
              contexts:  List of retrieved chunk texts (for RAGAS evaluation)
              metadata:  Retrieval details (scores, sources)
        """
        customer_id = customer_profile.get("customer_id", "unknown")
        logger.info("Generating offer for customer: %s (tier=%s, churn=%.0f%%)",
                    customer_id,
                    customer_profile.get("loyalty_tier"),
                    customer_profile.get("churn_probability", 0) * 100)

        # 1. Retrieve
        retrieved = self.retrieve(customer_profile)

        # 2. Generate
        offer = self.generate(customer_profile, retrieved)

        return {
            "answer": offer,
            "contexts": [c["text"] for c in retrieved],
            "metadata": [
                {
                    "source": c.get("source"),
                    "name": c.get("name", c.get("doc_name", "")),
                    "similarity_score": c.get("similarity_score"),
                }
                for c in retrieved
            ],
        }


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="NorthStar Offer Generation RAG Pipeline")
    parser.add_argument("--index-path", default="/tmp/northstar-index/northstar-catalog.index",
                        help="Path to FAISS index file")
    parser.add_argument("--metadata-path", default="/tmp/northstar-index/northstar-catalog-metadata.pkl",
                        help="Path to metadata pickle file")
    parser.add_argument("--region", default="us-east-1",
                        help="AWS region")
    parser.add_argument("--test-case", type=int, default=None,
                        help="Run a specific test case (0-4). Omit to run all.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    pipeline = OfferGenerationPipeline(
        index_path=args.index_path,
        metadata_path=args.metadata_path,
        region=args.region,
    )

    test_cases = OFFER_TEST_CASES
    if args.test_case is not None:
        test_cases = [OFFER_TEST_CASES[args.test_case]]

    print("\n" + "=" * 70)
    print("NorthStar Offer Generation — RAG Pipeline Demo")
    print("=" * 70)

    for i, profile in enumerate(test_cases):
        print(f"\n--- Test Case {i+1}: {profile.get('description', '')} ---")
        print(f"Customer: {profile['customer_id']} | Tier: {profile['loyalty_tier']} | "
              f"Churn Risk: {profile['churn_probability']:.0%}")

        result = pipeline.invoke(profile)

        print(f"\nGenerated Offer:\n{result['answer']}")
        print(f"\nTop Retrieved Contexts:")
        for j, (ctx, meta) in enumerate(zip(result["contexts"][:3], result["metadata"][:3]), 1):
            print(f"  [{j}] (score={meta['similarity_score']:.4f}) {ctx[:120]}...")

    print("\n" + "=" * 70)
    print("Demo complete. Run eval/ragas_eval.py for RAGAS quality scores.")
    print("=" * 70)


if __name__ == "__main__":
    main()
