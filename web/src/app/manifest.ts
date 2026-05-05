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
        src: "/icon",
        sizes: "32x32",
        type: "image/png",
      },
      {
        src: "/apple-icon",
        sizes: "180x180",
        type: "image/png",
      },
      {
        src: "/apple-icon",
        sizes: "180x180",
        type: "image/png",
        purpose: "maskable",
      },
    ],
  };
}
