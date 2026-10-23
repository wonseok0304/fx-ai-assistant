"""보너스: 동일 기능을 MCP 서버로 노출 (Claude Desktop 등 외부 클라이언트용).

배포된 REST API(API_BASE_URL)를 도구로 감싼다.
설치: pip install mcp httpx    실행: API_BASE_URL=https://... python mcp_server/server.py
"""
import os

import httpx
from mcp.server.fastmcp import FastMCP

API = os.getenv("API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
mcp = FastMCP("fx-ai-assistant")


def _get(path: str):
    r = httpx.get(f"{API}{path}", timeout=60)
    r.raise_for_status()
    return r.json()


@mcp.tool()
def get_data_summary() -> dict:
    """환율 데이터 요약(기간/개수/통계/트렌드)을 조회한다."""
    return _get("/api/data/summary")


@mcp.tool()
def get_recent_data(limit: int = 10) -> list:
    """가장 최근 환율 레코드 N개를 조회한다."""
    return _get("/api/data")[-max(1, min(limit, 60)):]


@mcp.tool()
def list_conversations() -> list:
    """저장된 대화 목록을 조회한다."""
    return _get("/api/conversations")


@mcp.tool()
def get_conversation(conversation_id: str) -> dict:
    """특정 대화의 전체 메시지를 조회한다."""
    return _get(f"/api/conversations/{conversation_id}")


if __name__ == "__main__":
    mcp.run()
