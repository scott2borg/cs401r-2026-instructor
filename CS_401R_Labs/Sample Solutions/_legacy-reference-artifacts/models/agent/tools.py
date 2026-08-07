"""
CS 401R — Lab 3: Model Development
Track C: Customer Service Agent — Tool Definitions

Tools implement the business logic that the Bedrock Converse agent can call.

Design principles:
  1. All tools return structured dicts (not strings) — the agent formats responses.
  2. Every tool call is logged: tool name, inputs, output, latency, and estimated cost.
  3. Tools enforce business rules internally (e.g., 60-day return window, $50 credit cap).
     This means the agent cannot circumvent policy by passing boundary inputs.
  4. Tools simulate DynamoDB / API Gateway calls with mock data for demo purposes.
     In production, replace the mock data with real boto3 DynamoDB calls.

Cost tracking:
  Claude Haiku pricing (us-east-1, July 2026):
    Input:  $0.25 per 1M tokens ($0.00000025 per token)
    Output: $1.25 per 1M tokens ($0.00000125 per token)

  Tool call latency and cost are tracked in session_logger.
  Call session_logger.report() at the end of a conversation to see totals.
"""

import json
import logging
import random
import time
from datetime import datetime, timedelta
from typing import Optional

import boto3

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Cost tracking
# ---------------------------------------------------------------------------

# Claude Haiku pricing (update when model pricing changes)
COST_PER_INPUT_TOKEN = 0.00000025    # $0.25 per 1M input tokens
COST_PER_OUTPUT_TOKEN = 0.00000125   # $1.25 per 1M output tokens


class ToolCallLogger:
    """
    Logs all tool calls for a single agent session and accumulates cost.

    Usage:
        session_logger.log("lookup_order", {"order_id": "ORD-123"}, result, latency_ms=45)
        session_logger.report()  # prints summary at end of conversation
    """

    def __init__(self) -> None:
        self.calls: list[dict] = []
        self.total_cost: float = 0.0
        self.session_start: datetime = datetime.utcnow()

    def log(
        self,
        tool_name: str,
        inputs: dict,
        output: dict,
        latency_ms: float,
        cost: float = 0.0,
    ) -> None:
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "tool": tool_name,
            "inputs": inputs,
            "output_keys": list(output.keys()) if isinstance(output, dict) else type(output).__name__,
            "latency_ms": round(latency_ms, 1),
            "cost_usd": cost,
        }
        self.calls.append(entry)
        self.total_cost += cost
        logger.info(
            "[TOOL] %s | latency=%.1fms | cost=$%.6f",
            tool_name, latency_ms, cost,
        )

    def report(self) -> str:
        """Return a formatted session summary."""
        duration = (datetime.utcnow() - self.session_start).total_seconds()
        lines = [
            "",
            "=" * 50,
            "Agent Session Report",
            "=" * 50,
            f"  Session duration: {duration:.1f}s",
            f"  Tool calls:       {len(self.calls)}",
            f"  Total cost:       ${self.total_cost:.6f}",
            "",
            "Tool call breakdown:",
        ]
        for i, call in enumerate(self.calls, 1):
            lines.append(
                f"  {i}. {call['tool']} | {call['latency_ms']}ms | ${call['cost_usd']:.6f}"
            )
        lines.append("=" * 50)
        report_str = "\n".join(lines)
        print(report_str)
        return report_str


# Global logger for the current agent session.
# Reset between sessions: session_logger = ToolCallLogger()
session_logger = ToolCallLogger()


# ---------------------------------------------------------------------------
# Mock data (replace with DynamoDB calls in production)
# ---------------------------------------------------------------------------

