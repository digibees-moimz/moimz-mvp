import os

import cv2
import numpy as np
import uuid
import face_recognition
import random


# 업로드 영상에서 프레임 추출
def extract_frames_from_video(video_bytes, interval=10):
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
    hsv[:, :, 2] = np.clip(hsv[:, :, 2] * 1.3, 0, 255)
    bright = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
    aug_images.append(bright)

    # 밝기 감소
    hsv_dark = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    hsv_dark[:, :, 2] = np.clip(hsv_dark[:, :, 2] * 0.6, 0, 255)
    darker = cv2.cvtColor(hsv_dark, cv2.COLOR_HSV2BGR)
    aug_images.append(darker)

    # 약한 블러
    blurred = cv2.GaussianBlur(image, (7, 7), 0)
    aug_images.append(blurred)

    # 회전 ±20도
    h, w = image.shape[:2]
    for angle in [-20, 20]:
        M = cv2.getRotationMatrix2D((w // 2, h // 2), angle, 1.0)
        rotated = cv2.warpAffine(image, M, (w, h))
        aug_images.append(rotated)

    # 노이즈 추가
    noise = np.random.normal(0, 1, image.shape).astype(np.uint8)
    noisy = cv2.add(image, noise)
    aug_images.append(noisy)

    # 얼굴 랜드마크 기반 가리기
    res = occlusion_augment(image)
    aug_images.extend(res)

    return aug_images


# 얼굴 랜드마크 기반 특정 부위(eyes, nose, mouth, chin, forehead 등)에 가림 효과 적용
def apply_occlusion(image: np.ndarray, landmarks: dict, region: str) -> np.ndarray:
    masked = image.copy()

    if region == "mask" and all(
        k in landmarks for k in ["top_lip", "chin", "nose_tip"]
    ):
        # 윗선 y 기준 (콧망울 위)
        nose_top_y = min(landmarks["nose_tip"], key=lambda p: p[1])[1]
        y1 = nose_top_y - 10

        # 마스크 중앙 x 기준
        top_lip = landmarks["top_lip"]
        mouth_center_x = int(np.mean([pt[0] for pt in top_lip]))
        x1 = mouth_center_x - 70
        x2 = mouth_center_x + 70

        # 윗 라인
        upper_line = [(x1, y1), (x2, y1)]

        # 턱 곡선 (반대방향으로 안전하게)
        chin = landmarks["chin"]
        chin_curve = chin[::-1]  # 왼쪽 → 오른쪽

        # 마스크 경로 구성
        path = upper_line + chin_curve
        mask_poly = np.array([path], dtype=np.int32)

        # 마스크 생성
        h, w = masked.shape[:2]
        mask = np.zeros((h, w), dtype=np.uint8)
        cv2.fillPoly(mask, [mask_poly], 255)
        mask = cv2.GaussianBlur(mask, (5, 5), 0)

        # 컬러 fill + blend
        fill_color = np.zeros_like(masked)
        fill_color[:] = (255, 255, 255)
        mask_3ch = cv2.merge([mask] * 3)
        alpha = mask_3ch.astype(np.float32) / 255.0
        masked = (masked * (1 - alpha) + fill_color * alpha).astype(np.uint8)

        return masked

    elif (
        region == "sunglasses" and "left_eye" in landmarks and "right_eye" in landmarks
    ):
        # 눈 부위 가리기
        eyes = landmarks["left_eye"] + landmarks["right_eye"]
        x_coords, y_coords = zip(*eyes)
        x1, y1 = min(x_coords) - 10, min(y_coords) - 15
        x2, y2 = max(x_coords) + 10, max(y_coords) + 15

        return apply_random_effect(masked, x1, y1, x2, y2, color=(30, 30, 30))

    elif (
        region == "hat" and "left_eyebrow" in landmarks and "right_eyebrow" in landmarks
    ):
        # 이마 위쪽 영역 가리기
        brows = landmarks["left_eyebrow"] + landmarks["right_eyebrow"]
        x_coords, y_coords = zip(*brows)
        x1, y1 = min(x_coords) - 10, min(y_coords) - 60
        x2, y2 = max(x_coords) + 10, min(y_coords) - 10
        y1 = max(0, y1)
        cv2.rectangle(masked, (x1, y1), (x2, y2), (40, 40, 40), -1)

    elif region == "hand" and "chin" in landmarks:
        # 턱/입 부분 가리기 (손 또는 핸드폰 가정)
        chin = landmarks["chin"]
        x_coords, y_coords = zip(*chin)
        x1 = min(x_coords)
        x2 = max(x_coords)

        # 아래쪽 1/3만 가리기
        y_mid = int(np.mean(y_coords))
        y2 = max(y_coords)
        y1 = y_mid + (y2 - y_mid) // 2  # 아래쪽 일부

        # 랜덤 효과 선택
        return apply_random_effect(masked, x1, y1, x2, y2, color=(60, 60, 60))

    return masked


# 증강 적용 함수
def occlusion_augment(
    image: np.ndarray, region_list=["mask", "sunglasses", "hat", "hand"]
):
    augmented = []
    landmark_list = face_recognition.face_landmarks(image)
    if not landmark_list:
        return []

    landmarks = landmark_list[0]  # 첫 번째 얼굴 기준

    for region in region_list:
        masked = apply_occlusion(image, landmarks, region)
        augmented.append(masked)

    return augmented


# 랜덤 효과 선택
def apply_random_effect(
    image: np.ndarray, x1: int, y1: int, x2: int, y2: int, color=(50, 50, 50)
) -> np.ndarray:
    effect = random.choice(["rectangle", "blur", "noise"])

    if effect == "rectangle":
        cv2.rectangle(image, (x1, y1), (x2, y2), color, -1)
    elif effect == "blur":
        roi = image[y1:y2, x1:x2]
        blurred = cv2.GaussianBlur(roi, (31, 31), 0)
        image[y1:y2, x1:x2] = blurred
    elif effect == "noise":
        roi = image[y1:y2, x1:x2]
        noise = np.random.normal(0, 30, roi.shape).astype(np.uint8)
        noised = cv2.add(roi, noise)
        image[y1:y2, x1:x2] = noised

    return image
