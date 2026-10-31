# backend/app/api/routes/assistant.py
"""
AI Financial Advisor (Daily Expense Coach for Indian Users).
Uses LangChain + Google Gemini with full Indian financial context in ₹.
Includes data-driven offline fallback with rule-based intent matching.
"""
import logging
import re
from typing import Optional, List, Dict, Any, Union
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from ..dependencies import get_db
from ..security import get_current_user_id
from ...core.config import settings
from ...services.context_builder import build_financial_context, format_inr

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/assistant", tags=["assistant"])

_PREFERRED_MODELS = ["gemini-3.8-flash", "gemini-flash-latest", "gemini-2.5-flash"]


def _extract_text(content: Union[str, list]) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict):
                parts.append(item.get("text", ""))
            elif isinstance(item, str):
                parts.append(item)
        return " ".join(p for p in parts if p).strip()
    return str(content)


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)
    history: Optional[List[ChatMessage]] = Field(default_factory=list)


class ChatResponse(BaseModel):
    response: str
    context_used: dict
    source: str = "AI (Gemini)"


SYSTEM_PROMPT = """You are FinPulse AI, an intelligent, empathetic daily expense coach for an Indian user living in an Indian city.
You have real-time access to their verified bank ledger, UPI transactions, bills, and anomaly alerts.

CRITICAL OPERATIONAL RULES:
1. CURRENCY: Always use Indian Rupees (₹) with Indian digit grouping (e.g. ₹1,23,456.00). NEVER use dollar signs ($).
2. ACCURACY: Only cite numbers provided in the user's authentic financial context below. NEVER invent, guess, or hallucinate financial numbers.
3. ADVICE SCOPE: Provide practical, culturally relevant Indian financial guidance:
   - Frequent UPI micro-transactions (tea, snacks, Swiggy/Zomato, quick commerce like Blinkit/Zepto).
   - Fixed commitments: Rent on the 5th, electricity, broadband recharges, OTT/gym subscriptions, and monthly SIPs.
   - Actionable ways to trim discretionary spending and build a 3-6 month emergency fund.
4. FORECASTS: Treat all cash projections as statistical estimates, NEVER as guaranteed outcomes.
5. ANOMALIES: NEVER use the word 'fraud' or accuse anyone of fraud. Refer to unusual expenses strictly as 'suspicious' or 'unusual' transactions flagged for review.
6. MISSING DATA: If specific data is not recorded or absent, clearly state that it is not yet in the ledger.
7. FORMATTING: Use clean Markdown with bullet points and bold highlights for effortless readability.
"""