_MOCK_ORDERS = {
    "ORD-1234567": {
        "order_id": "ORD-1234567",
        "customer_id": "CUST-001",
        "status": "Shipped",
        "order_date": (datetime.utcnow() - timedelta(days=5)).strftime("%Y-%m-%d"),
        "estimated_delivery": (datetime.utcnow() + timedelta(days=2)).strftime("%Y-%m-%d"),
        "tracking_number": "1Z999AA10123456784",
        "carrier": "UPS",
        "items": [
            {"sku": "SKU-0041", "name": "NorthStar Footwear Item 41", "qty": 1, "price": 129.99},
            {"sku": "SKU-0012", "name": "NorthStar Accessories Item 12", "qty": 2, "price": 24.99},
        ],
        "total": 179.97,
        "payment_method": "Visa ending 4242",
    },
    "ORD-9876543": {
        "order_id": "ORD-9876543",
        "customer_id": "CUST-002",
        "status": "Delivered",
        "order_date": (datetime.utcnow() - timedelta(days=75)).strftime("%Y-%m-%d"),
        "estimated_delivery": (datetime.utcnow() - timedelta(days=68)).strftime("%Y-%m-%d"),
        "tracking_number": "9400111899223397626001",
        "carrier": "USPS",
        "items": [
            {"sku": "SKU-0088", "name": "NorthStar Activewear Item 88", "qty": 1, "price": 215.00},
        ],
        "total": 215.00,
        "payment_method": "Mastercard ending 5555",
    },
    "ORD-5551234": {
        "order_id": "ORD-5551234",
        "customer_id": "CUST-003",
        "status": "Processing",
        "order_date": datetime.utcnow().strftime("%Y-%m-%d"),
        "estimated_delivery": (datetime.utcnow() + timedelta(days=5)).strftime("%Y-%m-%d"),
        "tracking_number": None,
        "carrier": "FedEx",
        "items": [
            {"sku": "SKU-0007", "name": "NorthStar Accessories Item 7", "qty": 3, "price": 18.99},
        ],
        "total": 56.97,
        "payment_method": "PayPal",
    },
}

_MOCK_CUSTOMERS = {
    "CUST-001": {
        "customer_id": "CUST-001",
        "name": "Jordan Martinez",
        "loyalty_tier": "Gold",
        "loyalty_points": 2847,
        "email": "jordan.m@example.com",
    },
    "CUST-002": {
        "customer_id": "CUST-002",
        "name": "Alex Chen",
        "loyalty_tier": "Platinum",
        "loyalty_points": 7420,
        "email": "alex.c@example.com",
    },
    "CUST-003": {
        "customer_id": "CUST-003",
        "name": "Sam Williams",
        "loyalty_tier": "Bronze",
        "loyalty_points": 312,
        "email": "sam.w@example.com",
    },
}

_MOCK_RETURNS = {}  # Populated by initiate_return()
_MOCK_TICKETS = {}  # Populated by escalate_to_human()


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------

def lookup_order(order_id: str) -> dict:
    """
    Return the current status and details of a customer order.

    In production: calls DynamoDB GetItem on the northstar-orders table.
    Simulates ~20ms DynamoDB lookup latency.

    Args:
        order_id: Order ID in format ORD-XXXXXXX

    Returns:
        Order dict with status, items, tracking info, or an error dict.

    Error codes:
        ORDER_NOT_FOUND: order_id does not exist
    """
    t0 = time.monotonic()
    time.sleep(0.02)  # Simulate DynamoDB latency

    order_id = order_id.strip().upper()
    result = _MOCK_ORDERS.get(order_id)

    if result is None:
        output = {
            "error": "ORDER_NOT_FOUND",
            "message": f"No order found with ID {order_id}. Please verify the order ID and try again.",
        }
    else:
        output = dict(result)

    latency_ms = (time.monotonic() - t0) * 1000
    session_logger.log("lookup_order", {"order_id": order_id}, output, latency_ms)
    return output


