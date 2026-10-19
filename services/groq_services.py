import os
from groq import AsyncGroq

SYSTEM_PROMPT_BUILD = """
You are CodeForge v2, an elite senior full-stack engineer like Replit Agent + Lovable + Bolt.

TASK: Given a user prompt, generate a COMPLETE, WORKING, SINGLE-FILE HTML APP.

CRITICAL RULES:
1. Output ONLY raw HTML. Start with <!DOCTYPE html> and end with </html>. NO markdown, NO ```, NO explanation.
2. Must be fully functional, interactive, production-quality. Not a mockup. Real working features.
3. All CSS in <style>, all JS in <script>. You may use Tailwind CDN: <script src="https://cdn.tailwindcss.com"></script> + Google Fonts.
4. UI: Modern, beautiful, SaaS-level. Gradients, glassmorphism, rounded-2xl, shadows, animations, Inter font. Mobile responsive.
5. LOGIC: 
   - Todo app -> add/delete/complete/filter + localStorage persistence + categories
   - School website -> full nav, hero, courses, admissions form with validation, footer
   - Dashboard -> interactive charts (use Chart.js CDN https://cdn.jsdelivr.net/npm/chart.js if needed), stats, filters
   - Food delivery -> menu, cart with quantity, checkout modal, search
6. Make it feel like a real product worth paying for.
7. Keep under 8000 tokens but impressive.
"""

SYSTEM_PROMPT_EDIT = """
You are CodeForge EDIT MODE. Given existing HTML code + edit request, return COMPLETE UPDATED HTML.

RULES:
1. Output ONLY raw HTML file. No markdown.
2. Preserve all existing functionality unless user explicitly wants removal.
3. Apply edit precisely. Examples: "add dark mode" -> add toggle + CSS variables + localStorage. "add Stripe" -> add button + modal.
4. Keep single file, inline CSS/JS.
5. Ensure result is still fully working, no broken tags.
"""

MODEL = "llama-3.3-70b-versatile"

def get_client():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not set. Add it to Vercel Environment Variables.")
    return AsyncGroq(api_key=api_key)

async def generate_app_code(user_prompt: str) -> str:
    client = get_client()
    completion = await client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT_BUILD},
            {"role": "user", "content": f"Build this app: {user_prompt}\n\nReturn ONLY full HTML file, no markdown."}
        ],
        temperature=0.75,
        max_tokens=8000,
        top_p=0.92,
    )
    return clean_code(completion.choices[0].message.content)

async def edit_app_code(existing_code: str, edit_prompt: str) -> str:
    client = get_client()
    truncated = existing_code[:15000]
    completion = await client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT_EDIT},
            {"role": "user", "content": f"Existing code (truncated):\n{truncated}\n\nEdit request: {edit_prompt}\n\nReturn ONLY the full updated HTML file."}
        ],
        temperature=0.55,
        max_tokens=8000,
        top_p=0.9,
    )
    return clean_code(completion.choices[0].message.content)

def clean_code(code: str) -> str:
    code = code.strip()
    if "```" in code:
        if code.count("```") >= 2:
            parts = code.split("```")
            for p in parts:
                if "<!DOCTYPE" in p or "<html" in p:
                    code = p
                    break
            else:
                code = parts[1]
        code = code.strip()
        if code.lower().startswith("html"):
            code = code[4:].strip()
    return code.strip()
