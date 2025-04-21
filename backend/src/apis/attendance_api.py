from fastapi import APIRouter, UploadFile, File
from src.services.attendance.checker import run_attendance_check

router = APIRouter()


# 출석체크 API
@router.post("/check")
async def check_attendance(file: UploadFile = File(...)):
    return await run_attendance_check(file)
