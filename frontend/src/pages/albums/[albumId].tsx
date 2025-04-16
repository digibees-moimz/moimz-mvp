import { useRouter } from "next/router";
import { useEffect, useState } from "react";
import { fetchAlbumDetail, PhotoList } from "@/apis/album";

export default function AlbumDetailPage() {
  const router = useRouter();
  const { albumId } = router.query;

  const [faces, setFaces] = useState<PhotoList[]>([]);

  useEffect(() => {
    if (!albumId) return;

    fetchAlbumDetail(albumId as string)
      .then((data) => {
        setFaces(data);
      })
      .catch((err) => {
        console.error(err);
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
            className="rounded-md h-25 w-25 object-cover object-top"
          />
        ))}
      </div>
    </div>
  );
}
