from fastapi import APIRouter, UploadFile, File
from typing import List
import face_recognition
import numpy as np
import os, pickle, cv2
from .face_clustering import update_user_clusters, visualize_clusters

router = APIRouter()

face_db = {}  # 얼굴 데이터 저장 - 임시
FACE_DATA_DIR = os.path.join("src", "face_data")  # 얼굴 데이터 저장 폴더 경로 설정
os.makedirs(FACE_DATA_DIR, exist_ok=True)  # 얼굴 벡터 파일 저장 디렉토리 생성


# 저장된 얼굴 벡터 파일들을 불러오는 로직
def load_faces_from_files():
    for file in os.listdir(FACE_DATA_DIR):
        if file.startswith("face_") and file.endswith(".pkl"):
            try:
                user_id = int(file.split("_")[1].split(".")[0])
                with open(os.path.join(FACE_DATA_DIR, file), "rb") as f:
                    loaded_data = pickle.load(f)

                    # 만약 loaded_data가 리스트이면, 새로운 구조로 변환
                    if isinstance(loaded_data, list):
                        loaded_data = {"raw": loaded_data}
                    face_db[user_id] = loaded_data
                print(f"✅ {user_id}번 사용자의 얼굴 데이터를 불러왔습니다.")
            except Exception as e:
                print(f"⚠️ {file} 로딩 실패: {e}")


# 서버 시작 시, 저장된 벡터 파일들을 불러옴
load_faces_from_files()


# 얼굴 등록 API
@router.post("/register_faces/{user_id}")
async def register_faces(user_id: int, files: List[UploadFile] = File(...)):

    encodings_list = []
    skipped_files = []  # 얼굴이 2개 이상인 파일 저장용

    for file in files:
        image_bytes = await file.read()  # 파일을 바이트로 읽기
        image_np = np.frombuffer(image_bytes, np.uint8)  # 바이트를 NumPy 배열로 변환
        image = cv2.imdecode(image_np, cv2.IMREAD_COLOR)  # OpenCV 형식으로 변환

        # 얼굴 인식 및 특징 벡터 추출
        face_encodings = face_recognition.face_encodings(image)

        if not face_encodings:
            skipped_files.append(
                {
                    "filename": file.filename,
                    "detected_faces": 0,
                    "reason": "해당 사진에서 얼굴을 찾을 수 없음",
                }
            )
            continue  # 감지된 얼굴으면 건너뜀

        if len(face_encodings) > 1:
            skipped_files.append(
                {
                    "filename": file.filename,
                    "detected_faces": len(face_encodings),
                    "reason": f"해당 사진에서 {len(face_encodings)}개의 얼굴이 감지됨",
                }
            )
            continue  # 얼굴이 2개 이상이면 등록 안 함

        encodings_list.append(face_encodings[0])

    if not encodings_list:
        if skipped_files:
            return {
                "error": "등록 가능한 얼굴이 없습니다.",
                "skipped_files": skipped_files,
            }

    # 기존 데이터와 합치기
    if user_id in face_db:
        # 만약 기존 데이터가 리스트 형태라면 "raw" 키로 변환
        if isinstance(face_db[user_id], list):
            face_db[user_id] = {"raw": face_db[user_id]}

        face_db[user_id]["raw"].extend(encodings_list)
    else:
        face_db[user_id] = {"raw": encodings_list}

    # 얼굴 등록 후 클러스터링 업데이트
    cluster_msg = update_user_clusters(face_db, user_id)

    # 얼굴 벡터 데이터를 파일로 저장
    save_path = os.path.join(FACE_DATA_DIR, f"face_{user_id}.pkl")
    with open(save_path, "wb") as f:
        pickle.dump(face_db[user_id], f)  # 사용자 데이터(딕셔너리) 전체 전체 저장

    new_encoding = encodings_list[0]  # 새로 등록한 얼굴 벡터

    # 기존 얼굴 데이터와 유사도 비교
    similarity_results = []
    for existing_user_id, data in face_db.items():
        raw_vectors = data.get("raw", [])
        if raw_vectors:
            distances = face_recognition.face_distance(raw_vectors, new_encoding)
            min_distance = float(np.min(distances))
            similarity_results.append(
                {"user_id": existing_user_id, "min_distance": min_distance}
            )

    return {
        "message": f"{user_id}번 사용자의 얼굴 {len(files)}개 중 {len(encodings_list)}개 등록 완료!",
        "cluster_msg": cluster_msg,  # 클러스터링 결과 메시지 포함
        "skipped_files": skipped_files,
        "similarity_results": similarity_results,  # 기존 얼굴과 유사도 출력
    }


