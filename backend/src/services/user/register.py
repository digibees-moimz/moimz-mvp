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


# 데이터 증강 로직
def augment_image(image: np.ndarray, use_flip=False) -> list:
    aug_images = [image]

    # 밝기 증가
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    hsv[:, :, 2] = np.clip(hsv[:, :, 2] * 1.2, 0, 255)
    bright = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
    aug_images.append(bright)

    # 약한 블러
    blurred = cv2.GaussianBlur(image, (5, 5), 0)
    aug_images.append(blurred)

    # 회전 ±20도
    h, w = image.shape[:2]
    for angle in [-20, 20]:
        M = cv2.getRotationMatrix2D((w // 2, h // 2), angle, 1.0)
        rotated = cv2.warpAffine(image, M, (w, h))
        aug_images.append(rotated)

    # 노이즈 추가
    noise = np.random.normal(0, 10, image.shape).astype(np.uint8)
    noisy = cv2.add(image, noise)
    aug_images.append(noisy)

    return aug_images
