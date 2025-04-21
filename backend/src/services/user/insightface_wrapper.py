import insightface
import numpy as np
import cv2


class FaceEngine:
    def __init__(self):
        # InsightFace 모델 로드 (buffalo_l은 정확도 높은 모델)
        self.model = insightface.app.FaceAnalysis(
            name="buffalo_l", providers=["CPUExecutionProvider"]
        )
        self.model.prepare(ctx_id=0)

    # 얼굴 전체 정보 (bbox + landmarks + embedding) 반환
    def get_faces(self, image: np.ndarray):
        if image is None:
            return []
        # OpenCV의 BGR 이미지를 RGB로 변환 (InsightFace는 RGB 이미지 사용)
        if image.shape[2] == 3:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        return self.model.get(image)

    #  얼굴 벡터 추출
    def get_embedding(self, face) -> np.ndarray:
        return face.embedding

    # 얼굴 위치 좌표 (x1, y1, x2, y2) 반환
    def get_bbox(self, face) -> list:
        return face.bbox

    # 5개 랜드마크(양쪽 눈, 코, 입 좌우) 반환
    def get_landmarks(self, face):
        return face.kps

    # 임베딩 벡터 간 코사인 유사도 계산
    def cosine_similarity(self, a, b):
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

    # 얼굴 영역만 크롭
    def crop_face(self, image: np.ndarray, face) -> np.ndarray:
        x1, y1, x2, y2 = map(int, face.bbox)
        return image[y1:y2, x1:x2]


# 전역 인스턴스
face_engine = FaceEngine()
