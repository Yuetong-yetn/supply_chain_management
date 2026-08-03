#!/usr/bin/env bash
# ============================================================
# start_server.sh
#   自包含的后端启动脚本：启动 uvicorn 为后台进程，轮询健康检查
#   确认启动成功，然后主动退出，并通过退出码向调用方报告结果。
#
# 用法:
#   bash scripts/start_server.sh [host] [port]
#     默认 host=127.0.0.1  port=8000
#
# 退出码:
#   0  = 启动成功（/api/health 返回 success:true），服务保持后台运行
#   1  = 启动失败（进程拉起失败，或健康检查返回异常状态）
#   2  = 超时（进程已拉起，但在 START_TIMEOUT 秒内未能通过健康检查）
#
# 说明:
#   - 脚本使用项目根目录的 virtualenv (backend/.venv) 与 backend/ 作为工作目录。
#   - 日志写入 TEMP 目录，避免污染项目工作区。
#   - 本脚本只负责“启动 + 自检 + 回报”，不阻塞调用方；配合退出码使用。
# ============================================================

set -u

# ---------- 配置 ----------
HOST="${1:-127.0.0.1}"
PORT="${2:-8000}"
START_TIMEOUT="${START_TIMEOUT:-30}"        # 健康检查总超时（秒）
POLL_INTERVAL="${POLL_INTERVAL:-1}"         # 每次轮询间隔（秒）
HEALTH_PATH="/api/health"
LOG_DIR="${TEMP:-/tmp}"

# ---------- 解析项目根目录（脚本所在目录的上一级） ----------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
BACKEND_DIR="${PROJECT_ROOT}/backend"
VENV_PY="${BACKEND_DIR}/.venv/Scripts/python.exe"

# ---------- 前置校验 ----------
if [ ! -f "${VENV_PY}" ]; then
    echo "[start_server] ERROR: virtualenv not found at ${VENV_PY}" >&2
    exit 1
fi
if [ ! -d "${BACKEND_DIR}" ]; then
    echo "[start_server] ERROR: backend dir not found at ${BACKEND_DIR}" >&2
    exit 1
fi

# 若 backend/.env 缺失则不强制（允许默认配置），仅提示
if [ ! -f "${BACKEND_DIR}/.env" ]; then
    echo "[start_server] WARN: backend/.env not found; using defaults." >&2
fi

HEALTH_URL="http://${HOST}:${PORT}${HEALTH_PATH}"
STDOUT_LOG="${LOG_DIR}/start_server_${PORT}.out.log"
STDERR_LOG="${LOG_DIR}/start_server_${PORT}.err.log"

# ---------- 健康检查函数 ----------
health_ok() {
    # 用 curl 判断 /api/health 返回 success:true；
    # 无 curl 时退回 python urllib（跨平台稳妥）。
    if command -v curl >/dev/null 2>&1; then
        body="$(curl -s --max-time 3 "$HEALTH_URL" 2>/dev/null || true)"
        case "$body" in
            *'"success":true'*) return 0 ;;
            *) return 1 ;;
        esac
    else
        "${VENV_PY}" -c "import sys,urllib.request,json; \
try:
    r=urllib.request.urlopen('${HEALTH_URL}',timeout=3)
    return 0 if json.loads(r.read()).get('success') else 1
except Exception as e:
    sys.stderr.write(str(e)); sys.exit(1)" >/dev/null 2>&1
    fi
}

# ---------- 若端口已被占用：复用现有健康服务并直接成功 ----------
if health_ok; then
    echo "[start_server] OK: service already running at ${HEALTH_URL}"
    exit 0
fi

# ---------- 启动后台 uvicorn ----------
echo "[start_server] starting uvicorn on ${HOST}:${PORT} ..."
(
    cd "${BACKEND_DIR}" || exit 1
    "${VENV_PY}" -m uvicorn main:app --host "$HOST" --port "$PORT"
) >"${STDOUT_LOG}" 2>"${STDERR_LOG}" &
SVC_PID=$!
echo "[start_server] uvicorn pid=${SVC_PID} (logs: ${STDERR_LOG})"

# ---------- 轮询健康检查直到成功或超时 ----------
elapsed=0
while [ "$elapsed" -lt "$START_TIMEOUT" ]; do
    if ! kill -0 "$SVC_PID" 2>/dev/null; then
        echo "[start_server] ERROR: uvicorn process exited during startup." >&2
        echo "[start_server] --- stderr tail ---" >&2
        [ -f "$STDERR_LOG" ] && tail -n 15 "$STDERR_LOG" >&2
        exit 1
    fi
    if health_ok; then
        echo "[start_server] OK: ${HEALTH_URL} is healthy after ${elapsed}s."
        exit 0
    fi
    sleep "$POLL_INTERVAL"
    elapsed=$((elapsed + POLL_INTERVAL))
done

# ---------- 超时 ----------
echo "[start_server] TIMEOUT: health check not OK within ${START_TIMEOUT}s." >&2
echo "[start_server] --- stderr tail ---" >&2
[ -f "$STDERR_LOG" ] && tail -n 15 "$STDERR_LOG" >&2
exit 2
