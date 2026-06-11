# -*- coding: utf-8 -*-
"""
产业链研究 API 路由
"""

import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from web.auth import get_current_user, oauth2_scheme
from web.database import (
    get_db, save_industry_report, get_user_industry_reports,
    get_industry_report_by_id, delete_industry_report,
)
from database.models import User
from engine.industry_research import engine as research_engine
from engine.industry_chains import get_all_industry_ids, get_chain_summary

router = APIRouter(prefix="/api/industry", tags=["产业链研究"])


# ===== 数据模型 =====

class ResearchRequest(BaseModel):
    industry_id: str


# ===== API 路由 =====

@router.get("/chains")
async def get_chains():
    """获取所有可用的产业链"""
    chains = research_engine.get_available_chains()
    return {"chains": chains, "total": len(chains)}


@router.get("/chains/{industry_id}")
async def get_chain_detail(industry_id: str):
    """获取产业链模板详情"""
    detail = research_engine.get_chain_layers_detail(industry_id)
    if not detail:
        raise HTTPException(status_code=404, detail="产业链不存在")
    return detail


@router.post("/research")
async def run_research(
    req: ResearchRequest,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    """执行产业链研究"""
    user = get_current_user(db, token)

    result = research_engine.research(req.industry_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    # 保存到数据库
    report_data_str = json.dumps(result, ensure_ascii=False)
    db_report = save_industry_report(
        db,
        user_id=user.id,
        industry_id=req.industry_id,
        industry_name=result.get("industry_name", ""),
        report_data=report_data_str,
    )

    return {
        "id": db_report.id,
        "report": result,
        "created_at": str(db_report.created_at),
    }


@router.get("/research")
async def list_research(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    """获取用户的研究记录列表"""
    user = get_current_user(db, token)
    reports = get_user_industry_reports(db, user.id, limit=limit, offset=offset)

    data = []
    for r in reports:
        report_data = json.loads(r.report_data) if r.report_data else {}
        data.append({
            "id": r.id,
            "industry_id": r.industry_id,
            "industry_name": r.industry_name,
            "summary": report_data.get("summary", {}),
            "created_at": str(r.created_at),
        })

    return {"results": data, "total": len(data)}


@router.get("/research/{report_id}")
async def get_research_detail(
    report_id: int,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    """获取研究报告详情"""
    user = get_current_user(db, token)
    r = get_industry_report_by_id(db, report_id)

    if r is None:
        raise HTTPException(status_code=404, detail="研究报告不存在")
    if r.user_id != user.id and user.username != "admin":
        raise HTTPException(status_code=403, detail="无权访问此报告")

    report_data = json.loads(r.report_data) if r.report_data else {}
    return {
        "id": r.id,
        "user_id": r.user_id,
        "industry_id": r.industry_id,
        "industry_name": r.industry_name,
        "report": report_data,
        "created_at": str(r.created_at),
    }


@router.delete("/research/{report_id}")
async def delete_research(
    report_id: int,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    """删除研究报告"""
    user = get_current_user(db, token)
    success = delete_industry_report(db, report_id, user.id)
    if not success:
        raise HTTPException(status_code=404, detail="研究报告不存在")
    return {"message": "删除成功"}


@router.get("/search")
async def search_company(
    industry_id: str = Query(...),
    keyword: str = Query(..., min_length=1),
):
    """在产业链中搜索公司"""
    results = research_engine.search_company_in_industry(industry_id, keyword)
    return {"results": results, "total": len(results)}
