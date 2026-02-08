"use client";

export default function AnimatedBackground() {
  return (
    <div className="fixed inset-0 -z-10 overflow-hidden">
      {/* Base background */}
      <div className="absolute inset-0 bg-[#0a0e1a]" />

      {/* Gradient orbs */}
      <div
        className="absolute -top-[40%] -left-[20%] w-[60%] h-[60%] rounded-full opacity-20 animate-gradient-shift"
        style={{
          background:
            "radial-gradient(circle, rgba(59,130,246,0.4) 0%, transparent 70%)",
        }}
      />
      <div
        className="absolute -bottom-[30%] -right-[20%] w-[50%] h-[50%] rounded-full opacity-15 animate-gradient-shift"
        style={{
          background:
            "radial-gradient(circle, rgba(139,92,246,0.4) 0%, transparent 70%)",
          animationDelay: "5s",
        }}
      />
      <div
        className="absolute top-[20%] right-[10%] w-[30%] h-[30%] rounded-full opacity-10 animate-gradient-shift"
        style={{
          background:
            "radial-gradient(circle, rgba(59,130,246,0.3) 0%, transparent 70%)",
          animationDelay: "10s",
        }}
      />

      {/* Subtle grid overlay */}
      <div
        className="absolute inset-0 opacity-[0.03]"
        style={{
          backgroundImage: `
            linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px),
            linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)
          `,
          backgroundSize: "60px 60px",
        }}
      />
    </div>
  );
}
