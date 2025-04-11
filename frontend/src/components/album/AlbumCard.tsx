interface AlbumCardProps {
  title: string;
  count: number;
  thumbnailUrl: string;
}

export const AlbumCard: React.FC<AlbumCardProps> = ({
  title,
  count,
  thumbnailUrl,
}) => {
  return (
    <div className="bg-white border rounded-lg shadow-md overflow-hidden">
      <div className="p-4">
        <h3 className="text-lg font-medium text-gray-900">{title}</h3>
        <p className="text-gray-500">{count}개의 사진</p>
        {thumbnailUrl && (
          <img
            src={thumbnailUrl}
            alt={title}
            className="mt-4 w-full h-48 object-cover"
          />
        )}
      </div>
    </div>
  );
};
