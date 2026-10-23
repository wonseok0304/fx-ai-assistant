"""시계열 데이터 -> 요약 정보 (프롬프트 주입용) / 확장 통계."""
import statistics
from collections import defaultdict

from app.services import data_service

FLAT_THRESHOLD = 0.5  # %


def _pct(new, old):
    return (new - old) / old * 100 if old else 0.0


def build_summary(rows: list[dict] | None = None) -> dict:
    rows = rows if rows is not None else data_service.list_data()
    if not rows:
        return {"period": None, "count": 0, "metrics": {}, "trend": "데이터 없음"}

    vals = [r["value"] for r in rows]
    mx = max(rows, key=lambda r: r["value"])
    mn = min(rows, key=lambda r: r["value"])
    daily = [_pct(vals[i], vals[i - 1]) for i in range(1, len(vals))]

    # 최근 구간 평균 vs 직전 구간 평균으로 추세 판단
    w = 30 if len(vals) >= 60 else max(len(vals) // 2, 1)
    recent, prev = vals[-w:], vals[-2 * w:-w] or vals[:w]
    change = _pct(statistics.mean(recent), statistics.mean(prev))
    label = "상승" if change > FLAT_THRESHOLD else "하락" if change < -FLAT_THRESHOLD else "보합"

    metrics = {
        "latest": vals[-1],
        "latest_date": rows[-1]["date"],
        "average": round(statistics.mean(vals), 2),
        "max": mx["value"],
        "max_date": mx["date"],
        "min": mn["value"],
        "min_date": mn["date"],
        "volatility_pct": round(statistics.pstdev(daily), 3) if daily else 0.0,
        "change_7d_pct": round(_pct(vals[-1], vals[-8]), 2) if len(vals) > 7 else None,
    }
    return {
        "period": f"{rows[0]['date']} ~ {rows[-1]['date']}",
        "count": len(rows),
        "metrics": metrics,
        "trend": f"{label} (최근 {w}건 평균이 직전 {w}건 대비 {change:+.2f}%)",
    }


def build_statistics() -> dict:
    """월별 통계 + 7일 이동평균 (그래프용)."""
    rows = data_service.list_data()
    monthly = defaultdict(list)
    for r in rows:
        monthly[r["date"][:7]].append(r["value"])
    months = [
        {"month": m, "average": round(statistics.mean(v), 2), "max": max(v), "min": min(v), "count": len(v)}
        for m, v in sorted(monthly.items())
    ]
    vals = [r["value"] for r in rows]
    ma = [
        {"date": rows[i]["date"], "value": round(statistics.mean(vals[max(0, i - 6): i + 1]), 2)}
        for i in range(len(rows))
    ]
    return {"monthly": months, "moving_average_7": ma}


def summary_to_prompt_text(s: dict) -> str:
    if not s["count"]:
        return "- 저장된 데이터가 없습니다."
    m = s["metrics"]
    return (
        f"- 데이터 기간: {s['period']}\n"
        f"- 총 레코드: {s['count']}개\n"
        f"- 최근값: {m['latest']}원 ({m['latest_date']})\n"
        f"- 평균: {m['average']}원 / 최고: {m['max']}원 ({m['max_date']}) / 최저: {m['min']}원 ({m['min_date']})\n"
        f"- 일간 변동성(표준편차): {m['volatility_pct']}% / 최근 7건 변화율: {m['change_7d_pct']}%\n"
        f"- 최근 트렌드: {s['trend']}"
    )
