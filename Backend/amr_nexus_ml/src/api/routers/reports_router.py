from typing import Dict, Any
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException, status
from src.api.schemas import EmailReportRequest
from src.core.email import generate_and_send_pdf

reports_router = APIRouter()


@reports_router.post(
    "/generate",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=Dict[str, str],
)
async def generate_weekly_report(
    payload: EmailReportRequest, background_tasks: BackgroundTasks
) -> Dict[str, str]:
    try:
        background_tasks.add_task(generate_and_send_pdf, payload.email)
        return {"status": "Report generation and dispatch sequence initiated"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to queue reporting generation routine: {str(e)}",
        )
