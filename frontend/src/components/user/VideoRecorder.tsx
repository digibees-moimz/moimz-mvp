"use client";

import React, { useRef, useState } from "react";

interface Props {
  userId: string;
}

export default function VideoRecorder({ userId }: Props) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const [recording, setRecording] = useState(false);
  const [videoBlob, setVideoBlob] = useState<Blob | null>(null);
  const [isCameraReady, setIsCameraReady] = useState(false);

  const startCamera = async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ video: true });

    if (videoRef.current) {
      videoRef.current.srcObject = stream;
    }

    // MIME 타입 브라우저별 fallback 처리
    const mimeType = MediaRecorder.isTypeSupported("video/webm;codecs=vp9")
      ? "video/webm;codecs=vp9"
      : MediaRecorder.isTypeSupported("video/webm;codecs=vp8")
      ? "video/webm;codecs=vp8"
      : "";

    const recorder = new MediaRecorder(stream);
    const chunks: Blob[] = [];

    // 녹화 중 생성된 데이터 수신
    recorder.ondataavailable = (e) => {
      console.log("📦 ondataavailable fired");
      chunks.push(e.data);
    };

    // 녹화 종료 시 최종 blob 저장
    recorder.onstop = () => {
      console.log("✅ onstop fired");
      const fullBlob = new Blob(chunks, { type: mimeType || "video/webm" });
      setVideoBlob(fullBlob);
      console.log("🎥 녹화된 blob:", fullBlob);
    };

    mediaRecorderRef.current = recorder;
    setIsCameraReady(true);
  };

  const startRecording = () => {
    if (!mediaRecorderRef.current) {
      alert("카메라를 먼저 시작해주세요!");
      return;
    }

    console.log("🎬 녹화 시작");
    setRecording(true);
    mediaRecorderRef.current.start();

    setTimeout(() => {
      mediaRecorderRef.current?.stop();
      console.log("🛑 녹화 종료");
      setRecording(false);
    }, 5000);
  };

  const uploadVideo = async () => {
    if (!videoBlob) return;

    const formData = new FormData();
    formData.append("file", videoBlob, "video.webm");

    const response = await fetch(
      `http://localhost:8000/faces/register_video/${userId}`,
      {
        method: "POST",
        body: formData,
      }
    );

    const result = await response.json();
    console.log("📤 업로드 결과:", result);
    alert("서버 응답: " + JSON.stringify(result));
  };

  return (
    <div className="w-screen h-screen flex flex-col items-center justify-center bg-black relative overflow-hidden">
      <video
        ref={videoRef}
        autoPlay
        playsInline
        muted
        className="aspect-9/16 top-0 left-0 w-full border shadow-lg object-cover bg-black transform scale-x-[-1]"
      />

      {/* 버튼 영역 */}
      <div className="absolute bottom-6 flex gap-4 z-10">
        <button
          onClick={startCamera}
          className="bg-blue-500 text-white px-4 py-2 rounded"
        >
          📷 카메라 시작
        </button>
        <button
          onClick={startRecording}
          disabled={!isCameraReady || recording}
          className="bg-red-500 text-white px-4 py-2 rounded"
        >
          🔴 녹화
        </button>
        <button
          onClick={uploadVideo}
          disabled={!videoBlob}
          className="bg-green-600 text-white px-4 py-2 rounded"
        >
          📤 업로드
        </button>
      </div>
    </div>
  );
}
