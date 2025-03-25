from fastapi import APIRouter, UploadFile, File
from sklearn.cluster import KMeans
from typing import List
import face_recognition
import numpy as np
import os
import pickle
import cv2

router = APIRouter()


face_db = {}  # 얼굴 데이터 저장 - 임시
FACE_DATA_DIR = os.path.join("src", "face_data")  # 얼굴 데이터 저장 폴더 경로 설정
os.makedirs(FACE_DATA_DIR, exist_ok=True)  # 얼굴 벡터 파일 저장 디렉토리 생성


# 저장된 얼굴 벡터 파일들을 불러오는 로직
def load_faces_from_files():
    for file in os.listdir(FACE_DATA_DIR):
        # "face_00.pkl" 형식의 파일 찾기
        if file.startswith("face_") and file.endswith(".pkl"):
            try:
                # 파일명에서 user_id 추출
                user_id = int(file.split("_")[1].split(".")[0])
                with open(os.path.join(FACE_DATA_DIR, file), "rb") as f:
                    face_db[user_id] = pickle.load(f)  # 얼굴 벡터 복원
                print(f"✅ {user_id}번 사용자의 얼굴 데이터를 불러왔습니다.")
            except Exception as e:
                print(f"⚠️ {file} 로딩 실패: {e}")


# 서버 시작 시, 저장된 벡터 파일들을 불러옴
load_faces_from_files()


# 클러스터링 업데이트 함수 - threshold: 임계치, n_clusters: 클러스터의 개수(k)
def update_user_clusters(user_id: int, threshold: int = 5, n_clusters: int = 3):

    # 사용자 원본 벡터 리스트(raw 데이터) 가져오기
    user_data = face_db.get(user_id)

    if not user_data or "raw" not in user_data:
        print(f"사용자 {user_id}의 raw 데이터가 없습니다.")
        return

    raw_vectors = user_data["raw"]
    if len(raw_vectors) < threshold:
        print(
            f"사용자 {user_id}의 raw 벡터 수가 {threshold}개 미만이므로 클러스터링을 수행하지 않습니다."
        )

    # 사용자 등록 데이터가 임계치(5개 이상)을 넘어가면 클러스터링 수행
    X = np.array(raw_vectors)
    kmeans = KMeans(n_clusters=n_clusters, random_state=42)
    kmeans.fit(X)

    centroids = kmeans.cluster_centers_  # 각 클러스터의 중심 벡터
    labels = kmeans.labels_.tolist()  # 각 벡터가 어떤 클러스터에 속하는지 (0, 1, 2 등)

    # face_db에 클러스터 결과 저장
    face_db[user_id]["clusters"] = {
        "centroids": centroids.tolist(),
        "labels": labels,
    }
    print(
        f"사용자 {user_id} 클러스터링 업데이트 완료: {n_clusters}개의 클러스터 생성됨."
    )


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
                    "detected_faces": len(face_encodings),
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
        face_db[user_id].extend(encodings_list)
    else:
        face_db[user_id] = encodings_list

    new_encoding = encodings_list[0]  # 새로 등록한 얼굴 벡터

    # 기존 얼굴 데이터와 유사도 비교
    similarity_results = []
    for existing_user_id, saved_encodings in face_db.items():
        distances = face_recognition.face_distance(saved_encodings, new_encoding)
        min_distance = float(np.min(distances))
        similarity_results.append(
            {"user_id": existing_user_id, "min_distance": min_distance}
        )

    # 얼굴 벡터를 파일로 저장 (나중에 서버를 재시작해도 얼굴 데이터가 유지됨) - 임시
    save_path = os.path.join(FACE_DATA_DIR, f"face_{user_id}.pkl")
    with open(save_path, "wb") as f:
        pickle.dump(face_db[user_id], f)  # 리스트 전체 저장

    return {
        "message": f"{user_id}번 사용자의 얼굴 {len(files)}개 중 {len(encodings_list)}개 등록 완료!",
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
        for user_id, known_encodings in face_db.items():
            for known_encoding in known_encodings:
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
