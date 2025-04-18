import io
from typing import Dict, Any

import matplotlib.pyplot as plt
import numpy as np
from fastapi.responses import StreamingResponse
from sklearn.cluster import KMeans
from sklearn.manifold import TSNE


# plt.style.use("seaborn")  # 스타일 지정


# 클러스터링 업데이트 함수
def update_user_clusters(
    face_db: Dict[int, Dict[str, Any]],
    user_id: int,
    threshold: int = 5,  # 클러스터링에 필요한 최소 데이터 수(임계치)
    n_clusters: int = 4,  # 클러스터의 개수(k)
):

    # 사용자 원본 벡터 리스트(raw 데이터) 가져오기
    user_data = face_db.get(user_id)

    if not user_data or "raw" not in user_data:
        return f"사용자 {user_id}의 raw 데이터가 없습니다."

    raw_vectors = user_data["raw"]
    if len(raw_vectors) < threshold:
        return f"사용자 {user_id}의 raw 벡터 수가 {threshold}개 미만이므로 클러스터링을 수행하지 않습니다."

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
    return (
        f"사용자 {user_id} 클러스터링 업데이트 완료: {n_clusters}개의 클러스터 생성됨."
    )


# 클러스터링 시각화
def visualize_clusters(face_db, user_id):
    user_data = face_db.get(user_id)
    if not user_data or "clusters" not in user_data or "raw" not in user_data:
        return "클러스터링 결과를 시각화할 데이터가 부족합니다."

    raw_vectors = np.array(user_data["raw"])
    labels = np.array(user_data["clusters"]["labels"])
    centroids = np.array(user_data["clusters"]["centroids"])

    # 원본 얼굴 벡터와 클러스터 중심을 하나의 배열로 결합(같은 2D 공간에 시각화)
    combined = np.concatenate([raw_vectors, centroids], axis=0)

    perplexity = max(2, min(30, (len(combined) - 1) // 3))
    # 2차원으로 축소할 t-SNE 객체 생성
    tsne = TSNE(n_components=2, random_state=42, perplexity=perplexity)
    # 결합된 고차원 데이터를 2차원으로 투영
    combined_embedded = tsne.fit_transform(combined)

    # t-SNE 결과 분리
    raw_embedded = combined_embedded[: len(raw_vectors)]
    centroids_embedded = combined_embedded[len(raw_vectors) :]

    # 시각화
    plt.figure(figsize=(8, 6))  # 시각화 창의 크기

    scatter = plt.scatter(
        raw_embedded[:, 0],
        raw_embedded[:, 1],
        c=labels,  # 군집 레이블에 따라 색상 분류
        cmap="viridis",  # 색상 맵 (다른 것: "plasma", "Accent", "Dark2" 등)
        s=50,  # 마커 크기
        label="face vectors",
        alpha=0.9,  # 투명도 (0~1)
        edgecolors="k",  # 마커 테두리 색
        marker="o",  # 마커 모양 (o, ^, s, x 등)
    )
    plt.scatter(
        centroids_embedded[:, 0],
        centroids_embedded[:, 1],
        color="red",
        alpha=0.1,  # 투명도 (0~1)
        marker="o",
        s=200,
        label="Centroids",
    )
    plt.title(f"User {user_id} Clusters")
    plt.xlabel("t-SNE 1")
    plt.ylabel("t-SNE 2")
    plt.legend()
    # plt.show()

    # 이미지 버퍼에 저장하고 StreamingResponse로 반환
    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    plt.close()  # 플롯 닫기
    buf.seek(0)
    return StreamingResponse(buf, media_type="image/png")
