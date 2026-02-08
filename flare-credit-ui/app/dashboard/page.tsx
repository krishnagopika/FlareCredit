"use client";

import { useAccount, useBalance } from "wagmi";
import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { useRouter } from "next/navigation";
import { ConnectButton } from "@rainbow-me/rainbowkit";

import {
  getCreditScore,
  processCreditScore,
  getLoanStatus,
  evaluateLoan,
} from "@/lib/api";

import {
  Card,
  CardContent,
} from "@/components/ui/card";

import { Button } from "@/components/ui/button";

import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";

import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import FlareCreditLogo from "@/components/FlareCreditLogo";

const MUSDC_ADDRESS = "0x45c7B48d002D014D0F8C8dff55045016AD28ACCB";

const stagger = {
  hidden: {},
  visible: {
    transition: { staggerChildren: 0.1 },
  },
};

const fadeUp = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.5, ease: "easeOut" as const },
  },
};

/* ---------- Credit Score Gauge ---------- */

function CreditGauge({ score }: { score: number }) {
  const max = 100;
  const pct = Math.min(score / max, 1);
  const radius = 54;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference * (1 - pct);

  const color =
    score >= 70 ? "#22c55e" : score >= 40 ? "#eab308" : "#ef4444";

  return (
    <div className="relative flex items-center justify-center">
      <svg width="140" height="140" className="-rotate-90">
        {/* Track */}
        <circle
          cx="70"
          cy="70"
          r={radius}
          fill="none"
          stroke="rgba(255,255,255,0.05)"
          strokeWidth="10"
        />
        {/* Progress */}
        <motion.circle
          cx="70"
          cy="70"
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth="10"
          strokeLinecap="round"
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset }}
          transition={{ duration: 1.2, ease: "easeOut" }}
        />
      </svg>
      <div className="absolute text-center">
        <motion.p
          className="text-3xl font-bold text-white"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
        >
          {score}
        </motion.p>
        <p className="text-xs text-slate-400">/ {max}</p>
      </div>
    </div>
  );
}

/* ---------- Stat Card ---------- */

function StatCard({
  label,
  value,
}: {
  label: string;
  value: string | number;
}) {
  return (
    <Card className="rounded-2xl glass-hover">
      <CardContent className="p-5">
        <p className="text-sm text-slate-400">{label}</p>
        <p className="text-2xl font-semibold mt-1 text-white">{value}</p>
      </CardContent>
    </Card>
  );
}

/* ---------- Dashboard ---------- */

