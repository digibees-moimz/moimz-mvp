import os
import pickle

from src.constants import FACE_DATA_DIR

# 얼굴 데이터 저장소
face_db = {}


# 장된 얼굴 벡터 파일 불러오기
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
