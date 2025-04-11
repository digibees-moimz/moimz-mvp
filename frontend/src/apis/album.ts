import axios from "axios";

export interface Album {
  album_id: string;
  title: string;
  type: string;
  count: number;
  thumbnail: {
    url: string;
    file_name: string;
  };
}

// API base 설정
const api = axios.create({
  baseURL: "http://localhost:8000", // FastAPI 주소
});

// 앨범 리스트 가져오기
export const fetchAlbums = async (): Promise<Album[]> => {
  const res = await api.get("/album/albums");
  return res.data.albums;
};
