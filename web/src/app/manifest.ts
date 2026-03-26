import { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "FinPilot — AI-Powered Stock Intelligence",
    short_name: "FinPilot",
    description:
      "Scans 1,500+ stocks daily with trained reinforcement learning models.",
    start_url: "/",
    display: "standalone",
    background_color: "#000000",
    theme_color: "#00d4ff",
    orientation: "portrait",
    icons: [
      {
        src: "/icon-192.png",
        sizes: "192x192",
        type: "image/png",
      },
      {
        src: "/icon-512.png",
        sizes: "512x512",
        type: "image/png",
      },
      {
        src: "/icon-512.png",
        sizes: "512x512",
        type: "image/png",
        purpose: "maskable",
      },
    ],
  };
}
