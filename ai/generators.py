
    
from decouple import config
import json
import time
import backoff
from tqdm.auto import tqdm
import openai
import re
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


@backoff.on_exception(
    backoff.expo,
    (RateLimitError, APIError),
    max_time=300
)
def generate_assignment_batch(user_text: str) -> list[dict]:
    """
    Generate a nested fileStructure JSON tree for an assignment.
    If the response is truncated, automatically ask to continue.
    Uses openai.chat.completions.create.
    """
    system_message = {
        "role": "system",
        "content": (
            "You are AssignmentBuilderGPT. When the user says:\n"
            "  “Generate a [assignmentType] assignment on [Topic]”,\n"
            "you must return ONLY this JSON shape:\n\n"
            "{\n"
            "  \"assignment\": {\n"
            "    \"fileStructure\": [ /* nested tree of files & folders */ ]\n"
            "  }\n"
            "}\n\n"
            "Rules for fileStructure:\n"
            "• Each node = { name: string, type: \"folder\"|\"file\" }.\n"
            "• Folders include children: [ … ].\n"
            "• Files include content: string.\n\n"
            "You may include any combination of these editor templates—only those that fit:\n"
            "  – instructions.md (Markdown)\n"
            "  – .txt files for documents\n"
            "  – quiz.json for quizzes\n"
            "  – shapes.json for shape data\n"
            "  – code/ folder with index.html, styles.css, script.js\n\n"
            "Variation allowed. Do NOT wrap in markdown fences or add extra keys/commentary."
        )
    }
    user_message = {"role": "user", "content": user_text}

    # first shot
    resp = openai.chat.completions.create(
        model="gpt-4-turbo-preview",
        messages=[system_message, user_message],
        temperature=0.7,
        max_tokens=1500,
    )

    choice = resp.choices[0]
    text = choice.message.content

    # if truncated, ask to continue
    if choice.finish_reason == "length":
        cont = openai.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                system_message,
                user_message,
                {"role": "assistant", "content": text},
                {"role": "user", "content": "Continue the JSON from where you left off, output ONLY JSON."}
            ],
            temperature=0.7,
            max_tokens=1500,
        )
        text += cont.choices[0].message.content

    # strip any ```json…``` fences
    text = text.strip()
    fenced = re.match(r"^```(?:json)?\s*([\s\S]+?)\s*```$", text)
    if fenced:
        text = fenced.group(1).strip()

    data = json.loads(text)
    return data["assignment"]["fileStructure"]

@backoff.on_exception(
    backoff.expo,
    (RateLimitError, APIError),
    max_time=300
)
def generate_lessonplan_batch(user_text: str) -> dict:
    """
    Calls the OpenAI API to generate a full lesson plan JSON object.
    The returned dict has exactly one key "lessonPlan" whose value is an object containing:
      - title: str
      - standards: list[str]
      - timeBreakdown: list[ dict(activity: str, duration: str) ]
      - objectives: list[str]
      - materials: list[str]
      - activities: list[ dict(step: int, description: str) ]
      - modifications: list[str]
      - closure: str

    If the user does not specify a state or standards type, the assistant
    will choose random relevant standards (e.g., Common Core, NGSS). Always
    include a time breakdown and possible modifications. Strips out any
    ```json…``` fences before parsing.
    """
    system_message = {
        "role": "system",
        "content": (
            "You are LessonPlanBuilderGPT. When the user says:\n"
            "  “Generate a [assignmentType] lesson plan on [Topic]”,\n"
            "you must return ONLY this JSON shape:\n\n"
            "{\n"
            "  \"lessonPlan\": {\n"
            "    \"title\": string,\n"
            "    \"standards\": [ string, ... ],\n"
            "    \"timeBreakdown\": [ { \"activity\": string, \"duration\": string }, ... ],\n"
            "    \"objectives\": [ string, ... ],\n"
            "    \"materials\": [ string, ... ],\n"
            "    \"activities\": [ { \"step\": int, \"description\": string }, ... ],\n"
            "    \"modifications\": [ string, ... ],\n"
            "    \"closure\": string\n"
            "  }\n"
            "}\n\n"
            "Rules:\n"
            "• If the user does NOT specify a state or standards type, pick a set of "
            "random but appropriate standards (e.g., Common Core Math, NGSS). Include at least three.\n"
            "• Always include a detailed timeBreakdown (activity names + durations).\n"
            "• Always include possible modifications for diverse learners.\n"
            "• Do NOT wrap in markdown fences or add any extra keys or commentary. "
            "Output exactly the JSON above."
        )
    }



    user_message = {
        "role": "user",
        "content": user_text
    }
    response = openai.chat.completions.create(
        model="gpt-4-turbo-preview",
        messages=[system_message, user_message],
        temperature=0.7,
        max_tokens=1000
    )


    raw = response.choices[0].message.content.strip()

    # ─── Remove any ```json … ``` fences ────────────────────────────────
    fenced = re.match(r"^```(?:json)?\s*([\s\S]+?)\s*```$", raw)
    if fenced:
        raw = fenced.group(1).strip()
    # ─────────────────────────────────────────────────────────────────────

    result = json.loads(raw)
    return result["lessonPlan"]

