import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 얼굴 등록 + 출석체크
FACE_DATA_DIR = os.path.join(BASE_DIR, "src", "data", "users")
os.makedirs(FACE_DATA_DIR, exist_ok=True)

# 사용자 정보
USER_INFO_PATH = os.path.join(FACE_DATA_DIR, "users.json")

FRAME_IMAGE_DIR = os.path.join("src", "data", "frames")
AUG_IMAGE_DIR = os.path.join("src", "data", "augmented")

# 인물별 앨범
MIN_FACE_COUNT = 5
ALBUM_DIR = os.path.join(BASE_DIR, "src", "data", "album")
os.makedirs(ALBUM_DIR, exist_ok=True)

ENCODING_PATH = os.path.join(ALBUM_DIR, "face_encodings.npy")
METADATA_PATH = os.path.join(ALBUM_DIR, "face_data.json")
REPRESENTATIVES_PATH = os.path.join(ALBUM_DIR, "representatives.json")
TEMP_CLUSTER_PATH = os.path.join(ALBUM_DIR, "temp_cluster_result.json")
TEMP_ENCODING_PATH = os.path.join(ALBUM_DIR, "temp_encodings.json")
IMAGE_HASH_PATH = os.path.join(ALBUM_DIR, "image_hashes.json")

RECENT_VECTOR_COUNT = 10

# threshold 값
MATCH_THRESHOLD_ALBUM = 0.45
MATCH_THRESHOLD_ATTENDANCE = 0.43
