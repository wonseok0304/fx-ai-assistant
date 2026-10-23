"""AI 챗봇: 요약 컨텍스트 주입 + Function Calling(도구 호출) + 대화 자동 저장."""
import json
import logging

from fastapi import HTTPException
from openai import OpenAI, OpenAIError

from app import config
from app.services import conversation_service as conv_svc
from app.services import data_service, summary_service

logger = logging.getLogger(__name__)

SYSTEM_TEMPLATE = """당신은 USD/KRW 환율 데이터 분석 비서입니다.

[사용자 데이터 요약]
{summary}

위 데이터를 기반으로 맞춤형 답변을 제공하세요.
- 요약에 있는 수치는 그대로 인용하고, 없는 수치는 지어내지 마세요.
- 더 자세한 값이 필요하면 제공된 도구를 호출하세요.
- 투자 권유는 하지 말고, 데이터에 근거한 해석만 간결한 한국어로 답하세요."""

TOOLS = [
    {"type": "function", "function": {
        "name": "get_data_summary",
        "description": "저장된 환율 데이터의 최신 요약(기간/개수/통계/트렌드)을 조회한다.",
        "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {
        "name": "get_recent_data",
        "description": "가장 최근 N개의 일별 환율 레코드를 조회한다. 특정 날짜 부근 값이 필요할 때 사용.",
        "parameters": {"type": "object", "properties": {
            "limit": {"type": "integer", "minimum": 1, "maximum": 60}}, "required": ["limit"]}}},
    {"type": "function", "function": {
        "name": "list_conversations",
        "description": "저장된 이전 대화 목록(제목, id)을 조회한다.",
        "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {
        "name": "get_conversation",
        "description": "특정 대화의 전체 메시지를 조회한다.",
        "parameters": {"type": "object", "properties": {"conversation_id": {"type": "string"}},
                       "required": ["conversation_id"]}}},
]


def run_tool(name: str, args: dict):
    if name == "get_data_summary":
        return summary_service.build_summary()
    if name == "get_recent_data":
        limit = max(1, min(int(args.get("limit", 10)), 60))
        rows = data_service.list_data(limit=limit, order="desc")
        return [{"date": r["date"], "value": r["value"], "memo": r.get("memo", "")} for r in rows]
    if name == "list_conversations":
        return conv_svc.list_conversations()[:10]
    if name == "get_conversation":
        c = conv_svc.get_conversation(args.get("conversation_id", ""))
        return c or {"error": "대화를 찾을 수 없습니다."}
    return {"error": f"알 수 없는 도구: {name}"}


def chat(message: str, conversation_id: str | None) -> dict:
    if not config.OPENAI_API_KEY:
        raise HTTPException(503, "OPENAI_API_KEY가 설정되지 않았습니다.")

    history = []
    if conversation_id:
        conv = conv_svc.get_conversation(conversation_id)
        if not conv:
            raise HTTPException(404, "대화를 찾을 수 없습니다.")
        history = [{"role": m["role"], "content": m["content"]} for m in conv["messages"][-10:]]

    # 컨텍스트 주입: 데이터 요약을 시스템 프롬프트에 삽입
    summary = summary_service.build_summary()
    system = SYSTEM_TEMPLATE.format(summary=summary_service.summary_to_prompt_text(summary))
    messages = [{"role": "system", "content": system}, *history, {"role": "user", "content": message}]

    client = OpenAI(api_key=config.OPENAI_API_KEY, base_url=config.OPENAI_BASE_URL, timeout=45)
    tools_used = []
    try:
        for _ in range(3):  # 도구 호출 루프 (최대 3회)
            res = client.chat.completions.create(
                model=config.OPENAI_MODEL, messages=messages, tools=TOOLS,
                max_tokens=config.OPENAI_MAX_TOKENS, temperature=0.3)
            msg = res.choices[0].message
            if not msg.tool_calls:
                break
            messages.append(msg)
            for call in msg.tool_calls:
                args = json.loads(call.function.arguments or "{}")
                tools_used.append({"name": call.function.name, "arguments": args})
                messages.append({"role": "tool", "tool_call_id": call.id,
                                 "content": json.dumps(run_tool(call.function.name, args), ensure_ascii=False)})
        else:
            msg = client.chat.completions.create(
                model=config.OPENAI_MODEL, messages=messages,
                max_tokens=config.OPENAI_MAX_TOKENS).choices[0].message
    except OpenAIError as e:
        raise HTTPException(502, f"AI 호출 실패: {e.__class__.__name__}")

    reply = (msg.content or "").strip() or "답변을 생성하지 못했습니다."

    # 자동 저장
    # 저장에 실패해도 이미 생성된 답변은 사용자에게 돌려주고, saved=False로 알린다.
    new = [{"role": "user", "content": message}, {"role": "assistant", "content": reply}]
    saved = True
    try:
        if conversation_id:
            conv_svc.append_messages(conversation_id, new)
        else:
            conversation_id = conv_svc.create_conversation("", new)["id"]
    except Exception:
        logger.exception("대화 자동 저장 실패")
        saved = False
    return {"reply": reply, "conversation_id": conversation_id, "tools_used": tools_used, "saved": saved}
