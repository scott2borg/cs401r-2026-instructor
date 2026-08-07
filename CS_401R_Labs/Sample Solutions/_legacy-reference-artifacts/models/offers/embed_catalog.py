"""
CS 401R — Lab 3: Model Development
Track B: Offer Generation — Catalog Embedding

Embeds the NorthStar product catalog and policy documents using Amazon Titan
Embeddings (Bedrock), builds a FAISS vector index, and uploads both the index
and metadata to S3 for use by the RAG pipeline at inference time.

Embedding model choice: amazon.titan-embed-text-v2:0
  - Native Bedrock integration: no additional API keys, billed to the same
    AWS account as the rest of the NorthStar platform
  - 1024-dimensional embeddings with strong semantic quality for English retail text
  - Cost: $0.02 per 1,000 tokens (comparable to Cohere Embed v3), but with no
    per-request overhead and native IAM-based access control
  - Alternative considered: Cohere Embed — similar quality but requires separate
    API credential management and cross-service authentication

Chunking strategy:
  - Product catalog: one chunk per product (name + category + description + tags).
    Products are semantically self-contained; splitting across product boundaries
    destroys the unit of retrieval.
  - Policy documents: paragraph-level chunks with 100-token overlap.
    Policy paragraphs are logical units (one rule / one clause). Paragraph
    boundaries preserve meaning better than fixed character counts.

FAISS index type: IndexFlatIP (inner product)
  - Vectors are L2-normalised before indexing, so inner product == cosine similarity
  - Flat (exact) search is appropriate for 12K SKUs + ~200 policy chunks
  - IndexFlatIP is preferred over IndexFlatL2 for cosine similarity because it
    avoids the subtraction step and is numerically cleaner with normalised vectors
  - At 15K vectors × 1024 dims × 4 bytes = ~60MB — well within memory for a
    Lambda function or ECS task

Usage:
    # Run locally (downloads sample catalog from S3 or uses local fixture)
    python embed_catalog.py \
        --catalog-path data/product_catalog.json \
        --policy-dir data/policies/ \
        --output-dir /tmp/northstar-index/ \
        --s3-bucket northstar-dev-artifacts \
        --s3-prefix rag/index/

    # Output: northstar-catalog.index, northstar-catalog-metadata.pkl
"""

import argparse
import json
import logging
import os
import pickle
import re
import time
from pathlib import Path
from typing import Any

import boto3
import faiss
import numpy as np

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

EMBEDDING_MODEL = "amazon.titan-embed-text-v2:0"
DIMENSION = 1024          # Titan Embeddings v2 native dimension
CHUNK_SIZE_TOKENS = 300   # Approximate token limit per product chunk
POLICY_CHUNK_SIZE = 500   # Policy paragraph chunk size in tokens
POLICY_OVERLAP = 100      # Overlap between policy chunks
EMBED_BATCH_SIZE = 20     # Bedrock rate limit: ~20 req/s per model; batch locally
BEDROCK_RETRY_DELAY = 1.0 # Seconds between retries on throttling


# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------

def _approximate_token_count(text: str) -> int:
    """
    Approximate token count using whitespace splitting.
    Titan tokenises similarly to BPE; ~1.3 words per token is a conservative estimate.
    Used only for chunk boundary decisions — not for billing.
    """
    return int(len(text.split()) / 1.3)


