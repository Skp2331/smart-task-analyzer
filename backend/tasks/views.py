import json
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt

from .scoring import analyze_tasks, suggest_top_tasks


def _parse_tasks_from_body(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return None, "Invalid JSON body."

    tasks = data.get("tasks")
    if not isinstance(tasks, list):
        return None, "'tasks' must be a list."

    strategy = data.get("strategy", "smart_balance")
    return {"tasks": tasks, "strategy": strategy}, None


from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse

@csrf_exempt
def analyze_tasks_view(request):
    if request.method == "OPTIONS":
        return JsonResponse({"message": "CORS preflight OK"}, status=200)

    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)

    parsed, error = _parse_tasks_from_body(request)
    if error:
        return JsonResponse({"error": error}, status=400)

    tasks = parsed["tasks"]
    strategy = parsed["strategy"]

    analyzed, warnings = analyze_tasks(tasks, strategy=strategy)
    return JsonResponse(
        {
            "strategy": strategy,
            "tasks": analyzed,
            "warnings": warnings,
            "count": len(analyzed),
        },
        status=200,
    )



@csrf_exempt
def suggest_tasks_view(request):
    if request.method == "OPTIONS":
        return JsonResponse({"message": "CORS preflight OK"}, status=200)

    if request.method != "GET":
        return JsonResponse({"error": "Only GET allowed"}, status=405)

    tasks_param = request.GET.get("tasks")
    if not tasks_param:
        return JsonResponse(
            {"error": "Please provide tasks as ?tasks=<json_array>"},
            status=400,
        )

    try:
        tasks = json.loads(tasks_param)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON in 'tasks' query parameter."}, status=400)

    strategy = request.GET.get("strategy", "smart_balance")

    top_tasks, warnings = suggest_top_tasks(tasks, strategy=strategy, limit=3)
    return JsonResponse(
        {
            "strategy": strategy,
            "top_tasks": top_tasks,
            "warnings": warnings,
            "count": len(top_tasks),
        },
        status=200,
    )

