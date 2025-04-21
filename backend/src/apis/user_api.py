from fastapi import APIRouter, Query

from src.constants import USER_INFO_PATH
from src.utils.file_io import load_json, save_json

router = APIRouter()


@router.post("/users/set-name")
def set_user_name(user_id: int = Query(...), name: str = Query(...)):
    user_info = load_json(USER_INFO_PATH, {})
    user_info[str(user_id)] = {"name": name}
    save_json(USER_INFO_PATH, user_info)
    return {"message": f"{user_id}번 사용자 이름이 '{name}'으로 저장되었습니다."}
