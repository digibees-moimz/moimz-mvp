import dynamic from "next/dynamic";

import { useRouter } from "next/router";
const VideoRecorder = dynamic(() => import("@/components/user/VideoRecorder"), {
  ssr: false,
});

export default function RegisterPage() {
  const router = useRouter();
  const { userId } = router.query;

  // 아직 라우팅이 안 됐을 수도 있으므로 체크
  if (!userId) return <div>로딩 중...</div>;

  return (
    <main className="flex flex-col items-center justify-center">
      <VideoRecorder userId={userId as string} />
    </main>
  );
}
