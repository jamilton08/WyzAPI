
    
from decouple import config
import json
import time
import backoff
from tqdm.auto import tqdm
import openai
try:
    from openai.error import RateLimitError, APIError
except ImportError:
    # older/newer layouts may put them directly on openai
    RateLimitError = getattr(openai, "RateLimitError", Exception)
    APIError      = getattr(openai, "APIError", Exception)

openai.api_key = config("OPEN_AI_API_KEY")


@backoff.on_exception(backoff.expo, (RateLimitError, APIError), max_time=300)
def generate_single_dsl(prompt: str) -> dict:
    model_id = "gpt-4.5-preview-2025-02-27"   # chat‐only model

    template = r"""
Produce a single JSON object with exactly these keys:
  "prompt": "{prompt}",
  "dsl": {{
    "objects": [
      {{
        "id": "<part>-<unique-id>",
        "name": "<descriptive name>",
        "type": "polygon",
        "points": [
          [x1,y1],[x2,y2],…,[xM,yM]
        ],  # M between 20 and 100 coordinate pairs
        "fill": "<css-color>",
        "stroke": "<css-color>",
        "strokeWidth": <number>,
        "fillOpacity": <0–1>,
        "angle": <number>
      }},
      …  # exactly 5–15 such polygon objects
    ]
  }}
Return only the raw JSON—no markdown, no commentary.
"""
    user_msg = template.format(prompt=prompt)

    # Use the chat endpoint for GPT-4.5-preview
    resp = openai.chat.completions.create(
        model=model_id,
        messages=[{"role": "user", "content": user_msg}],
        temperature=0.7,
        max_tokens=4000,
    )

    # Extract the JSON string
    content = resp.choices[0].message.content
    return json.loads(content)




@backoff.on_exception(backoff.expo, (RateLimitError, APIError), max_time=300)
def generate_question_batch(problem_type: str, topic: str, details: str, n: int = 10) -> list[dict]:
    """
    Calls the OpenAI API to generate `n` question rows in JSON format.
    """
    prompt = prompt = f"""
Generate a JSON array of {n} objects, each representing a CSV row with these columns:
- question_id: integer (start at 1, incrementing)
- subject: "Math"
- topic: "{topic}"
- subtopic: a subtopic related to "{topic}" (use "{details}" as guidance)
- grade_level: integer between 1 and 12
- question_type: "{problem_type}"
- question_text: a concise question matching the type/topic
- difficulty: one of ["Easy","Medium","Hard"]
- rubric_part_1 through rubric_part_5: five concise rubric criteria
- jsx_code: **MANDATORY**. Provide a fully working JSXGraph snippet that _visualizes_ the question.  
    * For **Geometry**: draw the appropriate points, lines, or polygon.  
    * For **Statistics**: render a simple bar or line chart.  
    * For **Fractions**: show a number-line diagram.  
    * For **Algebra**: draw coordinate axes with labeled points or lines.  
    If the question doesn’t naturally graph, still include a minimal placeholder (e.g. an empty coordinate system) so this field is never empty.  
    Each `jsx_code` must start with:
    ```js
    const board = JXG.JSXGraph.initBoard('jsxbox',{{boundingbox:[xMin,yMin,xMax,yMax],axis:true}});
    ```
- mathjax: LaTeX version of question_text wrapped in $$

Return **only** the raw JSON array of objects—no commentary, no markdown.
"""

    resp = openai.chat.completions.create(
        model="gpt-3.5-turbo-16k",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )
    return json.loads(resp.choices[0].message.content)




#

@backoff.on_exception(
    backoff.expo,
    (RateLimitError, APIError),
    max_time=300
)
def generate_rubric_batch(user_text: str) -> list[dict]:
    import re
    """
    Calls the OpenAI API to generate or refine a grading rubric. Each rubric entry now has:
      - "part": str
      - "weight": int (0–100)
      - "levels": an OBJECT mapping four varied level names to one-sentence descriptions.

    GPT will choose from multiple naming schemes per criterion, such as:
     • "Beginner", "Developing", "Proficient", "Advanced"
     • "Level A", "Level B", "Level C", "Level D"
     • "Poor", "Fair", "Good", "Excellent"
     • or any other four-tier naming it deems appropriate.

    If the user's prompt explicitly requests different names or a different number of levels, follow that. 
    Strip out any ```json…``` fences before parsing.
    """
    system_message = {
        "role": "system",
        "content": (
            "You are an assistant that creates or refines grading rubrics. "
            "Each rubric entry must be a JSON object with exactly three keys:\n\n"
            "  • \"part\" (string describing one criterion),\n"
            "  • \"weight\" (integer between 0 and 100),\n"
            "  • \"levels\" (an OBJECT whose keys are descriptive level names, and whose values "
            "    are one-sentence descriptions of what achieving that level looks like).\n\n"
            "By default, produce exactly FOUR levels per criterion. For each criterion, "
            "mix up your naming scheme: some criteria might use [\"Beginner\",\"Developing\",\"Proficient\",\"Advanced\"], "
            "others might use [\"Level A\",\"Level B\",\"Level C\",\"Level D\"], others [\"Poor\",\"Fair\",\"Good\",\"Excellent\"], "
            "or any other sensible four-tier set. Make sure each level’s value is a brief sentence.\n\n"
            "If the user explicitly specifies custom level names or a different count, follow those instructions. "
            "All weights across criteria must sum to exactly 100. Return ONLY the raw JSON array—no extra commentary or markdown."
        )
    }

    user_message = {
        "role": "user",
        "content": (
            f"User prompt (rubric request or existing rubric):\n{user_text}\n\n"
            "If this is an existing rubric in text form, refine its weights so they sum to 100 and ensure each criterion includes a "
            "\"levels\" object with four varied level names and descriptions.  \n"
            "If this is a request to create a new rubric, generate appropriate criteria, assign weights, and for each criterion provide four "
            "distinct level names (rotating among schemes like \"Beginner/Developing/Proficient/Advanced\", \"Level A–D\", \"Poor–Excellent\", etc.) "
            "with one-sentence descriptions.  \n\n"
            "Example for a single criterion in JSON:\n"
            "{\n"
            "  \"part\": \"Clarity of Writing\",\n"
            "  \"weight\": 25,\n"
            "  \"levels\": {\n"
            "    \"Beginner\": \"Sentences are frequently unclear or contain major grammatical errors.\",\n"
            "    \"Developing\": \"Most ideas are understandable, but errors sometimes obscure meaning.\",\n"
            "    \"Proficient\": \"Writing is generally clear with only minor errors and logical flow.\",\n"
            "    \"Advanced\": \"Writing is exceptionally clear, concise, and error-free, with outstanding organization.\"\n"
            "  }\n"
            "}\n\n"
            "Return a JSON array of objects exactly in that format (with one object per criterion)."
        )
    }

    response = openai.chat.completions.create(
        model="gpt-4-turbo-preview",
        messages=[system_message, user_message],
        temperature=0.7,
        max_tokens=700,
    )

    raw = response.choices[0].message.content.strip()

    # ─── Remove any ```json … ``` fences ──────────────────────────────────
    fenced = re.match(r"^```(?:json)?\s*([\s\S]+?)\s*```$", raw)
    if fenced:
        raw = fenced.group(1).strip()
    # ──────────────────────────────────────────────────────────────────────

    rubric_list = json.loads(raw)
    return rubric_list
