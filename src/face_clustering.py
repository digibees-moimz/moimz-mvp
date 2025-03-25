from sklearn.cluster import KMeans
import numpy as np
from typing import Dict, Any


# 클러스터링 업데이트 함수 - threshold: 임계치, n_clusters: 클러스터의 개수(k)
def update_user_clusters(
    face_db: Dict[int, Dict[str, Any]],
    user_id: int,
    threshold: int = 5,
    n_clusters: int = 3,
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
