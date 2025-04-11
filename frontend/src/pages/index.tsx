import Link from "next/link";

export default function Home() {
  return (
    <main className="p-8">
      <h1 className="text-2xl font-bold mb-4">홈페이지</h1>

      <Link href="/album">
        <button className="px-4 py-2 bg-emerald-500 text-white rounded">
          인물별 앨범 보러가기
        </button>
      </Link>
    </main>
  );
}