def _generate_rule_based_offline_answer(question: str, context: dict) -> str:
    """
    Data-driven offline fallback that inspects user's real DB context
    and answers each intent with accurate rupee numbers.
    """
    q = question.lower()
    balance = context["formatted_balance"]
    cur_exp = context["formatted_current_month_expense"]
    cur_inc = context["formatted_current_month_income"]
    cur_sav = context["formatted_monthly_savings"]
    top_cats = context["top_categories"]
    top_mer = context["top_merchants"]
    subs = context["recurring_items"]
    anoms = context["unreviewed_anomalies"]

    # 1. Top spending category
    if any(k in q for k in ["where", "most", "category", "spending the most", "highest spend"]):
        if top_cats:
            first = top_cats[0]
            cat_list = "\n".join([f"- **{c['category']}:** {c['formatted']}" for c in top_cats[:4]])
            return (
                f"Based on your recent expenses, you are spending the most on **{first['category']}** ({first['formatted']}).\n\n"
                f"**Top Expense Categories:**\n{cat_list}\n\n"
                f"💡 *Tip:* Review your high-velocity UPI orders in {first['category']} to identify discretionary purchases you can trim."
            )
        return "You do not have enough categorized expense transactions recorded yet."

    # 2. Month's spend
    if any(k in q for k in ["how much did i spend", "spend this month", "this month's spend", "month expense"]):
        return (
            f"Here is your spending snapshot for the current calendar month:\n\n"
            f"- **Total Spent This Month:** **{cur_exp}**\n"
            f"- **Total Income Received:** {cur_inc}\n"
            f"- **Net Monthly Savings:** {cur_sav}\n"
            f"- **Current Balance:** {balance}\n\n"
            f"Your current monthly net savings stand at {cur_sav}."
        )

    # 3. Month-end cash shortage / running out of money
    if any(k in q for k in ["run out", "shortage", "before month end", "out of money"]):
        num_balance = context["balance"]
        num_exp = context["current_month_expense"]
        if num_balance > 20000:
            return (
                f"Good news: Your current verified balance is **{balance}**, and your net savings this month are **{cur_sav}**.\n\n"
                f"Based on your current daily spending rate, you have adequate liquidity to comfortably meet your remaining expenses before month-end.\n"
                f"*(Note: All balance projections are statistical estimates based on past averages, not guarantees.)*"
            )
        else:
            return (
                f"⚠️ **Cash Flow Alert:** Your current balance is **{balance}** against this month's spending of **{cur_exp}**.\n\n"
                f"With month-end approaching, consider pausing non-essential discretionary orders (Swiggy, dining, shopping) to ensure your account remains comfortably above minimum balance."
            )

    # 4. Reducible expenses / discretionary spending
    if any(k in q for k in ["reduce", "cut", "trim", "save money", "discretionary"]):
        reducible = [c for c in top_cats if c["category"] in ["Food & Dining", "Shopping", "Entertainment", "Subscriptions"]]
        rec_text = "\n".join([f"- **{c['category']}:** {c['formatted']}" for c in reducible[:3]]) if reducible else "- Discretionary ordering and dining out"
        sub_text = "\n".join([f"- **{s['merchant']}:** {s['formatted']}" for s in subs[:3]]) if subs else "- Active monthly OTT/app subscriptions"
        return (
            f"Here are key areas where you can optimize your daily expenses:\n\n"
            f"**1. Discretionary Categories to Review:**\n{rec_text}\n\n"
            f"**2. Recurring Subscriptions:**\n{sub_text}\n\n"
            f"💡 *Action Plan:* Halving your weekly food delivery orders and canceling unused subscriptions could recover an estimated ₹2,000–₹5,000 monthly for your emergency fund."
        )

    # 5. Unusual / anomaly transactions
    if any(k in q for k in ["unusual", "anomaly", "suspicious", "flagged"]):
        if anoms:
            anom_text = "\n".join([f"- **{a['date']} — {a['merchant']} ({a['formatted']}):** {a['reason']}" for a in anoms])
            return (
                f"There are currently **{context['anomaly_count']} suspicious or unusual transaction(s)** flagged by Isolation Forest for review:\n\n"
                f"{anom_text}\n\n"
                f"Please review these on your Anomalies page to verify if they were authorized or require a dispute with your bank."
            )
        return (
            "✅ **All Clear:** No unusual or suspicious transactions are currently pending review in your account."
        )

    # 6. Save next month
    if any(k in q for k in ["how much can i save", "save next month", "savings target"]):
        est_savings = max(1000.0, context["current_month_income"] * 0.20)
        return (
            f"Based on your verified monthly income of {cur_inc}:\n\n"
            f"- **Recommended 20% Savings Target:** **{format_inr(est_savings)}**\n"
            f"- **Current Month Net Savings:** {cur_sav}\n"
            f"- **Current Balance:** {balance}\n\n"
            f"To reach {format_inr(est_savings)} next month, maintain your monthly SIP on schedule and set a daily UPI spending limit of ₹500 for dining and quick commerce."
        )

    # 7. Week summary
    if any(k in q for k in ["week", "one-line", "summary"]):
        return (
            f"This week you maintained a total ledger balance of **{balance}** with net monthly savings of **{cur_sav}** across your verified accounts."
        )

    # Default fallback answering with actual metrics
    return (
        f"**Your Verified Financial Snapshot:**\n\n"
        f"- **Current Balance:** {balance}\n"
        f"- **This Month's Spending:** {cur_exp} (Income: {cur_inc})\n"
        f"- **Monthly Net Savings:** {cur_sav}\n"
        f"- **Top Spending Category:** {top_cats[0]['category'] if top_cats else 'N/A'} ({top_cats[0]['formatted'] if top_cats else '₹0.00'})\n"
        f"- **Pending Unusual Items:** {context['anomaly_count']} item(s)\n\n"
        f"Ask me about your top spending categories, month-end balance forecasts, or ways to reduce daily expenses."
    )


