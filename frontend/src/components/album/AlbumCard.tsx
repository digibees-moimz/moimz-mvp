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
    <div>
      <div className="bg-white h-25 rounded-lg shadow-md overflow-hidden">
        <div className="w-full h-40 relative">
          {thumbnailUrl && (
            <img
              src={thumbnailUrl}
              alt={title}
              className="mb-2 w-full h-25 object-cover"
            />
          )}
        </div>
      </div>
      <div className="p-1 leading-tight">
        <h3 className="text-m font-medium text-gray-900">{title}</h3>
        {count > 0 && <p className="text-xs text-gray-400">{count}</p>}
      </div>
    </div>
  );
};