def chunk_product_catalog(catalog_path: str, chunk_size: int = CHUNK_SIZE_TOKENS, overlap: int = 50) -> list[dict]:
    """
    Load the product catalog and produce one chunk per product.

    Each chunk is a dict with keys:
        text:       The string to embed
        source:     "catalog"
        product_id: NorthStar SKU
        category:   Product category
        name:       Product name

    For products with very long descriptions (>chunk_size tokens), the description
    is split at sentence boundaries and each sentence-group becomes a separate chunk
    that inherits the product's name, category, and tags as a prefix. This ensures
    the embedding query "waterproof hiking boots" can match even if the description
    is truncated.

    Args:
        catalog_path: Path to product_catalog.json
        chunk_size:   Max tokens per chunk (approximate)
        overlap:      Not used for product chunks (products are self-contained)
                      Kept as parameter for API consistency with chunk_policy_docs.

    Returns:
        List of chunk dicts
    """
    with open(catalog_path, "r", encoding="utf-8") as f:
        catalog = json.load(f)

    chunks = []
    products = catalog if isinstance(catalog, list) else catalog.get("products", [])

    for product in products:
        product_id = product.get("product_id", product.get("sku", "unknown"))
        name = product.get("name", "")
        category = product.get("category", "")
        description = product.get("description", "")
        tags = ", ".join(product.get("tags", []))
        price = product.get("price", "")

        # Build the canonical product text
        prefix = f"Product: {name}\nCategory: {category}\nPrice: ${price}\nTags: {tags}\nDescription: "
        full_text = prefix + description

        if _approximate_token_count(full_text) <= chunk_size:
            # Short product — single chunk
            chunks.append({
                "text": full_text,
                "source": "catalog",
                "product_id": product_id,
                "category": category,
                "name": name,
                "chunk_index": 0,
            })
        else:
            # Long description — split at sentence boundaries
            sentences = re.split(r"(?<=[.!?])\s+", description)
            current_sentences: list[str] = []
            chunk_index = 0

            for sentence in sentences:
                current_sentences.append(sentence)
                candidate = prefix + " ".join(current_sentences)
                if _approximate_token_count(candidate) >= chunk_size:
                    # Flush current chunk
                    chunks.append({
                        "text": prefix + " ".join(current_sentences[:-1]),
                        "source": "catalog",
                        "product_id": product_id,
                        "category": category,
                        "name": name,
                        "chunk_index": chunk_index,
                    })
                    # Start new chunk with last sentence (overlap)
                    current_sentences = [sentence]
                    chunk_index += 1

            # Flush remainder
            if current_sentences:
                chunks.append({
                    "text": prefix + " ".join(current_sentences),
                    "source": "catalog",
                    "product_id": product_id,
                    "category": category,
                    "name": name,
                    "chunk_index": chunk_index,
                })

    logger.info("Product catalog: %d products → %d chunks", len(products), len(chunks))
    return chunks


def chunk_policy_docs(policy_dir: str, chunk_size: int = POLICY_CHUNK_SIZE, overlap: int = POLICY_OVERLAP) -> list[dict]:
    """
    Load all .txt and .md policy documents from policy_dir and chunk at paragraph
    boundaries with token-level overlap.

    Chunking rationale:
      - Policy documents are structured as paragraphs, each containing one rule.
      - Splitting at paragraph boundaries preserves logical units.
      - 100-token overlap ensures that a rule that spans a paragraph break is
        represented in both adjacent chunks, preventing retrieval misses.

    Args:
        policy_dir:  Directory containing policy text files
        chunk_size:  Target chunk size in approximate tokens
        overlap:     Overlap between adjacent chunks in approximate tokens

    Returns:
        List of chunk dicts with keys: text, source, doc_name, chunk_index
    """
    policy_dir_path = Path(policy_dir)
    if not policy_dir_path.exists():
        logger.warning("Policy directory not found: %s — skipping policy chunking", policy_dir)
        return []

    chunks = []
    doc_files = list(policy_dir_path.glob("*.txt")) + list(policy_dir_path.glob("*.md"))

    for doc_path in doc_files:
        doc_name = doc_path.stem
        text = doc_path.read_text(encoding="utf-8")

        # Split on blank lines (paragraph boundaries)
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]

        current_tokens = 0
        current_paras: list[str] = []
        chunk_index = 0
        overlap_buffer: list[str] = []

        for para in paragraphs:
            para_tokens = _approximate_token_count(para)

            if current_tokens + para_tokens > chunk_size and current_paras:
                # Flush chunk
                chunks.append({
                    "text": "\n\n".join(current_paras),
                    "source": "policy",
                    "doc_name": doc_name,
                    "chunk_index": chunk_index,
                })
                chunk_index += 1

                # Build overlap: keep last N tokens worth of paragraphs
                overlap_paras: list[str] = []
                overlap_tokens = 0
                for p in reversed(current_paras):
                    p_tokens = _approximate_token_count(p)
                    if overlap_tokens + p_tokens <= overlap:
                        overlap_paras.insert(0, p)
                        overlap_tokens += p_tokens
                    else:
                        break
                current_paras = overlap_paras
                current_tokens = overlap_tokens

            current_paras.append(para)
            current_tokens += para_tokens

        # Flush last chunk
        if current_paras:
            chunks.append({
                "text": "\n\n".join(current_paras),
                "source": "policy",
                "doc_name": doc_name,
                "chunk_index": chunk_index,
            })

    logger.info("Policy documents: %d files → %d chunks", len(doc_files), len(chunks))
    return chunks