# 출석체크 API
@router.post("/check_attendance")
async def check_attendance(file: UploadFile = File(...)):
    image_bytes = await file.read()
    image_np = np.frombuffer(image_bytes, np.uint8)
    image = cv2.imdecode(image_np, cv2.IMREAD_COLOR)

    # 단체 사진에서 얼굴 인코딩 추출
    unknown_encodings = face_recognition.face_encodings(image)
    if not unknown_encodings:
        return {"message": "사진에서 얼굴을 찾을 수 없습니다."}

    all_matches = []

    # 모든 (unknown 얼굴, 등록된 얼굴) 조합 거리 계산
    for unknown_id, unknown_encoding in enumerate(unknown_encodings):
        for user_id, user_data in face_db.items():
            raw_vectors = user_data.get("raw", [])
            clusters = user_data.get("clusters", None)

            # 클러스터링된 경우
            if clusters:
                centroids = np.array(clusters["centroids"])
                labels = clusters["labels"]

                # 중심점들과 거리 비교 → 가장 가까운 클러스터 선택
                distances_to_centroids = face_recognition.face_distance(
                    centroids, unknown_encoding
                )
                closest_cluster_idx = int(np.argmin(distances_to_centroids))

                # 해당 클러스터에 속한 raw 벡터들만 비교
                selected_vectors = [
                    raw_vectors[i]
                    for i, label in enumerate(labels)
                    if label == closest_cluster_idx  # 가장 가까운 클러스터 선택
                ]

            else:
                # 클러스터가 없으면 전체 raw 벡터와 비교
                selected_vectors = raw_vectors

            if not selected_vectors:
                continue

            # 벡터들과 실제 거리 계산
            for known_encoding in selected_vectors:
                distance = face_recognition.face_distance(
                    [known_encoding], unknown_encoding
                )[0]
                all_matches.append(
                    {"unknown_id": unknown_id, "user_id": user_id, "distance": distance}
                )

    # 거리 기준 정렬 (유사한 조합부터 차례대로 검사하기 위함)
    all_matches.sort(key=lambda x: x["distance"])

    matched_users = set()  # 출석된 user_id들 저장 (중복 방지용)
    matched_unknowns = set()  # 단체 사진 속 얼굴들 중 이미 매칭된 얼굴
    attendance_results = []  # 최종 출석 결과 저장

    for match in all_matches:
        if match["distance"] > 0.45:
            break  # 정렬되었기 때문에 유사도가 기준값을 넘어가면 더이상 확인할 필요 없음

        if match["user_id"] in matched_users:
            continue
        if match["unknown_id"] in matched_unknowns:
            continue

        matched_users.add(match["user_id"])
        matched_unknowns.add(match["unknown_id"])
        attendance_results.append(
            {"user_id": match["user_id"], "distance": match["distance"]}
        )

    if attendance_results:
        return {
            "출석자 ID 명단": list(attendance_results),
            "출석 인원 수": len(attendance_results),
        }
    else:
        return {"message": "출석한 사람 없음"}


# 클러스터링 시각화 API
@router.get("/visualize_clusters/{user_id}")
async def get_cluster_visualization(user_id: int):
    return visualize_clusters(face_db, user_id)
