// 인물별 앨범 페이지
import { useEffect, useState } from "react";
import { fetchAlbums, Album } from "@/apis/album";

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
        <h1 className="text-3xl font-semibold text-center mb-8">모임 앨범</h1>
        <div className="py-2 text-gray-500">
          {albums.length > 0 ? (
            <div>총 {albums.length}개의 앨범</div>
          ) : (
            <div>📦 앨범 없음</div>
          )}
        </div>
        <div>
          <div className="grid grid-cols-3 lg:grid-cols-4 gap-8">
            {albums.map((album) => (
              <div>
                <div
                  key={album.album_id}
                  className="bg-white h-25 rounded-lg shadow-md overflow-hidden"
                >
                  <div className="w-full h-40 relative">
                    {album.thumbnail.url && (
                      <img
                        src={`http://localhost:8000/album${album.thumbnail.url}`}
                        alt={album.title}
                        className="mb-2 w-full h-25 object-cover"
                      />
                    )}
                  </div>
                </div>
                <div className="p-2">
                  <h3 className="text-m font-medium text-gray-900">
                    {album.title}
                  </h3>
                  <p className="text-xs text-gray-400">
                    {album.count ? album.count : 0}개의 사진
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </>
  );
}