# ---------------------------------------------------------------------------
# Embedding
# ---------------------------------------------------------------------------

def embed_texts(texts: list[str], bedrock_client: Any) -> np.ndarray:
    """
    Embed a list of texts using Amazon Titan Embeddings v2.

    Processes one text at a time (Titan does not support batch embedding requests).
    Retries on ThrottlingException with exponential backoff.

    Args:
        texts:          List of strings to embed
        bedrock_client: boto3 bedrock-runtime client

    Returns:
        numpy array of shape (len(texts), DIMENSION), float32, L2-normalised
    """
    embeddings = []
    total = len(texts)

    for i, text in enumerate(texts):
        if i % 100 == 0:
            logger.info("Embedding %d / %d", i, total)

        # Titan has a 8,192 token limit — truncate if necessary
        if _approximate_token_count(text) > 8000:
            words = text.split()
            text = " ".join(words[:8000])
            logger.warning("Truncated chunk %d to 8000 tokens", i)

        retries = 0
        while True:
            try:
                response = bedrock_client.invoke_model(
                    modelId=EMBEDDING_MODEL,
                    body=json.dumps({
                        "inputText": text,
                        "dimensions": DIMENSION,
                        "normalize": True,   # L2-normalise so IP == cosine similarity
                    }),
                    contentType="application/json",
                    accept="application/json",
                )
                body = json.loads(response["body"].read())
                embedding = np.array(body["embedding"], dtype=np.float32)
                embeddings.append(embedding)
                break

            except bedrock_client.exceptions.ThrottlingException:
                retries += 1
                wait = BEDROCK_RETRY_DELAY * (2 ** retries)
                logger.warning("Throttled on chunk %d — retrying in %.1fs (attempt %d)", i, wait, retries)
                time.sleep(wait)
                if retries > 5:
                    raise RuntimeError(f"Max retries exceeded embedding chunk {i}")

    embeddings_array = np.stack(embeddings, axis=0)
    logger.info("Embedding complete: shape=%s", embeddings_array.shape)
    return embeddings_array


# ---------------------------------------------------------------------------
# FAISS index
# ---------------------------------------------------------------------------

def build_faiss_index(embeddings: np.ndarray) -> faiss.IndexFlatIP:
    """
    Build a FAISS IndexFlatIP (inner product) index.

    IndexFlatIP performs exact nearest-neighbor search using inner product.
    Because Titan embeddings are L2-normalised (norm=1), inner product equals
    cosine similarity. IndexFlat is appropriate here because:
      - Our index size (~15K vectors) is small — exact search completes in <10ms
      - Approximate indexes (IVF, HNSW) trade recall for speed; exact search
        guarantees no retrieval misses at this scale

    Args:
        embeddings: numpy array (n, DIMENSION), float32, already L2-normalised

    Returns:
        Populated FAISS index
    """
    n, d = embeddings.shape
    assert d == DIMENSION, f"Expected embedding dimension {DIMENSION}, got {d}"

    index = faiss.IndexFlatIP(DIMENSION)
    index.add(embeddings)
    logger.info("FAISS index built: %d vectors, dimension %d", index.ntotal, DIMENSION)
    return index


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------

