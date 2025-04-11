// 인물별 앨범 페이지
import { useEffect, useState } from "react";
import { fetchAlbums, Album } from "@/apis/album";

export default function AlbumPage() {
  const [albums, setAlbums] = useState<Album[]>([]);

  useEffect(() => {
    fetchAlbums()
      .then(setAlbums)
      .catch((err) => console.error("앨범 가져오기 실패:", err));
  }, []);
  return (
    <>
      <div className="p-8">
        <h1 className="text-3xl font-semibold text-center mb-8">앨범 목록</h1>
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
          {albums.map((album) => (
            <div
              key={album.album_id}
              className="bg-white border rounded-lg shadow-md overflow-hidden"
            >
              <div className="p-4">
                <h3 className="text-lg font-medium text-gray-900">
                  {album.title}
                </h3>
                <p className="text-gray-500">{album.count}개의 사진</p>
                {album.thumbnail.url && (
                  <img
                    src={album.thumbnail.url}
                    alt={album.title}
                    className="mt-4 w-full h-48 object-cover"
                  />
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </>
  );
}