# api/utils/grader.py


def extract_file(fs, filename):
    """Recursively find a file named `filename` in the file-structure dict."""
    if isinstance(fs, dict):
        if fs.get("name") == filename and fs.get("type") == "file":
            return fs.get("content", "")
        for child in fs.get("children", []):
            found = extract_file(child, filename)
            if found is not None:
                return found
    elif isinstance(fs, list):
        for item in fs:
            found = extract_file(item, filename)
            if found is not None:
                return found
    return None

def flatten_files(fs, parent=""):
    """Flatten all files except rubric.md and assignment.md into a list."""
    files = []
    if isinstance(fs, dict):
        name = fs.get("name", "")
        path = f"{parent}/{name}" if parent else name
        if fs.get("type") == "file" and name not in ("rubric.md", "assignment.md"):
            files.append({"path": path, "content": fs.get("content", "")})
        for child in fs.get("children", []):
            files.extend(flatten_files(child, path))
    elif isinstance(fs, list):
        for item in fs:
            files.extend(flatten_files(item, parent))
    return files

def build_grade_prompt(file_structure):
    """
    Given the file_structure dict, return a single string prompt
    to send into OpenAI for grading.
    """
    rubric_md     = extract_file(file_structure, "rubric.md")     or ""
    assignment_md = extract_file(file_structure, "assignment.md") or ""
    other_files   = flatten_files(file_structure)

    prompt_sections = [
        "You are an expert grader.",
        "",
        "Here is the rubric (rubric.md):",
        rubric_md,
        "",
        "Here is the assignment description (assignment.md):",
        assignment_md,
        "",
        "Evaluate the student submission in these files:",
    ]

    for f in other_files:
        prompt_sections.append(f"---\nFile: {f['path']}\n{f['content']}")

    prompt_sections.append(
        """
Please return a JSON object with two keys:
1. "score": an integer 0–100 for the overall grade.
2. "suggestions": an array of objects { "text": "...", "points": N } 
   where each suggestion would improve the score by approximately N points.
"""
    )

    # join with new lines
    return "\n".join(prompt_sections)




@backoff.on_exception(backoff.expo, (RateLimitError, APIError), max_time=300)
def generate_grade_from_files(file_structure: dict) -> dict:
    """
    Given the nested file_structure dict, build a grading prompt,
    send to OpenAI, and return a dict with keys:
      - score: int 0–100
      - suggestions: list of { text: str, points: int }
    """
    # 1) build the prompt text
    prompt = build_grade_prompt(file_structure)

    # 2) call OpenAI
    resp = openai.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that grades student submissions."},
            {"role": "user",   "content": prompt},
        ],
        temperature=0.0,
    )
    raw = resp.choices[0].message.content.strip()

    # 3) strip any ```json …``` fences
    fenced = re.match(r"^```(?:json)?\s*([\s\S]+?)\s*```$", raw)
    if fenced:
        raw = fenced.group(1).strip()

    # 4) parse and return
    return json.loads(raw)