def save_index(index: faiss.IndexFlatIP, metadata: list[dict], output_path: str) -> tuple[str, str]:
    """
    Save the FAISS index and metadata list to disk.

    The metadata list is a parallel array to the FAISS index: metadata[i]
    describes the chunk at FAISS index position i (text, source, product_id, etc.).
    This alignment is maintained throughout — never shuffle or sort after building.

    Args:
        index:       FAISS index
        metadata:    List of chunk dicts (same order as index)
        output_path: Directory path for output files

    Returns:
        (index_path, metadata_path)
    """
    os.makedirs(output_path, exist_ok=True)
    index_path = os.path.join(output_path, "northstar-catalog.index")
    metadata_path = os.path.join(output_path, "northstar-catalog-metadata.pkl")

    faiss.write_index(index, index_path)
    logger.info("FAISS index written: %s (%d vectors)", index_path, index.ntotal)

    with open(metadata_path, "wb") as f:
        pickle.dump(metadata, f, protocol=pickle.HIGHEST_PROTOCOL)
    logger.info("Metadata written: %s (%d entries)", metadata_path, len(metadata))

    return index_path, metadata_path


def upload_to_s3(local_path: str, s3_bucket: str, s3_key: str) -> str:
    """
    Upload a local file to S3.

    The index and metadata are uploaded to S3 so the RAG pipeline Lambda/ECS task
    can download them at cold start. At ~60MB for the full catalog, this download
    takes ~2s on a Lambda with 1GB memory — acceptable for the first invocation.

    Args:
        local_path: Path to local file
        s3_bucket:  Destination bucket
        s3_key:     Destination key

    Returns:
        Full S3 URI (s3://bucket/key)
    """
    s3_client = boto3.client("s3", region_name="us-east-1")
    s3_client.upload_file(local_path, s3_bucket, s3_key)
    uri = f"s3://{s3_bucket}/{s3_key}"
    logger.info("Uploaded %s → %s", local_path, uri)
    return uri


# ---------------------------------------------------------------------------
# Demo data generation (for local testing without real catalog)
# ---------------------------------------------------------------------------

def generate_sample_catalog(output_path: str, n_products: int = 50) -> str:
    """
    Generate a minimal sample product catalog for local testing.
    Run this if you don't have a real catalog file available.
    """
    categories = ["Footwear", "Outerwear", "Accessories", "Activewear", "Homewear"]
    products = []
    for i in range(n_products):
        cat = categories[i % len(categories)]
        products.append({
            "product_id": f"SKU-{i+1:04d}",
            "name": f"NorthStar {cat} Item {i+1}",
            "category": cat,
            "price": round(29.99 + i * 5.5, 2),
            "description": (
                f"Premium quality {cat.lower()} designed for the modern lifestyle. "
                f"Features durable construction, all-season versatility, and NorthStar's "
                f"signature comfort technology. Perfect for loyalty members seeking "
                f"quality and value in the {cat.lower()} category."
            ),
            "tags": [cat.lower(), "new-arrival", "loyalty-reward"],
        })

    catalog = {"products": products}
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2)
    logger.info("Sample catalog written: %s (%d products)", output_path, n_products)
    return output_path


