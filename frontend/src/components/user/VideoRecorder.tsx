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

  type StepType = "front" | "left" | "right" | "smile" | "";

  const [step, setStep] = useState<StepType>("");
  const [stepMessage, setStepMessage] =
    useState("얼굴을 화면 중앙에 맞춰주세요");

  const steps: { step: StepType; msg: string }[] = [
    { step: "front", msg: "정면을 바라봐 주세요" },
    { step: "left", msg: "천천히 왼쪽으로 얼굴을 돌려주세요" },
    { step: "front", msg: "다시 정면을 바라봐 주세요" },
    { step: "right", msg: "천천히 오른쪽으로 얼굴을 돌려주세요" },
    { step: "smile", msg: "정면을 보며 환하게 웃어주세요!" },
  ];

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
    if (!mediaRecorderRef.current) return;

    console.log("🎬 녹화 시작");
    setRecording(true);
    mediaRecorderRef.current.start();

    steps.forEach((s, i) => {
      setTimeout(() => {
        setStep(s.step);
        setStepMessage(s.msg);
      }, i * 3000);
    });

    setTimeout(() => {
      mediaRecorderRef.current?.stop();
      console.log("🛑 녹화 종료");
      setRecording(false);
    }, steps.length * 3000);
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

      <div className="absolute top-[220px] w-full left-1/2 -translate-x-1/2 text-xl font-bold z-20 text-center">
        {step === "left" && (
          <span className="animate-arrow-left text-3xl">⬅︎ </span>
        )}
        <span>{stepMessage}</span>
        {step === "right" && (
          <span className="animate-arrow-right text-3xl">➡︎ </span>
        )}
      </div>

      <div className="absolute top-[45%] left-1/2 -translate-x-1/2 -translate-y-1/2 opacity-90">
        <div className="w-[65vw] max-w-[300px] aspect-square rounded-full border-2 border-dashed border-white flex justify-center items-center text-white font-bold text-xl text-center">
          {!recording && (
            <p>
              얼굴을 화면 중앙에 <br />
              맞춰주세요
            </p>
          )}
        </div>
      </div>

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
