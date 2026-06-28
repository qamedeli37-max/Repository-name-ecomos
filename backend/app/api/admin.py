from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from app.services.execution_service import ExecutionService

router = APIRouter()

_service = None


def get_service():
    global _service
    if _service is None:
        _service = ExecutionService()
    return _service


@router.get("/admin", response_class=HTMLResponse)
def admin_page():
    return """<!DOCTYPE html>
<html>
<head>
    <title>EcomOS Admin</title>
    <style>
        body { font-family: system-ui; max-width: 1200px; margin: 0 auto; padding: 20px; background: #f5f5f5; }
        h1 { color: #333; }
        .card { background: white; border-radius: 8px; padding: 20px; margin: 10px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #eee; }
        th { background: #f8f9fa; font-weight: 600; }
        .status { padding: 4px 8px; border-radius: 4px; font-size: 12px; }
        .success { background: #d4edda; color: #155724; }
        .failed { background: #f8d7da; color: #721c24; }
        .running { background: #fff3cd; color: #856404; }
        button { background: #007bff; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; }
        button:hover { background: #0056b3; }
        .detail { display: none; margin-top: 10px; padding: 15px; background: #f8f9fa; border-radius: 4px; }
        .timeline { margin: 10px 0; }
        .timeline-item { display: flex; align-items: center; margin: 5px 0; }
        .timeline-phase { width: 100px; font-weight: 600; }
        .timeline-bar { height: 20px; background: #007bff; border-radius: 4px; min-width: 2px; }
        .timeline-time { margin-left: 10px; color: #666; }
    </style>
</head>
<body>
    <h1>🎯 EcomOS Admin Console</h1>
    <div class="card">
        <h2>Execution Logs</h2>
        <button onclick="loadExecutions()">Refresh</button>
        <table id="exec-table">
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Goal</th>
                    <th>Status</th>
                    <th>Score</th>
                    <th>Started</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody id="exec-body"></tbody>
        </table>
        <div id="detail-panel" class="detail"></div>
    </div>
    <script>
        async function loadExecutions() {
            const res = await fetch('/executions?limit=20');
            const data = await res.json();
            const tbody = document.getElementById('exec-body');
            tbody.innerHTML = data.executions.map(e => `
                <tr>
                    <td>${e.execution_id.substring(0,8)}...</td>
                    <td>${e.goal}</td>
                    <td><span class="status ${e.status}">${e.status}</span></td>
                    <td>${e.score?.toFixed(2) || '-'}</td>
                    <td>${new Date(e.started_at).toLocaleString()}</td>
                    <td><button onclick="viewDetail('${e.execution_id}')">View</button></td>
                </tr>
            `).join('');
        }
        async function viewDetail(id) {
            const res = await fetch('/executions/' + id);
            const data = await res.json();
            const panel = document.getElementById('detail-panel');
            panel.style.display = 'block';
            panel.innerHTML = `
                <h3>Execution: ${id.substring(0,8)}...</h3>
                <p><strong>Goal:</strong> ${data.goal}</p>
                <p><strong>Status:</strong> <span class="status ${data.status}">${data.status}</span></p>
                <p><strong>Strategy:</strong> ${data.strategy} | <strong>Profile:</strong> ${data.profile} | <strong>Cognition:</strong> ${data.cognition}</p>
                <p><strong>Score:</strong> ${data.score?.toFixed(2) || '-'} | <strong>Replans:</strong> ${data.replans}</p>
                <h4>Steps (${data.steps?.length || 0})</h4>
                <pre>${JSON.stringify(data.steps, null, 2)}</pre>
                ${data.error ? `<h4>Error</h4><pre>${JSON.stringify(data.error, null, 2)}</pre>` : ''}
            `;
        }
        loadExecutions();
    </script>
</body>
</html>"""


@router.get("/api/admin/executions")
def admin_list_executions(limit: int = 20, offset: int = 0):
    service = get_service()
    logs = service.list_all(limit, offset)
    return {
        "executions": [
            {
                "id": log.id,
                "tenant_id": log.tenant_id,
                "goal": log.goal,
                "status": log.status,
                "score": log.score,
                "started_at": log.started_at.isoformat() if log.started_at else None,
                "finished_at": log.finished_at.isoformat() if log.finished_at else None
            }
            for log in logs
        ]
    }


@router.get("/api/admin/executions/{execution_id}")
def admin_get_execution(execution_id: str):
    service = get_service()
    log = service.get(execution_id)
    if not log:
        return {"error": "not found"}
    return {
        "id": log.id,
        "tenant_id": log.tenant_id,
        "goal": log.goal,
        "status": log.status,
        "started_at": log.started_at.isoformat() if log.started_at else None,
        "finished_at": log.finished_at.isoformat() if log.finished_at else None,
        "steps": log.steps or [],
        "result": log.result,
        "error": log.error,
        "strategy": log.strategy,
        "profile": log.profile,
        "cognition": log.cognition,
        "replans": log.replans,
        "score": log.score
    }