def generate_sample_policies(output_dir: str) -> None:
    """Generate minimal policy documents for local testing."""
    os.makedirs(output_dir, exist_ok=True)

    policies = {
        "return_policy.txt": """Return Policy

NorthStar accepts returns within 60 days of purchase for most items.

Items must be in original condition with tags attached. Worn or washed items are not eligible for return unless defective.

Loyalty members at Gold tier and above receive free return shipping. Bronze and Silver tier members pay $5.99 for return shipping labels.

Refunds are processed within 5-7 business days to the original payment method. Loyalty points are reversed upon return completion.

Gift receipts allow exchange or store credit only — no cash refunds for gift purchases.

Final sale items (marked with red tag in store or "FINAL SALE" online) are not eligible for return or exchange.""",

        "loyalty_program.txt": """NorthStar Loyalty Program Terms

Tier Structure
Bronze: 0–499 points per year
Silver: 500–1,499 points per year
Gold: 1,500–4,999 points per year
Platinum: 5,000+ points per year

Earning Points
Members earn 1 point per $1 spent in-store and online. Double points apply during promotional events. Bonus points are awarded for category-specific purchases during seasonal campaigns.

Redemption
100 points = $1 discount on any purchase. Points cannot be applied to gift cards, taxes, or shipping fees. Minimum redemption is 500 points.

Tier Benefits
Gold members receive: early sale access (48 hours), free standard shipping, 2x points in birthday month.
Platinum members receive: VIP event invitations, dedicated customer service line, 3x points year-round, complimentary gift wrapping.

Expiration
Points expire after 18 months of account inactivity. Tier status resets annually on January 1st based on prior year spending.""",
    }

    for filename, content in policies.items():
        path = os.path.join(output_dir, filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
    logger.info("Sample policy documents written to %s", output_dir)


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="NorthStar Catalog Embedding Pipeline")
    parser.add_argument("--catalog-path", default="data/product_catalog.json",
                        help="Path to product catalog JSON file")
    parser.add_argument("--policy-dir", default="data/policies/",
                        help="Directory containing policy .txt or .md files")
    parser.add_argument("--output-dir", default="/tmp/northstar-index/",
                        help="Local directory for index and metadata output")
    parser.add_argument("--s3-bucket", default=None,
                        help="S3 bucket to upload index to (optional)")
    parser.add_argument("--s3-prefix", default="rag/index/",
                        help="S3 key prefix for uploaded index files")
    parser.add_argument("--region", default="us-east-1",
                        help="AWS region for Bedrock client")
    parser.add_argument("--generate-sample-data", action="store_true",
                        help="Generate sample catalog and policy files for local testing")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    # Optional: generate sample data for local testing without real NorthStar files
    if args.generate_sample_data:
        logger.info("Generating sample data for local testing...")
        catalog_dir = str(Path(args.catalog_path).parent)
        os.makedirs(catalog_dir, exist_ok=True)
        generate_sample_catalog(args.catalog_path, n_products=50)
        generate_sample_policies(args.policy_dir)

    # Validate inputs
    if not Path(args.catalog_path).exists():
        raise FileNotFoundError(
            f"Catalog not found: {args.catalog_path}. "
            "Run with --generate-sample-data to create test fixtures."
        )

    # Build Bedrock client
    bedrock_client = boto3.client("bedrock-runtime", region_name=args.region)

    # ---- 1. Chunk ----
    logger.info("Chunking product catalog: %s", args.catalog_path)
    catalog_chunks = chunk_product_catalog(args.catalog_path)

    logger.info("Chunking policy documents: %s", args.policy_dir)
    policy_chunks = chunk_policy_docs(args.policy_dir)

    all_chunks = catalog_chunks + policy_chunks
    texts = [c["text"] for c in all_chunks]
    logger.info("Total chunks to embed: %d (%d catalog, %d policy)",
                len(all_chunks), len(catalog_chunks), len(policy_chunks))

    # ---- 2. Embed ----
    logger.info("Embedding with Titan Embeddings v2 (this may take several minutes)...")
    embeddings = embed_texts(texts, bedrock_client)

    # Verify normalisation (should be ~1.0 per vector since normalize=True)
    norms = np.linalg.norm(embeddings, axis=1)
    logger.info("Embedding norms: min=%.4f, max=%.4f, mean=%.4f", norms.min(), norms.max(), norms.mean())

    # ---- 3. Build index ----
    index = build_faiss_index(embeddings)

    # ---- 4. Save ----
    index_path, metadata_path = save_index(index, all_chunks, args.output_dir)

    # ---- 5. Upload to S3 (optional) ----
    if args.s3_bucket:
        upload_to_s3(index_path, args.s3_bucket, f"{args.s3_prefix}northstar-catalog.index")
        upload_to_s3(metadata_path, args.s3_bucket, f"{args.s3_prefix}northstar-catalog-metadata.pkl")
        logger.info("Index uploaded to s3://%s/%s", args.s3_bucket, args.s3_prefix)

    print("\n" + "=" * 60)
    print("Embedding Pipeline Complete")
    print("=" * 60)
    print(f"  Catalog chunks:  {len(catalog_chunks)}")
    print(f"  Policy chunks:   {len(policy_chunks)}")
    print(f"  Total vectors:   {index.ntotal}")
    print(f"  FAISS index:     {index_path}")
    print(f"  Metadata:        {metadata_path}")
    if args.s3_bucket:
        print(f"  S3 location:     s3://{args.s3_bucket}/{args.s3_prefix}")
    print("=" * 60)


if __name__ == "__main__":
    main()