def query_policy(
    question: str,
    bedrock_client: Optional[object] = None,
    faiss_index: Optional[object] = None,
) -> dict:
    """
    Answer a policy question using RAG over NorthStar policy documents.

    Uses the same FAISS index as the offer generation system. In production,
    this calls the full embed_catalog.py FAISS index. For demo purposes, this
    returns simulated policy answers based on keyword matching.

    In production, pass a live bedrock_client and faiss_index for full RAG.

    Args:
        question:       Natural language question about NorthStar policy
        bedrock_client: Bedrock runtime client (optional — uses mock if None)
        faiss_index:    Loaded FAISS index (optional — uses mock if None)

    Returns:
        Dict with answer, source_documents, confidence
    """
    t0 = time.monotonic()
    time.sleep(0.05)  # Simulate RAG latency

    question_lower = question.lower()

    # Keyword-based mock responses for demo
    # In production: embed question → FAISS search → Claude generation
    if any(word in question_lower for word in ["return", "refund", "exchange"]):
        answer = (
            "NorthStar accepts returns within 60 days of purchase for most items in original condition "
            "with tags attached. Gold and Platinum members receive free return shipping. Bronze and Silver "
            "members pay $5.99 for a return label. Refunds are processed within 5-7 business days. "
            "Final sale items cannot be returned."
        )
        sources = ["return_policy.txt (sections 1-3)"]
        confidence = "high"

    elif any(word in question_lower for word in ["point", "reward", "tier", "loyalty", "redeem"]):
        answer = (
            "NorthStar loyalty members earn 1 point per $1 spent. Redemption rate is 100 points = $1 "
            "discount. Tier thresholds: Bronze 0-499, Silver 500-1499, Gold 1500-4999, Platinum 5000+ "
            "points per year. Points expire after 18 months of inactivity. Gold members get 2x points "
            "in their birthday month; Platinum members earn 3x points year-round."
        )
        sources = ["loyalty_program.txt (sections 1-4)"]
        confidence = "high"

    elif any(word in question_lower for word in ["shipping", "deliver", "track"]):
        answer = (
            "Standard shipping takes 5-7 business days. Expedited shipping (2-3 days) is available for "
            "an additional fee. Gold and Platinum loyalty members receive free standard shipping on all orders. "
            "Tracking numbers are sent via email once the order ships."
        )
        sources = ["shipping_policy.txt (section 2)"]
        confidence = "medium"

    elif any(word in question_lower for word in ["price", "match", "competitor"]):
        answer = (
            "NorthStar offers a 7-day price match guarantee for identical items sold by authorized retailers. "
            "Price match requests must be submitted within 7 days of purchase with proof of the competitor price. "
            "This policy does not apply to marketplace sellers, clearance items, or bundle deals."
        )
        sources = ["price_match_policy.txt"]
        confidence = "medium"

    else:
        # Fall back to a generic response indicating escalation may be needed
        answer = (
            "I found relevant policy information, but the specific answer to your question may require "
            "human review. The most relevant policy sections cover our return, loyalty, and shipping terms."
        )
        sources = ["general_faq.txt"]
        confidence = "low"

    output = {
        "answer": answer,
        "source_documents": sources,
        "confidence": confidence,
    }

    latency_ms = (time.monotonic() - t0) * 1000
    session_logger.log("query_policy", {"question": question[:100]}, output, latency_ms)
    return output


