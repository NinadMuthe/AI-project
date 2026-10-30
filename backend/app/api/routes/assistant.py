# backend/app/api/routes/assistant.py
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from ..dependencies import get_db
from ..security import get_current_user_id
from ...core.config import settings
from ...services.context_builder import build_financial_context

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/assistant", tags=["assistant"])


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)


class ChatResponse(BaseModel):
    response: str
    context_used: dict


SYSTEM_PROMPT = """You are FinPulse AI, a professional, empathetic, and highly practical personal financial advisor.
You are given the user's authentic financial context directly from their database.

STRICT OPERATIONAL RULES:
1. ONLY reference the data provided in the financial context below. NEVER invent or hallucinate financial numbers.
2. If data is missing or incomplete, clearly state that the specific data is not yet recorded.
3. Treat all forecasts and balance projections as estimates and predictions, NEVER as guarantees.
4. When discussing unusual transactions or anomalies, NEVER use the word 'fraud' or accuse anyone of fraud. Refer to them strictly as 'suspicious' or 'unusual' transactions flagged for review.
5. Provide actionable, concise, and clear suggestions to help the user manage expenses, improve savings, and prepare for potential balance shortages.
6. Format your answer with clean Markdown (bullet points, bold highlights) for ease of reading.
"""


@router.post("/chat", response_model=ChatResponse)
async def chat_with_assistant(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    # 1. Fetch user financial context from real DB
    context = await build_financial_context(db, user_id)

    # 2. Check if API key is present
    api_key_str = settings.GOOGLE_API_KEY.get_secret_value() if settings.GOOGLE_API_KEY else ""
    if not api_key_str or "placeholder" in api_key_str.lower():
        # Friendly graceful fallback if key is not configured
        fallback_msg = (
            f"**FinPulse Advisor Summary (Offline Mode)**:\n\n"
            f"- **Current Balance:** ${context['balance']:,.2f}\n"
            f"- **This Month's Spending:** ${context['current_month_expense']:,.2f} against ${context['current_month_income']:,.2f} income\n"
            f"- **Monthly Net Savings:** ${context['monthly_savings']:,.2f}\n"
            f"- **Top Spending Category:** {context['top_categories'][0]['category'] if context['top_categories'] else 'N/A'}\n"
            f"- **Unreviewed Suspicious Transactions:** {context['anomaly_count']} item(s)\n\n"
            "*(Google Gemini API key is currently in placeholder mode. Real-time conversational generation requires an active Gemini API key in configuration.)*"
        )
        return ChatResponse(response=fallback_msg, context_used=context)

    # 3. Format context prompt
    context_str = (
        f"USER FINANCIAL CONTEXT:\n"
        f"- Current Ledger Balance: ${context['balance']:.2f}\n"
        f"- Current Month Income: ${context['current_month_income']:.2f}\n"
        f"- Current Month Expenses: ${context['current_month_expense']:.2f}\n"
        f"- Monthly Net Savings: ${context['monthly_savings']:.2f}\n"
        f"- Top Expense Categories (past 90 days): {context['top_categories']}\n"
        f"- Recent Transactions: {context['recent_transactions']}\n"
        f"- Unreviewed Suspicious Items: {context['unreviewed_anomalies']}\n"
    )

    try:
        llm = ChatGoogleGenerativeAI(
            model=settings.GEMINI_MODEL,
            google_api_key=api_key_str,
            temperature=0.2,
        )
        messages = [
            SystemMessage(content=SYSTEM_PROMPT + "\n\n" + context_str),
            HumanMessage(content=request.message),
        ]
        result = await llm.ainvoke(messages)
        content_text = result.content if isinstance(result.content, str) else str(result.content)
        return ChatResponse(response=content_text, context_used=context)
    except Exception as e:
        logger.error("Gemini Assistant error (no secrets logged): %s", type(e).__name__)
        # Safe friendly fallback without crashing
        fallback = (
            f"I encountered a temporary service issue communicating with the AI service: {type(e).__name__}.\n\n"
            f"Here is your latest verified financial snapshot from your ledger:\n"
            f"- **Balance:** ${context['balance']:.2f}\n"
            f"- **Current Month Expenses:** ${context['current_month_expense']:.2f}\n"
            f"- **Monthly Savings:** ${context['monthly_savings']:.2f}\n"
            f"- **Unusual Items:** {context['anomaly_count']} pending review."
        )
        return ChatResponse(response=fallback, context_used=context)
