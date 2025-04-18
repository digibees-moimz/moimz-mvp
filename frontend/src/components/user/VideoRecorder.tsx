"use client";

import React, { useRef, useState, useEffect } from "react";

interface Props {
  userId: string;
}

export default function VideoRecorder({ userId }: Props) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const [recording, setRecording] = useState(false);
  const [isCameraReady, setIsCameraReady] = useState(false);
  const [isUploading, setIsUploading] = useState(false);

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
      chunks.push(e.data);
    };

    // 녹화 종료 시 최종 blob 저장
    recorder.onstop = () => {
      const fullBlob = new Blob(chunks, { type: mimeType || "video/webm" });

      // 녹화 종료 시 자동 업로드
      uploadVideo(fullBlob);
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

  const uploadVideo = async (blob?: Blob) => {
    const videoToUpload = blob;
    if (!videoToUpload || isUploading) return;

    setIsUploading(true);
    const formData = new FormData();
    formData.append("file", videoToUpload, "video.webm");

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
    setIsUploading(false);
  };

  useEffect(() => {
    startCamera();
  }, []);

  return (
    <div className="w-screen h-screen flex flex-col items-center justify-center bg-black relative overflow-hidden">
      {isUploading && (
        <div className="absolute inset-0 bg-black bg-opacity-60 flex items-center justify-center z-20">
          <div className="text-white text-xl font-semibold animate-pulse">
            ⏳ 업로드 중입니다...
          </div>
        </div>
      )}
      <video
        ref={videoRef}
        autoPlay
        playsInline
        muted
        className="aspect-12/16 top-0 left-0 w-full border shadow-lg object-cover bg-black transform scale-x-[-1]"
      />

      {/* 버튼 영역 */}
      <div className="absolute flex items-center justify-center bottom-12 left-1/2 transform -translate-x-1/2 w-18 h-18 rounded-full bg-white z-10">
        <button
          onClick={startRecording}
          disabled={!isCameraReady || recording}
          className={`w-16 h-16 rounded-full border-4 ${
            recording ? "bg-red-600 animate-pulse" : "bg-white"
          }`}
        />
      </div>
    </div>
  );
}
