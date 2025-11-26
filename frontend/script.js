const tasks = [];

const form = document.getElementById("task-form");
const bulkJson = document.getElementById("bulk-json");
const loadBulkBtn = document.getElementById("load-bulk");
const strategySelect = document.getElementById("strategy");
const analyzeBtn = document.getElementById("analyze-btn");
const suggestBtn = document.getElementById("suggest-btn");
const resultsDiv = document.getElementById("results");
const statusEl = document.getElementById("status");

const API_BASE = "http://127.0.0.1:8000/api/tasks";

function setStatus(text) {
  statusEl.textContent = text;
}

function readTask() {
  const id = document.getElementById("task-id").value.trim();
  const title = document.getElementById("task-title").value.trim();
  const due_date = document.getElementById("due-date").value || null;
  const estimated_hours = document.getElementById("estimated-hours").value || null;
  const importance = document.getElementById("importance").value || null;

  const depsRaw = document.getElementById("dependencies").value.trim();
  const dependencies = depsRaw ? depsRaw.split(",").map(d => d.trim()) : [];

  if (!title) {
    alert("Task title is required.");
    return null;
  }

  return {
    id: id || undefined,
    title,
    due_date,
    estimated_hours: estimated_hours ? Number(estimated_hours) : null,
    importance: importance ? Number(importance) : null,
    dependencies
  };
}

form.addEventListener("submit", e => {
  e.preventDefault();
  const task = readTask();
  if (!task) return;

  tasks.push(task);
  setStatus(`Added task "${task.title}". Total: ${tasks.length}`);
  form.reset();
});

loadBulkBtn.addEventListener("click", () => {
  try {
    const parsed = JSON.parse(bulkJson.value);
    if (!Array.isArray(parsed)) {
      alert("JSON must be an array.");
      return;
    }
    tasks.length = 0;
    parsed.forEach(t => tasks.push(t));
    setStatus(`Loaded ${tasks.length} tasks.`);
  } catch (err) {
    alert("Invalid JSON.");
  }
});

function renderTasks(list, top = false) {
  if (!list.length) {
    resultsDiv.innerHTML = "<p>No results.</p>";
    return;
  }

  resultsDiv.innerHTML = list
    .map(t => {
      const badge =
        t.score >= 0.7
          ? "high"
          : t.score >= 0.4
          ? "medium"
          : "low";

      return `
        <div class="task-card">
          <strong>${t.title}</strong>
          <div class="task-meta">
            <span>ID: ${t.id ?? "-"}</span>
            <span>Score: ${t.score}</span>
            <span>Due: ${t.due_date || "N/A"}</span>
            <span>Hrs: ${t.estimated_hours ?? "N/A"}</span>
            <span>Imp: ${t.importance ?? "N/A"}</span>
            <span>Deps: ${t.dependencies.join(", ") || "None"}</span>
            <span class="badge ${badge}">Priority</span>
          </div>
          <p style="margin-top:4px;font-size:0.85rem;">${t.explanation}</p>
        </div>
      `;
    })
    .join("");
}

analyzeBtn.addEventListener("click", async () => {
  if (!tasks.length) return alert("Add tasks first.");

  const strategy = strategySelect.value;

  const res = await fetch(`${API_BASE}/analyze/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ tasks, strategy })
  });

  const data = await res.json();

  if (!res.ok) return setStatus("Error analyzing tasks.");

  renderTasks(data.tasks);
  setStatus(data.warnings?.join(" | ") || "Analysis complete.");
});

suggestBtn.addEventListener("click", async () => {
  if (!tasks.length) return alert("Add tasks first.");

  const strategy = strategySelect.value;
  const tasksJson = encodeURIComponent(JSON.stringify(tasks));

  const res = await fetch(`${API_BASE}/suggest/?tasks=${tasksJson}&strategy=${strategy}`);
  const data = await res.json();

  if (!res.ok) return setStatus("Error fetching suggestions.");

  renderTasks(data.top_tasks, true);
  setStatus(data.warnings?.join(" | ") || "Top suggestions ready.");
});
