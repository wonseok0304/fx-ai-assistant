import csv
import io
import json

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response

from app.schemas import DataIn, DataOut, SummaryOut
from app.services import data_service, summary_service

router = APIRouter(prefix="/api/data", tags=["data"])


@router.post("", response_model=DataOut, status_code=201)
def create(body: DataIn):
    return data_service.create_data(body.model_dump())


@router.get("", response_model=list[DataOut])
def list_all():
    return data_service.list_data()


@router.get("/summary", response_model=SummaryOut)
def summary():
    return summary_service.build_summary()


@router.get("/statistics")
def statistics():
    return summary_service.build_statistics()


@router.get("/export")
def export(format: str = Query("csv", pattern="^(csv|json)$")):
    rows = data_service.list_data()
    if format == "json":
        body, media = json.dumps(rows, ensure_ascii=False, indent=2), "application/json"
    else:
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(["date", "value", "memo"])
        w.writerows([r["date"], r["value"], r.get("memo", "")] for r in rows)
        body, media = "﻿" + buf.getvalue(), "text/csv"
    return Response(body, media_type=media,
                    headers={"Content-Disposition": f'attachment; filename="usd_krw.{format}"'})


@router.put("/{doc_id}", response_model=DataOut)
def update(doc_id: str, body: DataIn):
    updated = data_service.update_data(doc_id, body.model_dump())
    if not updated:
        raise HTTPException(404, "데이터를 찾을 수 없습니다.")
    return updated


@router.delete("/{doc_id}")
def delete(doc_id: str):
    if not data_service.delete_data(doc_id):
        raise HTTPException(404, "데이터를 찾을 수 없습니다.")
    return {"deleted": doc_id}
