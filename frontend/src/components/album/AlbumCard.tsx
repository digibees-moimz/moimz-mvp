import Link from "next/link";

interface AlbumCardProps {
  album_id: string;
  title: string;
  count: number;
  thumbnailUrl: string;
}

export const AlbumCard: React.FC<AlbumCardProps> = ({
  album_id,
  title,
  count,
  thumbnailUrl,
}) => {
  return (
    <Link href={`/albums/${album_id}`}>
      <div className="cursor-pointer">
        <div className="bg-white h-34 rounded-lg shadow-md overflow-hidden">
          <div className="w-full h-34 relative">
            <img
              alt={title}
              className="mb-2 w-full h-34 object-cover object-top"
              src={
                thumbnailUrl
                  ? `http://localhost:8000/album${thumbnailUrl}`
                  : "/icons/icon-512x512.png"
              }
            />
          </div>
        </div>
        <div className="p-1 leading-tight">
          <h3 className="text-m font-medium text-gray-900">{title}</h3>
          {count > 0 && <p className="text-xs text-gray-400">{count}</p>}
        </div>
      </div>
    </Link>
  );
};
