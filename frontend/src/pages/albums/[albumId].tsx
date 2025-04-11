import { useRouter } from "next/router";
import { useEffect, useState } from "react";
import axios from "axios";

interface Face {
  face_id: string;
  file_name: string;
  location: number[];
  image_url: string;
}

export default function AlbumDetailPage() {
  const router = useRouter();
  const { albumId } = router.query;

  const [faces, setFaces] = useState<Face[]>([]);

  useEffect(() => {
    if (!albumId || albumId === "all_photos") return; // 전체 앨범은 제외
    axios
      .get(`http://localhost:8000/album/albums/${albumId}`)
      .then((res) => {
        setFaces(res.data.faces);
      })
      .catch((err) => {
        console.error("❌ 앨범 상세 조회 실패:", err);
      });
  }, [albumId]);

  return (
    <div className="p-6">
      <h1 className="text-2xl font-semibold mb-4 text-center">{albumId}</h1>
      <div className="grid grid-cols-3 md:grid-cols-4 gap-2">
        {faces.map((face) => (
          <img
            key={face.face_id}
            src={`http://localhost:8000/album${face.image_url}`}
            alt={face.face_id}
            className="rounded-md h-32 w-32  object-cover"
          />
        ))}
      </div>
    </div>
  );
}