def initiate_return(order_id: str, reason: str) -> dict:
    """
    Initiate a return for a customer order.

    Business rules enforced internally (not left to agent judgment):
      - Order must exist
      - Order must be within 60-day return window (checked against order_date)
      - Orders in "Processing" status cannot be returned — must be cancelled instead
      - Each return gets a unique return ID (RTN-XXXXXXX)

    In production: writes to northstar-returns DynamoDB table and triggers
    a return label generation Lambda.

    Args:
        order_id: Order ID to return
        reason:   Customer-provided reason for return

    Returns:
        Success: {"return_id": str, "status": str, "instructions": str, "label_url": str}
        Error:   {"error": str, "message": str}
    """
    t0 = time.monotonic()
    time.sleep(0.03)  # Simulate write latency

    order_id = order_id.strip().upper()
    order = _MOCK_ORDERS.get(order_id)

    if order is None:
        output = {
            "error": "ORDER_NOT_FOUND",
            "message": f"No order found with ID {order_id}.",
        }
        session_logger.log("initiate_return", {"order_id": order_id, "reason": reason}, output,
                           (time.monotonic() - t0) * 1000)
        return output

    # Check 60-day return window
    order_date = datetime.strptime(order["order_date"], "%Y-%m-%d")
    days_since_order = (datetime.utcnow() - order_date).days

    if days_since_order > 60:
        output = {
            "error": "OUTSIDE_RETURN_WINDOW",
            "message": (
                f"Order {order_id} was placed {days_since_order} days ago. "
                "NorthStar's return policy allows returns within 60 days of purchase. "
                "This order is outside the eligible return window."
            ),
        }
        session_logger.log("initiate_return", {"order_id": order_id, "reason": reason}, output,
                           (time.monotonic() - t0) * 1000)
        return output

    # Cannot return Processing orders
    if order["status"] == "Processing":
        output = {
            "error": "ORDER_NOT_ELIGIBLE",
            "message": (
                f"Order {order_id} is currently being processed and cannot be returned yet. "
                "Please contact us after the order ships to initiate a return."
            ),
        }
        session_logger.log("initiate_return", {"order_id": order_id, "reason": reason}, output,
                           (time.monotonic() - t0) * 1000)
        return output

    # Create return record
    return_id = f"RTN-{random.randint(1000000, 9999999)}"
    _MOCK_RETURNS[return_id] = {
        "return_id": return_id,
        "order_id": order_id,
        "reason": reason,
        "created_at": datetime.utcnow().isoformat(),
        "status": "Initiated",
    }

    output = {
        "return_id": return_id,
        "status": "Initiated",
        "instructions": (
            f"Your return for order {order_id} has been initiated (Return ID: {return_id}). "
            "A prepaid return label has been emailed to the address on file. "
            "Pack the item(s) securely and drop off at any UPS location within 14 days. "
            "Refunds are processed within 5-7 business days after we receive the item."
        ),
        "label_url": f"https://returns.northstar.com/label/{return_id}",
        "eligible_refund": order["total"],
    }

    latency_ms = (time.monotonic() - t0) * 1000
    session_logger.log("initiate_return", {"order_id": order_id, "reason": reason}, output, latency_ms)
    return output


def apply_loyalty_credit(customer_id: str, amount: float, reason: str) -> dict:
    """
    Apply a loyalty credit to a customer's account.

    IMPORTANT: This tool must NEVER be called without explicit policy justification.
    The agent must cite the specific policy reason before calling this tool.
    Credits > $50 require manager approval (this is a hard system limit, not advisory).

    Business rules:
      - Credits <= $50: applied immediately, returns success
      - Credits > $50: not applied; returns approval_required=True with ticket ID
      - Customer must exist in the system

    In production: calls northstar-loyalty-service API, which writes to
    DynamoDB and triggers a notification to the customer.

    Args:
        customer_id: Customer account ID
        amount:      Credit amount in USD (positive)
        reason:      Policy-based justification for the credit

    Returns:
        {"success": bool, "new_balance": float, "approval_required": bool, ...}
    """
    t0 = time.monotonic()
    time.sleep(0.025)

    if amount <= 0:
        output = {
            "success": False,
            "error": "INVALID_AMOUNT",
            "message": "Credit amount must be positive.",
        }
        session_logger.log("apply_loyalty_credit",
                           {"customer_id": customer_id, "amount": amount, "reason": reason},
                           output, (time.monotonic() - t0) * 1000)
        return output

    customer = _MOCK_CUSTOMERS.get(customer_id)
    if customer is None:
        output = {
            "success": False,
            "error": "CUSTOMER_NOT_FOUND",
            "message": f"No customer found with ID {customer_id}.",
        }
        session_logger.log("apply_loyalty_credit",
                           {"customer_id": customer_id, "amount": amount, "reason": reason},
                           output, (time.monotonic() - t0) * 1000)
        return output

    # Hard limit: credits > $50 require manager approval
    if amount > 50.0:
        ticket_id = f"MGR-{random.randint(10000, 99999)}"
        output = {
            "success": False,
            "approval_required": True,
            "ticket_id": ticket_id,
            "message": (
                f"A loyalty credit of ${amount:.2f} exceeds the $50 self-service limit. "
                f"A manager approval request (Ticket {ticket_id}) has been submitted. "
                "The credit will be applied within 1 business day if approved."
            ),
        }
        logger.warning(
            "Credit of $%.2f for %s requires manager approval (reason: %s)",
            amount, customer_id, reason,
        )
        session_logger.log("apply_loyalty_credit",
                           {"customer_id": customer_id, "amount": amount, "reason": reason},
                           output, (time.monotonic() - t0) * 1000)
        return output

    # Apply credit
    current_balance = customer["loyalty_points"]
    # Convert dollar credit to points (100 points = $1)
    points_added = int(amount * 100)
    new_balance = current_balance + points_added
    _MOCK_CUSTOMERS[customer_id]["loyalty_points"] = new_balance

    output = {
        "success": True,
        "approval_required": False,
        "customer_id": customer_id,
        "amount_credited": amount,
        "points_added": points_added,
        "new_balance": new_balance,
        "reason_recorded": reason,
        "message": (
            f"A loyalty credit of ${amount:.2f} ({points_added} points) has been applied "
            f"to {customer.get('name', 'your')} account. "
            f"New balance: {new_balance} points."
        ),
    }

    latency_ms = (time.monotonic() - t0) * 1000
    session_logger.log("apply_loyalty_credit",
                       {"customer_id": customer_id, "amount": amount, "reason": reason},
                       output, latency_ms)
    return output