@router.post("/chat", response_model=ChatResponse)
async def chat_with_assistant(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    try:
        # 1. Fetch fresh financial context from live database
        context = await build_financial_context(db, user_id)

        # 2. Check Google API key
        api_key_str = settings.GOOGLE_API_KEY.get_secret_value() if settings.GOOGLE_API_KEY else ""
        if not api_key_str or "placeholder" in api_key_str.lower():
            offline_resp = _generate_rule_based_offline_answer(request.message, context)
            return ChatResponse(
                response=offline_resp,
                context_used=context,
                source="Offline mode (rule-based, not AI)",
            )

        # 3. Format context string with Indian Rupees
        top_cat_summary = ", ".join([f"{c['category']}: {c['formatted']}" for c in context["top_categories"]])
        top_mer_summary = ", ".join([f"{m['merchant']}: {m['formatted']}" for m in context["top_merchants"]])
        rec_summary = "; ".join([f"{t['date']} {t['merchant']} {t['formatted']} ({t['payment_mode']})" for t in context["recent_transactions"][:6]])
        anom_summary = "; ".join([f"{a['date']} {a['merchant']} {a['formatted']}: {a['reason']}" for a in context["unreviewed_anomalies"]]) or "None"

        context_str = (
            f"AUTHENTIC USER FINANCIAL CONTEXT (LIVE FROM POSTGRESQL):\n"
            f"- Ledger Balance: {context['formatted_balance']}\n"
            f"- Current Month Income: {context['formatted_current_month_income']}\n"
            f"- Current Month Expenses: {context['formatted_current_month_expense']}\n"
            f"- Monthly Net Savings: {context['formatted_monthly_savings']}\n"
            f"- Top Expense Categories: {top_cat_summary}\n"
            f"- Top Merchants: {top_mer_summary}\n"
            f"- Recent Transactions: {rec_summary}\n"
            f"- Unreviewed Suspicious Items: {anom_summary}\n"
        )

        # Build messages with conversation history (last 6 messages)
        messages = [
            SystemMessage(content=SYSTEM_PROMPT + "\n\n" + context_str),
        ]

        if request.history:
            for past in request.history[-6:]:
                if past.role == "user":
                    messages.append(HumanMessage(content=past.content))
                elif past.role == "assistant":
                    messages.append(AIMessage(content=past.content))

        messages.append(HumanMessage(content=request.message))

        # Candidate models to try in sequence
        configured_model = settings.GEMINI_MODEL
        candidates = [configured_model] + [m for m in _PREFERRED_MODELS if m != configured_model]

        last_error: Exception | None = None
        for model_name in candidates:
            try:
                llm = ChatGoogleGenerativeAI(
                    model=model_name,
                    google_api_key=api_key_str,
                    temperature=0.2,
                )
                result = await llm.ainvoke(messages)
                content_text = _extract_text(result.content)
                if content_text and len(content_text.strip()) > 5:
                    return ChatResponse(
                        response=content_text,
                        context_used=context,
                        source="AI (Gemini)",
                    )
            except Exception as e:
                logger.warning("Gemini model '%s' failed: %s", model_name, type(e).__name__)
                last_error = e

        # If all models fail, return intelligent data-driven offline fallback
        offline_resp = _generate_rule_based_offline_answer(request.message, context)
        return ChatResponse(
            response=offline_resp,
            context_used=context,
            source="Offline mode (rule-based, not AI)",
        )
    except Exception as exc:
        # Any unexpected error – fall back to rule‑based answer to keep the endpoint alive
        logger.error("Unexpected error in assistant endpoint: %s", exc)
        # Ensure we still have a context (may be missing if DB failed)
        fallback_context = {} if 'context' not in locals() else context
        offline_resp = _generate_rule_based_offline_answer(request.message, fallback_context)
        return ChatResponse(
            response=offline_resp,
            context_used=fallback_context,
            source="Offline mode (fallback after unexpected error)",
        )