export default function Dashboard() {
  const { address, isConnected } = useAccount();
  const router = useRouter();

  const [credit, setCredit] = useState<any>(null);
  const [loan, setLoan] = useState<any>(null);

  const [creditProcessing, setCreditProcessing] = useState(false);
  const [loanAmount, setLoanAmount] = useState("");
  const [evaluating, setEvaluating] = useState(false);

  const { data: gasBalance, isLoading: gasLoading } = useBalance({
    address,
  });

  const { data: musdcBalance, isLoading: musdcLoading } = useBalance({
    address,
    token: MUSDC_ADDRESS,
  });

  useEffect(() => {
    if (!address) return;

    const fetchLoan = async () => {
      try {
        const loanData = await getLoanStatus(address);
        setLoan(loanData);
      } catch {}
    };

    fetchLoan();
  }, [address]);

  const handleRequestScore = async () => {
    if (!address) return;

    try {
      setCreditProcessing(true);
      await processCreditScore(address);

      setTimeout(async () => {
        const score = await getCreditScore(address);
        setCredit(score);
        setCreditProcessing(false);
      }, 5000);
    } catch {
      setCreditProcessing(false);
    }
  };

  const handleEvaluateLoan = async () => {
    if (!address || !loanAmount) return;

    try {
      setEvaluating(true);
      const result = await evaluateLoan(address, Number(loanAmount));

      alert(
        result.approved
          ? `Approved! APR: ${result.adjusted_apr}%`
          : `Rejected: ${result.reason}`
      );
    } finally {
      setEvaluating(false);
    }
  };

  if (!isConnected) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <motion.div
          className="glass rounded-2xl p-8 text-center space-y-4"
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
        >
          <p className="text-slate-400 text-lg">
            Please connect your wallet to continue.
          </p>
          <button
            onClick={() => router.push("/")}
            className="btn-gradient"
          >
            Go Home
          </button>
        </motion.div>
      </div>
    );
  }

  return (
    <motion.div
      className="min-h-screen"
      variants={stagger}
      initial="hidden"
      animate="visible"
    >
      {/* Nav Bar */}
      <motion.nav
        className="glass border-b border-white/5 sticky top-0 z-40"
        variants={fadeUp}
      >
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <FlareCreditLogo size="sm" />
          <ConnectButton
            accountStatus="address"
            chainStatus="icon"
            showBalance={false}
          />
        </div>
      </motion.nav>

      <div className="max-w-6xl mx-auto px-6 py-8 space-y-8">
        {/* Account Info */}
        <motion.div variants={fadeUp}>
          <Card className="rounded-2xl glow-blue">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div className="space-y-1">
                  <h2 className="text-2xl font-semibold text-white">
                    My Wallet
                  </h2>
                  <p className="font-mono text-sm text-slate-400">
                    {address?.slice(0, 6)}...{address?.slice(-4)}
                  </p>
                </div>
                <div className="flex items-center gap-3">
                  <div className="flex items-center gap-2 glass rounded-full px-4 py-2">
                    <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
                    <span className="text-sm text-green-400 font-medium">
                      Connected
                    </span>
                  </div>
                </div>
              </div>

              <div className="mt-4 pt-4 border-t border-white/5 grid grid-cols-2 gap-4">
                <div>
                  <p className="text-xs text-slate-500 uppercase tracking-wider">
                    Gas Balance
                  </p>
                  <p className="text-lg font-semibold text-white mt-1">
                    {gasLoading
                      ? "..."
                      : `${Number(gasBalance?.formatted).toFixed(2)} C2FLR`}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-slate-500 uppercase tracking-wider">
                    Stable Balance
                  </p>
                  <p className="text-lg font-semibold text-white mt-1">
                    {musdcLoading
                      ? "..."
                      : `${Number(musdcBalance?.formatted).toLocaleString()} mUSDC`}
                  </p>
                </div>
              </div>

              <div className="mt-4 pt-4 border-t border-white/5">
                <p className="text-xs text-slate-500 uppercase tracking-wider">
                  Full Address
                </p>
                <p className="font-mono text-xs text-slate-400 mt-1 break-all">
                  {address}
                </p>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Financial Profile */}
        <motion.div variants={fadeUp}>
          <Card className="rounded-2xl">
            <CardContent className="p-6 space-y-6">
              <div>
                <h2 className="text-2xl font-semibold text-white">
                  Financial Profile
                </h2>
                <p className="text-slate-400 text-sm">
                  Live wallet balances
                </p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <StatCard
                  label="Gas Balance"
                  value={
                    gasLoading
                      ? "Loading..."
                      : `${Number(gasBalance?.formatted).toFixed(2)} C2FLR`
                  }
                />
                <StatCard
                  label="Stable Balance"
                  value={
                    musdcLoading
                      ? "Loading..."
                      : `${Number(musdcBalance?.formatted).toLocaleString()} mUSDC`
                  }
                />
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Credit Intelligence */}
        <motion.div variants={fadeUp}>
          <Card className="rounded-2xl">
            <CardContent className="p-6 space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-2xl font-semibold text-white">
                    Credit Intelligence
                  </h2>
                  <p className="text-slate-400 text-sm">
                    Agent-verified borrowing power
                  </p>
                </div>

                {credit && (
                  <Badge className="bg-green-500/20 text-green-400 border-green-500/30">
                    Verified
                  </Badge>
                )}
              </div>

              {!credit ? (
                <motion.button
                  onClick={handleRequestScore}
                  disabled={creditProcessing}
                  className="btn-gradient w-full disabled:opacity-50 disabled:cursor-not-allowed"
                  whileHover={{ scale: creditProcessing ? 1 : 1.02 }}
                  whileTap={{ scale: creditProcessing ? 1 : 0.98 }}
                >
                  {creditProcessing ? (
                    <span className="flex items-center justify-center gap-2">
                      <svg
                        className="animate-spin h-5 w-5"
                        viewBox="0 0 24 24"
                      >
                        <circle
                          className="opacity-25"
                          cx="12"
                          cy="12"
                          r="10"
                          stroke="currentColor"
                          strokeWidth="4"
                          fill="none"
                        />
                        <path
                          className="opacity-75"
                          fill="currentColor"
                          d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"
                        />
                      </svg>
                      Running credit agents...
                    </span>
                  ) : (
                    "Request Credit Score"
                  )}
                </motion.button>
              ) : (
                <motion.div
                  className="space-y-6"
                  variants={stagger}
                  initial="hidden"
                  animate="visible"
                >
                  {/* Gauge */}
                  <motion.div
                    className="flex justify-center"
                    variants={fadeUp}
                  >
                    <CreditGauge
                      score={credit.combined_risk_score}
                    />
                  </motion.div>

                  <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                    <motion.div variants={fadeUp}>
                      <StatCard
                        label="TradFi Score"
                        value={credit.tradfi_score}
                      />
                    </motion.div>
                    <motion.div variants={fadeUp}>
                      <StatCard
                        label="Onchain Score"
                        value={credit.onchain_score}
                      />
                    </motion.div>
                    <motion.div variants={fadeUp}>
                      <StatCard
                        label="Risk Score"
                        value={credit.combined_risk_score}
                      />
                    </motion.div>
                    <motion.div variants={fadeUp}>
                      <StatCard
                        label="Max Borrow"
                        value={`${Number(credit.max_borrow_amount) / 1e18} mUSDC`}
                      />
                    </motion.div>
                    <motion.div variants={fadeUp}>
                      <StatCard
                        label="APR"
                        value={`${credit.apr}%`}
                      />
                    </motion.div>
                  </div>
                </motion.div>
              )}

              {/* Apply for Loan */}
              {credit && (
                <Dialog>
                  <DialogTrigger asChild>
                    <motion.button
                      className="btn-gradient w-full"
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                    >
                      Apply For Loan
                    </motion.button>
                  </DialogTrigger>

                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle className="text-white">
                        Request Loan
                      </DialogTitle>
                    </DialogHeader>

                    <div className="space-y-4">
                      <div>
                        <Label className="text-slate-300">Amount</Label>
                        <Input
                          placeholder="Enter amount"
                          value={loanAmount}
                          onChange={(e) => setLoanAmount(e.target.value)}
                          className="bg-white/5 border-white/10 text-white placeholder:text-slate-500 mt-2"
                        />
                      </div>

                      <button
                        onClick={handleEvaluateLoan}
                        disabled={evaluating}
                        className="btn-gradient w-full disabled:opacity-50"
                      >
                        {evaluating ? "Evaluating..." : "Evaluate Loan"}
                      </button>
                    </div>
                  </DialogContent>
                </Dialog>
              )}
            </CardContent>
          </Card>
        </motion.div>

        {/* Active Loan */}
        {loan?.has_active_loan && (
          <motion.div variants={fadeUp}>
            <Card className="rounded-2xl border-blue-500/20">
              <CardContent className="p-6 space-y-6">
                <div className="flex items-center gap-3">
                  <h2 className="text-2xl font-semibold text-white">
                    Active Loan
                  </h2>
                  <Badge className="bg-blue-500/20 text-blue-400 border-blue-500/30">
                    Active
                  </Badge>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  <StatCard
                    label="Borrowed"
                    value={`${loan.amount_tokens} mUSDC`}
                  />
                  <StatCard
                    label="APR"
                    value={`${loan.apr}%`}
                  />
                  <StatCard
                    label="Borrowed At"
                    value={new Date(
                      loan.borrowed_at * 1000
                    ).toLocaleDateString()}
                  />
                </div>
              </CardContent>
            </Card>
          </motion.div>
        )}
      </div>
    </motion.div>
  );
}
