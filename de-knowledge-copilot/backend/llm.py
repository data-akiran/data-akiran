import os
from groq import Groq
from typing import List

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MODEL = "llama-3.1-8b-instant"

client = Groq(api_key=GROQ_API_KEY)


def generate_answer(question: str, context_chunks: List[str]) -> str:
    context = "\n\n---\n\n".join(context_chunks)

    prompt = f"""You are a Data Engineering Knowledge Copilot. Answer the question based ONLY on the provided context.
If the context doesn't contain enough information, say so clearly.
Be concise, technical, and accurate.

Context:
{context}

Question: {question}

Answer:"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You are a helpful data engineering assistant. Answer only from the provided context."},
            {"role": "user", "content": prompt}
        ],
        temperature=0,
        max_tokens=1024
    )

    return response.choices[0].message.content.strip()