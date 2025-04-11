import os
from fastapi import APIRouter, UploadFile, File, Query
from typing import List
from pathlib import Path

from src.utils.file_io import load_json, save_json
from src.services.photo.clustering import process_and_classify_faces
from src.constants import METADATA_PATH, ALBUM_DIR

router = APIRouter()


@router.post("/faces/upload")
async def upload_faces(files: List[UploadFile] = File(...)):
    results = await process_and_classify_faces(files)
    return {"message": "얼굴 업로드 및 분류 완료", "results": results}


# 전체 앨범 목록 조회
@router.get("/albums")
def list_albums():
    metadata = load_json(METADATA_PATH, {})
    albums = {}

    for face in metadata.values():
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
        album_type = "unknown" if person_id == "unknown" else "person"
        album_list.append(
            {
                "album_id": person_id,
                "title": person_id,
                "type": album_type,
                "count": len(faces),
                "thumbnail": {
                    "file_name": faces[0]["file_name"],
                    "url": f"/images/{faces[0]['file_name']}",
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


# 사용자 수정
@router.post("/faces/override")
def override_face_label(face_id: str = Query(...), new_person_id: str = Query(...)):
    metadata = load_json(METADATA_PATH, {})
    if face_id not in metadata:
        return {"error": "face_id가 존재하지 않음"}

    metadata[face_id]["override"] = new_person_id
    save_json(METADATA_PATH, metadata)
    return {"message": f"{face_id} → {new_person_id} 재지정 완료"}
