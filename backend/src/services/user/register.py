import os

import cv2
import numpy as np
import uuid


# 업로드 영상에서 프레임 추출
def extract_frames_from_video(video_bytes, interval=5):
    np_array = np.frombuffer(video_bytes, np.uint8)
    temp_video_path = f"temp_{uuid.uuid4().hex}.mp4"
    with open(temp_video_path, "wb") as f:
        f.write(np_array)

    cap = cv2.VideoCapture(temp_video_path)
    frames = []
    frame_count = 0

    while True:
        success, frame = cap.read()
        if not success:
            break
        if frame_count % interval == 0:
            frames.append(frame)
        frame_count += 1

    cap.release()
    os.remove(temp_video_path)
    return frames
