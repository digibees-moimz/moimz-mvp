// 인물별 앨범 페이지
import { useEffect, useState } from "react";
import { fetchAlbums, Album } from "@/apis/album";
import { AlbumCard } from "@/components/album/AlbumCard";

export default function AlbumPage() {
  const [albums, setAlbums] = useState<Album[]>([]);

  useEffect(() => {
    fetchAlbums()
      .then((data) => {
        setAlbums(data);
        console.log("🎯 앨범 리스트", data);
      })
      .catch((err) => {
        console.error("❌ API 호출 실패:", err);
      });
  }, []);

  return (
    <>
      <div className="p-8">
        <h1 className="text-3xl font-semibold text-center my-6">모임 앨범</h1>
        <div className="py-2 text-gray-500">
          {albums.length > 0 ? (
            <div>총 {albums.length}개의 앨범</div>
          ) : (
            <div>📦 앨범 없음</div>
          )}
        </div>
        <div>
          <div className="grid grid-cols-3 lg:grid-cols-4 gap-4">
            {albums.map((album) => (
              <AlbumCard
                key={album.album_id}
                album_id={album.album_id}
                title={album.title}
                count={album.count}
                thumbnailUrl={`http://localhost:8000/album${album.thumbnail.url}`}
              />
            ))}
          </div>
        </div>
      </div>
    </>
  );
}
