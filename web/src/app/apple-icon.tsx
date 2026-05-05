import { ImageResponse } from "next/og";

export const size = { width: 180, height: 180 };
export const contentType = "image/png";

export default function AppleIcon() {
  return new ImageResponse(
    (
      <div
        style={{
          width: 180,
          height: 180,
          borderRadius: 40,
          background: "#0f172a",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <svg
          width="130"
          height="130"
          viewBox="0 0 64 64"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            d="M12 44 L22 28 L32 36 L42 20 L52 12"
            stroke="#00e6e6"
            strokeWidth="4"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          <path
            d="M12 44 L22 28 L32 36 L42 20 L52 12 L52 44 Z"
            fill="#00e6e6"
            opacity="0.12"
          />
          <circle cx="52" cy="12" r="5" fill="#22c55e" />
          <circle cx="42" cy="20" r="3.5" fill="#00e6e6" />
          <circle cx="32" cy="36" r="3.5" fill="#00e6e6" />
          <circle cx="22" cy="28" r="3.5" fill="#00e6e6" />
        </svg>
      </div>
    ),
    { ...size },
  );
}
