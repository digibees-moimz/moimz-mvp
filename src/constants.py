import os

ALBUM_DIR = os.path.join("src", "data", "album")
os.makedirs(ALBUM_DIR, exist_ok=True)

ENCODING_PATH = os.path.join(ALBUM_DIR, "face_encodings.npy")
METADATA_PATH = os.path.join(ALBUM_DIR, "face_data.json")
REPRESENTATIVES_PATH = os.path.join(ALBUM_DIR, "representatives.json")
TEMP_CLUSTER_PATH = os.path.join(ALBUM_DIR, "temp_cluster_result.json")
TEMP_ENCODING_PATH = os.path.join(ALBUM_DIR, "temp_encodings.json")
