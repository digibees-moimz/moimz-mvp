import os
import io
import cv2
from typing import List
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, Query
from fastapi.responses import StreamingResponse

from src.services.photo.clustering import (
    add_incremental_faces,
    run_album_clustering,
    save_clustered_faces,
    override_person,
)
from src.services.photo.thumbnail import get_thumbnail_map, get_image_path
from src.constants import (
    TEMP_CLUSTER_PATH,
    TEMP_ENCODING_PATH,
    METADATA_PATH,
)
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


# 인물별 앨범 리스트 조회 API
@router.get("/persons")
def list_persons():
    thumbnail_map = get_thumbnail_map()

    person_list = [
        {
            "person_id": person_id,
            "face_id": face["face_id"],
            "file_name": face["file_name"],
            "thumbnail": {
                "url": f"/persons/{person_id}/thumbnail",
                "file_name": face["file_name"],
                "location": face["location"],  # 썸네일 이미지 crop에 사용
                "face_id": face.get("face_id"),
            },
        }
        for person_id, face in thumbnail_map.items()
    ]

    return {"persons": person_list}


# 썸네일 반환 API
@router.get("/persons/{person_id}/thumbnail")
def get_person_thumbnail(person_id: str):

    thumbnail_map = get_thumbnail_map()
    thumbnail = thumbnail_map.get(person_id)

    if not thumbnail:
        return {"error": f"{person_id}에 대한 썸네일이 없습니다."}

    # 이미지 파일 열기
    file_name = thumbnail["file_name"]
    image_path = get_image_path(person_id, file_name)
    image = cv2.imread(image_path)
    if not Path(image_path).exists():
        return {"error": "이미지 파일이 존재하지 않습니다."}

    image = cv2.imread(str(image_path))
    top, right, bottom, left = thumbnail["location"]
    cropped = image[top:bottom, left:right]

    _, buffer = cv2.imencode(".jpg", cropped)
    return StreamingResponse(io.BytesIO(buffer.tobytes()), media_type="image/jpeg")
