import { useEffect } from "react";
import Head from "next/head";
import "@/styles/globals.css";
import type { AppProps } from "next/app";

export default function App({ Component, pageProps }: AppProps) {
  useEffect(() => {
    window.addEventListener("beforeinstallprompt", (e) => {
      console.log("📦 PWA 설치 가능!", e);
    });
  }, []);

  useEffect(() => {
    if ("serviceWorker" in navigator) {
      window.addEventListener("load", () => {
        navigator.serviceWorker
          .register("/sw.js")
          .then((reg) => {
            console.log("🧙‍♂️ Service worker registered!", reg);
          })
          .catch((err) => {
            console.error("❌ SW registration failed:", err);
          });
      });
    }
  }, []);

  return (
    <>
      <Component {...pageProps} />
    </>
  );
}
