import os
from typing import List
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, Query

from src.services.photo.clustering import (
    add_incremental_faces,
    run_album_clustering,
    save_clustered_faces,
    override_person,
)
from src.constants import TEMP_CLUSTER_PATH, TEMP_ENCODING_PATH, METADATA_PATH
from src.utils.file_io import load_json

router = APIRouter()


# 사진 업로드 시 인물별 자동 분류 API
@router.post("/upload")
async def upload_faces(files: List[UploadFile] = File(...)):
    if not Path(TEMP_CLUSTER_PATH).exists():
        # 처음 업로드면 클러스터링
        return await run_album_clustering(files)
    else:
        # 이미 임시 데이터가 있다면 증분 분류
        return await add_incremental_faces(files)


# 사용자 수정(인물 재지정)
@router.post("/override_person")
async def manual_override_person(
    face_id: str = Query(..., description="ex. face_0003"),
    new_person_id: str = Query(..., description="ex. person_5"),
):
    success = override_person(face_id, new_person_id)

    if success:
        return {"message": f"{face_id} → {new_person_id}로 수동 재지정 완료되었습니다."}
    else:
        return {
            "error": f"{face_id}가 존재하지 않습니다. 유효한 face_id를 확인해주세요."
        }


# 클러스터링 결과 저장
@router.post("/confirm_save")
async def confirm_save():
    cluster_data = load_json(TEMP_CLUSTER_PATH, {})
    full_encodings = load_json(TEMP_ENCODING_PATH, [])

    result = save_clustered_faces(cluster_data, full_encodings)

    # 임시 데이터 삭제
    os.remove(TEMP_CLUSTER_PATH)
    os.remove(TEMP_ENCODING_PATH)

    return {
        "message": "임시 데이터를 정식 저장소로 이동 완료했습니다.",
        "saved": result,
    }

# 특정 인물의 사진 리스트 조회 API 
@router.get("/people/{person_id}")
def get_person_faces(person_id: str):
    # 정식 저장된 얼굴 정보 불러오기 (dict)
    metadata = load_json(METADATA_PATH, {})
    metadata_faces = [
        {
            "file_name": v["file_name"],
            "location": v["location"],
            "face_id": k,
        }
        for k, v in metadata.items()
        if v.get("person_id") == person_id
    ]

    # 임시 저장된 얼굴 정보 불러오기 (list)
    temp_faces = load_json(TEMP_ENCODING_PATH, [])
    temp_person_faces = [
        {
            "file_name": f["file_name"],
            "location": f["location"],
            "face_id": f.get("face_id"),
        }
        for f in temp_faces
        if f.get("predicted_person") == person_id
    ]

    all_faces = metadata_faces + temp_person_faces

    return {
        "person_id": person_id,
        "num_faces": len(all_faces),
        "faces": all_faces,
    }
