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

export interface PhotoList {
  face_id: string;
  file_name: string;
  location: number[];
  image_url: string;
}

// API base 설정
const api = axios.create({
  baseURL: "http://localhost:8000/album", // FastAPI 주소
});

// 앨범 리스트 조회
export const fetchAlbums = async (): Promise<Album[]> => {
  const res = await api.get("/albums");
  return res.data.albums;
};

// 앨범 리스트 상세 조회
export const fetchAlbumDetail = async (albumId: string): Promise<PhotoList[]> => {
  const res = await api.get(`/albums/${albumId}`);
  return res.data.faces;
};