def escalate_to_human(
    customer_id: str,
    issue_summary: str,
    priority: str = "normal",
) -> dict:
    """
    Escalate the conversation to a human customer service agent.

    Required for:
      - Policy exceptions (anything outside documented policy)
      - Credits > $50
      - Customer expressed frustration or used abusive language
      - Complex multi-issue complaints
      - Any situation where the AI agent is uncertain

    Priority levels: "normal", "urgent"
      - normal: standard queue, estimated wait 5-15 minutes
  - urgent: priority queue, estimated wait 1-3 minutes

    In production: writes a ticket to Zendesk/ServiceNow and initiates
    a call-back queue entry.

    Args:
        customer_id:   Customer account ID
        issue_summary: Concise summary of the issue for the human agent
        priority:      "normal" or "urgent"

    Returns:
        {"ticket_id": str, "estimated_wait_minutes": int, "message": str}
    """
    t0 = time.monotonic()
    time.sleep(0.02)

    priority = priority.lower()
    if priority not in ("normal", "urgent"):
        priority = "normal"

    ticket_id = f"TKT-{random.randint(1000000, 9999999)}"
    wait_minutes = random.randint(1, 3) if priority == "urgent" else random.randint(5, 15)

    _MOCK_TICKETS[ticket_id] = {
        "ticket_id": ticket_id,
        "customer_id": customer_id,
        "issue_summary": issue_summary,
        "priority": priority,
        "created_at": datetime.utcnow().isoformat(),
        "status": "Queued",
    }

    output = {
        "ticket_id": ticket_id,
        "priority": priority,
        "estimated_wait_minutes": wait_minutes,
        "message": (
            f"I've connected you with a NorthStar customer service specialist "
            f"(Ticket: {ticket_id}). "
            f"Estimated wait time: {wait_minutes} minutes. "
            "You'll receive a callback at the number on file, or you can continue "
            "waiting in this chat. Thank you for your patience."
        ),
    }

    logger.info(
        "Escalated customer %s to human (priority=%s, ticket=%s): %s",
        customer_id, priority, ticket_id, issue_summary[:80],
    )

    latency_ms = (time.monotonic() - t0) * 1000
    session_logger.log("escalate_to_human",
                       {"customer_id": customer_id, "priority": priority},
                       output, latency_ms)
    return output
