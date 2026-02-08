"use client";

import { motion } from "framer-motion";

export default function FlareCreditLogo({
  size = "md",
}: {
  size?: "sm" | "md" | "lg";
}) {
  const dimensions = {
    sm: { icon: 28, text: "text-xl" },
    md: { icon: 40, text: "text-3xl" },
    lg: { icon: 64, text: "text-5xl" },
  };

  const { icon, text } = dimensions[size];

  return (
    <motion.div
      className="flex items-center gap-3"
      whileHover={{ scale: 1.03 }}
      transition={{ type: "spring", stiffness: 300 }}
    >
      {/* Flame SVG */}
      <svg
        width={icon}
        height={icon}
        viewBox="0 0 64 64"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <defs>
          <linearGradient
            id="flameGradient"
            x1="32"
            y1="4"
            x2="32"
            y2="60"
            gradientUnits="userSpaceOnUse"
          >
            <stop stopColor="#60a5fa" />
            <stop offset="0.5" stopColor="#3b82f6" />
            <stop offset="1" stopColor="#f97316" />
          </linearGradient>
          <linearGradient
            id="innerFlame"
            x1="32"
            y1="20"
            x2="32"
            y2="58"
            gradientUnits="userSpaceOnUse"
          >
            <stop stopColor="#93c5fd" />
            <stop offset="1" stopColor="#fb923c" />
          </linearGradient>
        </defs>
        {/* Outer flame */}
        <path
          d="M32 4C32 4 18 20 18 36C18 44.837 24.268 52 32 56C39.732 52 46 44.837 46 36C46 20 32 4 32 4Z"
          fill="url(#flameGradient)"
          opacity="0.9"
        />
        {/* Inner flame */}
        <path
          d="M32 20C32 20 25 30 25 38C25 43.523 28.134 48 32 50C35.866 48 39 43.523 39 38C39 30 32 20 32 20Z"
          fill="url(#innerFlame)"
          opacity="0.8"
        />
        {/* Core glow */}
        <ellipse
          cx="32"
          cy="42"
          rx="4"
          ry="6"
          fill="white"
          opacity="0.6"
        />
      </svg>

      {/* Wordmark */}
      <span className={`${text} font-bold tracking-tight`}>
        <span className="text-white">Flare</span>
        <span className="text-gradient">Credit</span>
      </span>
    </motion.div>
  );
}
