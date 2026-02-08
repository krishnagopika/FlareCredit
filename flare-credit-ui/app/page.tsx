"use client";

import { ConnectButton } from "@rainbow-me/rainbowkit";
import { useAccount } from "wagmi";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { motion } from "framer-motion";
import FlareCreditLogo from "@/components/FlareCreditLogo";

const fadeUp = {
  hidden: { opacity: 0, y: 30 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.15, duration: 0.6, ease: "easeOut" as const },
  }),
};

export default function Landing() {
  const { isConnected } = useAccount();
  const router = useRouter();

  useEffect(() => {
    if (isConnected) {
      router.push("/dashboard");
    }
  }, [isConnected, router]);

  return (
    <main className="relative flex min-h-screen flex-col items-center justify-center gap-8 px-4">
      {/* Hero */}
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.7, ease: "easeOut" }}
      >
        <FlareCreditLogo size="lg" />
      </motion.div>

      <motion.p
        className="text-lg md:text-xl text-slate-400 text-center max-w-md"
        variants={fadeUp}
        initial="hidden"
        animate="visible"
        custom={1}
      >
        Unlock lower collateral loans using verifiable credit data.
      </motion.p>

      <motion.div
        variants={fadeUp}
        initial="hidden"
        animate="visible"
        custom={2}
      >
        <ConnectButton />
      </motion.div>
    </main>
  );
}
