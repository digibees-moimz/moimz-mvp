from typing import Dict

import numpy as np
from scipy.spatial.distance import cosine

from src.utils.file_io import load_json
from src.constants import (
    METADATA_PATH,
    REPRESENTATIVES_PATH,
    TEMP_ENCODING_PATH,
)


def get_thumbnail_map() -> Dict[str, Dict]:
    # 정식 저장 + 임시 저장된 얼굴 데이터 불러오기
    metadata = load_json(METADATA_PATH)
    temp_faces = load_json(TEMP_ENCODING_PATH, [])

    # 형식 통일
    all_faces = list(metadata.values()) + temp_faces

    # 대표 벡터 불러오기
    reps = load_json(REPRESENTATIVES_PATH)

    # 각 person_id마다 가장 유사한 얼굴을 고름
    thumbnail_map = {}

    for person_id, rep_vec in reps.items():
        min_distance = float("inf")
        thumbnail_face = None

        for face in all_faces:
            if (
                face.get("person_id") != person_id
                and face.get("predicted_person") != person_id
            ):
                continue

            face_vec = np.array(face["encoding"])
            distance = cosine(rep_vec, face_vec)

            if distance < min_distance:
                min_distance = distance
                thumbnail_face = {
                    "file_name": face["file_name"],
                    "location": face["location"],
                    "face_id": face.get("face_id"),
                }

        if thumbnail_face:
            thumbnail_map[person_id] = thumbnail_face

    return thumbnail_map
