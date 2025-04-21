import os
import cv2

import numpy as np
from fastapi import APIRouter, UploadFile, File, Query
from typing import List
from pathlib import Path
from fastapi.responses import FileResponse

from src.utils.file_io import load_json, save_json
from src.services.photo.clustering import process_and_classify_faces
from src.constants import METADATA_PATH, ALBUM_DIR, MIN_FACE_COUNT, REPRESENTATIVES_PATH

router = APIRouter()


@router.post("/upload")
async def upload_faces(files: List[UploadFile] = File(...)):
    results = await process_and_classify_faces(files)
    return {"message": "얼굴 업로드 및 분류 완료", "results": results}


# 전체 앨범 목록 조회
@router.get("/albums")
def list_albums():
    metadata = load_json(METADATA_PATH, {})
    albums = {}

    # too_small 제외하고 count
    for face in metadata.values():
        if face.get("too_small"):  # 작아서 제외된 얼굴
            continue
        person_id = face.get("override") or face.get("person_id", "unknown")
        albums.setdefault(person_id, []).append(face)

    album_list = []

    # 전체 앨범
    uploaded_files = os.listdir(Path(ALBUM_DIR) / "uploaded")
    if uploaded_files:
        album_list.append(
            {
                "album_id": "all_photos",
                "title": "전체 사진",
                "type": "all",
                "count": len(uploaded_files),
                "thumbnail": {
                    "file_name": uploaded_files[-1],
                    "url": f"/images/{uploaded_files[-1]}",
                },
            }
        )

    # 인물/미분류 앨범
    for person_id, faces in albums.items():
        # 너무 적으면 앨범 생성 안함
        if len(faces) < MIN_FACE_COUNT:
            continue

        album_type = "unknown" if person_id == "unknown" else "person"
        thumbnail_face_id = find_face_id(metadata, faces[0])

        album_list.append(
            {
                "album_id": person_id,
                "title": person_id,
                "type": album_type,
                "count": len(faces),
                "thumbnail": {
                    "file_name": faces[0]["file_name"],
                    "url": f"/thumbnails/{thumbnail_face_id}",  # 크롭된 썸네일 사용
                },
            }
        )

    return {"albums": album_list}


# 인물별 앨범 상세 조회
@router.get("/albums/{album_id}")
def get_album_faces(album_id: str):
    metadata = load_json(METADATA_PATH, {})
    if album_id == "all_photos":
        image_files = os.listdir(Path(ALBUM_DIR) / "uploaded")
        return {
            "album_id": album_id,
            "faces": [
                {"file_name": f, "image_url": f"/images/{f}"} for f in image_files
            ],
        }

    result_faces = []
    for face_id, face in metadata.items():
        person_id = face.get("override") or face.get("person_id", "unknown")
        if person_id == album_id:
            result_faces.append(
                {
                    "face_id": face_id,
                    "file_name": face["file_name"],
                    "location": face["location"],
                    "image_url": f"/images/{face['file_name']}",
                }
            )

    return {"album_id": album_id, "count": len(result_faces), "faces": result_faces}


def find_face_id(metadata, face_data):
    for face_id, data in metadata.items():
        if data == face_data:
            return face_id


# 얼굴 ID 기반 썸네일 이미지 반환 (crop 영역 반환)
@router.get("/thumbnails/{face_id}")
def get_face_thumbnail(face_id: str):
    metadata = load_json(METADATA_PATH, {})
    if face_id not in metadata:
        return {"error": "해당 face_id가 존재하지 않습니다."}

    face_info = metadata[face_id]
    file_name = face_info["file_name"]
    top, right, bottom, left = face_info["location"]
    image_path = Path(ALBUM_DIR) / "uploaded" / file_name

    if not image_path.exists():
        return {"error": "원본 이미지가 존재하지 않습니다."}

    # 이미지 열고 얼굴 영역 자르기
    image = cv2.imread(str(image_path))
    cropped = image[top:bottom, left:right]
    thumb_path = Path(ALBUM_DIR) / "thumbnails"
    os.makedirs(thumb_path, exist_ok=True)

    thumb_file = thumb_path / f"{face_id}.jpg"
    cv2.imwrite(str(thumb_file), cropped)

    return FileResponse(thumb_file)


@router.get("/images/{file_name}")
def get_image(file_name: str):
    image_path = Path(ALBUM_DIR) / "uploaded" / file_name
    if not image_path.exists():
        return {"error": "이미지가 존재하지 않습니다."}
    return FileResponse(image_path)


# 사용자 수정
@router.post("/faces/override")
def override_face_label(face_id: str = Query(...), new_person_id: str = Query(...)):
    metadata = load_json(METADATA_PATH, {})
    if face_id not in metadata:
        return {"error": "face_id가 존재하지 않음"}

    metadata[face_id]["override"] = new_person_id
    save_json(METADATA_PATH, metadata)
    return {"message": f"{face_id} → {new_person_id} 재지정 완료"}


# 인물 병합 API
@router.post("/faces/merge")
def merge_person(
    source_person_id: str = Query(...), target_person_id: str = Query(...)
):
    metadata = load_json(METADATA_PATH)
    representatives = load_json(REPRESENTATIVES_PATH)

    if source_person_id == target_person_id:
        return {"error": "같은 person_id는 병합할 수 없습니다."}

    # 병합 대상 face 업데이트
    for face in metadata.values():
        if face.get("person_id") == source_person_id:
            face["person_id"] = target_person_id

    # 대표 벡터 처리
    if source_person_id in representatives:
        source_vec = np.array(representatives[source_person_id], dtype=np.float32)
        target_vecs = (
            [np.array(representatives[target_person_id], dtype=np.float32)]
            if target_person_id in representatives
            else []
        )
        all_vecs = target_vecs + [source_vec]
        new_rep = np.mean(all_vecs, axis=0)
        representatives[target_person_id] = new_rep.tolist()

    # source person 제거
    representatives.pop(source_person_id, None)
    representatives.pop(f"{source_person_id}_history", None)

    save_json(METADATA_PATH, metadata)
    save_json(REPRESENTATIVES_PATH, representatives)

    return {"message": f"{source_person_id} → {target_person_id} 병합 완료"}
