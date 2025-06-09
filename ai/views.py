# api/views.py
import json
import re
from pathlib import Path
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
import torch
from django.views.decorators.http import require_POST
import random
from .models import PromptDSL, GeneratedQuestion, RubricRequest
from .generators import generate_single_dsl, generate_question_batch, generate_rubric_batch



# 1) locate & load model
HERE      = Path(__file__).resolve().parent
MODEL_DIR = HERE / "shapes_model"
if not MODEL_DIR.exists():
    raise RuntimeError(f"Model folder not found at {MODEL_DIR}")

TORCH_DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
HF_DEVICE    = 0 if torch.cuda.is_available() else -1

tokenizer = AutoTokenizer.from_pretrained(str(MODEL_DIR))
model     = AutoModelForSeq2SeqLM.from_pretrained(str(MODEL_DIR)).to(TORCH_DEVICE)
generator = pipeline(
    "text2text-generation",
    model=model,
    tokenizer=tokenizer,
    device=TORCH_DEVICE
)




@csrf_exempt
def prompt_to_dsl(request):
    # handle CORS preflight
    if request.method == "OPTIONS":
        resp = HttpResponse()
        resp["Access-Control-Allow-Origin"]  = "*"
        resp["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        resp["Access-Control-Allow-Headers"] = "Content-Type"
        return resp

    if request.method != "POST":
        return HttpResponseBadRequest("Use POST")

    # parse incoming JSON
    try:
        payload = json.loads(request.body)
        prompt  = payload["prompt"]
    except (json.JSONDecodeError, KeyError):
        return HttpResponseBadRequest('JSON must be {"prompt":"..."}')

    # generate
    try:
        output =     out = generator(prompt, max_length=64, num_beams=4, early_stopping=True)
    except Exception as e:
        return JsonResponse(
            {"prompt": prompt, "error_detail": str(e)},
            headers={"Access-Control-Allow-Origin": "*"},
        )

    dsl_text = output[0].get("generated_text", "")
    print(f"DSL: {dsl_text}")

    # prepare response data
    resp_data = {"prompt": prompt, "raw": dsl_text}

    # first try direct JSON parse
    try:
        resp_data["dsl"] = json.loads(dsl_text)
    except json.JSONDecodeError:
        # fallback: normalize and retry
        normalized = normalize_dsl_text(dsl_text)
        try:
            resp_data["dsl"] = json.loads(normalized)
        except json.JSONDecodeError:
            # still bad — we'll just return raw
            pass

    resp = JsonResponse(resp_data, headers={"Access-Control-Allow-Origin": "*"})
    return resp




  # wherever you defined it

@csrf_exempt
@require_POST
def generate_dsl_view(request):
    try:
        payload = json.loads(request.body)
        prompt = payload.get("prompt", "").strip()
        if not prompt:
            return JsonResponse({"error": "No prompt provided"}, status=400)

        # 1) generate the DSL
        record = generate_single_dsl(prompt)  
        # record is a dict: {"prompt": prompt, "dsl": {…}}

        # 2) persist it
        saved = PromptDSL.objects.create(
            prompt=record["prompt"],
            dsl=record["dsl"]
        )

        print("Saved new DSL record:", record["dsl"])

        # 3) return it (including its new id/timestamp if you like)
        response_data = {
            "id": saved.pk,
            "prompt": saved.prompt,
            "dsl": saved.dsl,
            "created_at": saved.created_at.isoformat(),
        }
        return JsonResponse(response_data, status=201)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
    


 # your batch generator function

@csrf_exempt
@require_POST
def generate_questions_view(request):
    """
    Expects JSON POST with keys:
      - topic (str)
      - subtopic (str, optional)
      - grade_level (int)
      - difficulty (str: Easy|Medium|Hard)
      - question_type (str)
      - details (str, optional)

    Generates 10 questions via OpenAI, saves them, picks 3 at random,
    and returns those 3 as JSON.
    """
    try:
        payload = json.loads(request.body)
        topic        = payload['topic']
        subtopic     = payload.get('subtopic', '')
        grade_level  = payload['grade_level']
        difficulty   = payload['difficulty']
        question_type= payload['question_type']
        details      = payload.get('details', '')

        # Generate 10 question dicts
        batch = generate_question_batch(
            problem_type=question_type,
            topic=topic,
            details=details,
            n=10
        )

        saved_objs = []
        for item in batch:
            obj = GeneratedQuestion.objects.create(
                question_id   = item['question_id'],
                subject       = item['subject'],
                topic         = item['topic'],
                subtopic      = item['subtopic'],
                grade_level   = item['grade_level'],
                question_type = item['question_type'],
                question_text = item['question_text'],
                difficulty    = item['difficulty'],
                rubric_part_1 = item.get('rubric_part_1', ''),
                rubric_part_2 = item.get('rubric_part_2', ''),
                rubric_part_3 = item.get('rubric_part_3', ''),
                rubric_part_4 = item.get('rubric_part_4', ''),
                rubric_part_5 = item.get('rubric_part_5', ''),
                jsx_code      = item.get('jsx_code', ''),
                mathjax       = item.get('mathjax', '')
            )
            saved_objs.append(obj)

        # Pick 3 at random
        selected = random.sample(saved_objs, 3)
        response_data = []
        for obj in selected:
            response_data.append({
                'id': obj.pk,
                'question_id': obj.question_id,
                'subject': obj.subject,
                'topic': obj.topic,
                'subtopic': obj.subtopic,
                'grade_level': obj.grade_level,
                'question_type': obj.question_type,
                'question_text': obj.question_text,
                'difficulty': obj.difficulty,
                'rubric_part_1': obj.rubric_part_1,
                'rubric_part_2': obj.rubric_part_2,
                'rubric_part_3': obj.rubric_part_3,
                'rubric_part_4': obj.rubric_part_4,
                'rubric_part_5': obj.rubric_part_5,
                'jsx_code': obj.jsx_code,
                'mathjax': obj.mathjax,
                'created_at': obj.created_at.isoformat(),
            })

        return JsonResponse({'selected_questions': response_data}, status=201)

    except KeyError as e:
        return JsonResponse({'error': f'Missing parameter: {str(e)}'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    



@csrf_exempt  # In production, supply a CSRF token instead
def generate_rubric(request):
    
    """
    View at /api/rubric/ that:
     • Accepts POST JSON {"text": "..."}
     • Calls generate_rubric_batch(text)
     • Saves prompt + resulting JSON into RubricRequest
     • Returns the JSON array to the client
    """
    if request.method != "POST":
        return HttpResponseBadRequest("Only POST allowed.")
    print("step 1: request body =", request.body)

    try:
        payload = json.loads(request.body.decode("utf-8"))
        user_text = payload.get("text", "").strip()
        if not user_text:
            return HttpResponseBadRequest("Missing 'text' in request body.")
    except Exception:
        return HttpResponseBadRequest("Invalid JSON payload.")

    # 1) Save the prompt first (we’ll update with results soon)
    rubric_obj = RubricRequest.objects.create(prompt_text=user_text)

    try:
        print("am i getting here")
        # 2) Call OpenAI via our helper function
        rubric_list = generate_rubric_batch(user_text)
        print("step 2: generated rubric_list =", rubric_list)

        # 3) Save the JSON result back to the model
        rubric_obj.generated_rubric = rubric_list
        rubric_obj.save()

        # 4) Return the list of {part, weight} dicts as JSON
        print("Generated rubric:", rubric_list)
        return JsonResponse(rubric_list, safe=False)

    except Exception as e:
        print(e)
        # If anything goes wrong (OpenAI error or JSON parsing), record the error message
        rubric_obj.generated_rubric = {"error": str(e)}
        rubric_obj.save()

        return JsonResponse(
            {"error": "Could not generate rubric", "details": str(e)},
            status=500
        )



