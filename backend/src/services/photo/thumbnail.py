from typing import Dict

import numpy as np

from src.utils.file_io import load_json
from src.services.user.insightface_wrapper import face_engine
from src.constants import (
    METADATA_PATH,
    REPRESENTATIVES_PATH,
    TEMP_ENCODING_PATH,
)


def get_thumbnail_map() -> Dict[str, Dict]:
    # 정식 저장 + 임시 저장된 얼굴 데이터 불러오기
    metadata = load_json(METADATA_PATH)
    temp_faces = load_json(TEMP_ENCODING_PATH, [])

    # 타입 검사 및 통일
    metadata_faces = list(metadata.values()) if isinstance(metadata, dict) else metadata
    temp_faces = (
        list(temp_faces.values()) if isinstance(temp_faces, dict) else temp_faces
    )
    all_faces = metadata_faces + temp_faces

    # 대표 벡터 불러오기
    reps = load_json(REPRESENTATIVES_PATH)

    # 각 person_id마다 가장 유사한 얼굴을 고름
    thumbnail_map = {}

    for person_id, rep_vec in reps.items():
        best_sim = -1
        thumbnail_face = None

        for face in all_faces:
            # 작은 얼굴 제외
            if face.get("too_small"):
                continue

            if (
                face.get("person_id") != person_id
                and face.get("predicted_person") != person_id
            ):
                continue

            face_vec = np.array(face["encoding"], dtype=np.float32)
            sim = face_engine.cosine_similarity(rep_vec, face_vec)

            if sim > best_sim:
                best_sim = sim
                thumbnail_face = {
                    "file_name": face["file_name"],
                    "location": face["location"],
                    "face_id": face.get("face_id"),
                }

        if thumbnail_face:
            thumbnail_map[person_id] = thumbnail_face

    return thumbnail_map
