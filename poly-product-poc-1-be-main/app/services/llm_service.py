from app.core.groq_client import get_groq_client
from app.core.config import settings


class LLMService:
    @staticmethod
    def synthesize_answer(query: str, faqs: list[dict], learnings: str = "") -> str:
        context = "\n\n".join(f"Q: {f['question']}\nA: {f['answer']}" for f in faqs)

        # Learnings are supplementary context from past interactions. When empty
        # (default / integration disabled) the prompt is unchanged from before.
        learnings_section = f"\n\n{learnings.strip()}\n" if learnings.strip() else ""

        prompt = f"""
        You are an AI assistant designed to answer user questions using a provided FAQ knowledge base.

        User query:
        {query}

        Relevant FAQ context:
        {context}
        {learnings_section}
        Answer the query using the content above. The FAQ context is authoritative; treat any learnings as supplementary guidance from past interactions. Some learnings may state how the user wants answers formatted (for example as a table or bullet points) — follow those preferences. If answer is present indirectly, infer and answer.
        Be concise, clear and helpful. Do not mention that you're using FAQs. It must be in the form of markdown. Don't use markdown decorators.
        """

        client = get_groq_client()
        if client is None:
            return "The assistant is not configured (missing GROQ_API_KEY)."

        resp = client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )

        return resp.choices[0].message.content.strip()
