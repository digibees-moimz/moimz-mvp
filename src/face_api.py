from fastapi import APIRouter, UploadFile, File
import face_recognition
import numpy as np
import pickle
import cv2

router = APIRouter()

# 얼굴 데이터 저장 - 임시
face_db = {}


# 얼굴 등록 API (파일 업로드 필수)
@router.post("/register_face/{user_id}")
async def register_face(user_id: int, file: UploadFile = File(...)):
    image_bytes = await file.read()  # 파일을 바이트로 읽기
    image_np = np.frombuffer(image_bytes, np.uint8)  # 바이트를 NumPy 배열로 변환
    image = cv2.imdecode(image_np, cv2.IMREAD_COLOR)  # OpenCV 형식으로 변환

    # 얼굴 인식 및 특징 벡터 추출
    face_encodings = face_recognition.face_encodings(image)
    if not face_encodings:
        return {"error": "얼굴을 찾을 수 없습니다."}

    # 얼굴 벡터를 파일로 저장 (나중에 서버를 재시작해도 얼굴 데이터가 유지됨) - 임시
    face_db[user_id] = face_encodings[0]
    with open(f"face_{user_id}.pkl", "wb") as f:
        pickle.dump(face_encodings[0], f)

    return {"message": f"{user_id} 얼굴 등록 완료!"}
