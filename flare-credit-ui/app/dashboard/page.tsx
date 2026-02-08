"use client";

import { useAccount, useBalance, useWriteContract, useWaitForTransactionReceipt } from "wagmi";
import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useRouter } from "next/navigation";
import { ConnectButton } from "@rainbow-me/rainbowkit";

import {
  processCreditScore,
  getLoanStatus,
  evaluateLoan,
  disburseLoan,
  getRepaymentInfo,
} from "@/lib/api";

import {
  Card,
  CardContent,
} from "@/components/ui/card";

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

const MUSDC_ADDRESS = "0x45c7B48d002D014D0F8C8dff55045016AD28ACCB" as const;
const LENDING_ADDRESS = "0x9feF5655Ad38c61E6F662c5aED8174dcde2fd788" as const;

const ERC20_ABI = [
  {
    inputs: [
      { name: "spender", type: "address" },
      { name: "amount", type: "uint256" },
    ],
    name: "approve",
    outputs: [{ name: "", type: "bool" }],
    stateMutability: "nonpayable",
    type: "function",
  },
] as const;

const LENDING_ABI = [
  {
    inputs: [],
    name: "repay",
    outputs: [],
    stateMutability: "nonpayable",
    type: "function",
  },
] as const;

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
        <circle
          cx="70"
          cy="70"
          r={radius}
          fill="none"
          stroke="rgba(255,255,255,0.05)"
          strokeWidth="10"
        />
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
  info,
}: {
  label: string;
  value: string | number;
  info?: string;
}) {
  const [showInfo, setShowInfo] = useState(false);

  return (
    <Card className="rounded-2xl glass-hover">
      <CardContent className="p-5">
        <div className="flex items-center gap-1.5">
          <p className="text-sm text-slate-400">{label}</p>
          {info && (
            <div className="relative">
              <button
                onClick={() => setShowInfo(!showInfo)}
                onMouseEnter={() => setShowInfo(true)}
                onMouseLeave={() => setShowInfo(false)}
                className="w-4 h-4 rounded-full bg-white/10 flex items-center justify-center text-[10px] text-slate-400 hover:bg-white/20 hover:text-slate-300 transition-colors"
              >
                i
              </button>
              <AnimatePresence>
                {showInfo && (
                  <motion.div
                    initial={{ opacity: 0, y: 4 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: 4 }}
                    transition={{ duration: 0.15 }}
                    className="absolute z-50 bottom-full left-1/2 -translate-x-1/2 mb-2 w-52 p-2.5 rounded-lg bg-navy-800/95 backdrop-blur-xl border border-white/10 shadow-xl"
                  >
                    <p className="text-xs text-slate-300 leading-relaxed">{info}</p>
                    <div className="absolute top-full left-1/2 -translate-x-1/2 w-2 h-2 bg-navy-800/95 border-r border-b border-white/10 rotate-45 -mt-1" />
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          )}
        </div>
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
  const [loanLoading, setLoanLoading] = useState(true);
  const [repaymentInfo, setRepaymentInfo] = useState<any>(null);

  const [creditProcessing, setCreditProcessing] = useState(false);
  const [loanAmount, setLoanAmount] = useState("");
  const [loanToken, setLoanToken] = useState("mUSDC");
  const [loanType, setLoanType] = useState("Business");
  const [evaluating, setEvaluating] = useState(false);
  const [evalResult, setEvalResult] = useState<any>(null);
  const [disbursing, setDisbursing] = useState(false);
  const [disburseResult, setDisburseResult] = useState<any>(null);
  const [error, setError] = useState("");

  const [loanExpanded, setLoanExpanded] = useState(false);
  const [settleStep, setSettleStep] = useState<"idle" | "approving" | "repaying" | "done" | "error">("idle");
  const [settleError, setSettleError] = useState("");

  const { data: gasBalance, isLoading: gasLoading } = useBalance({
    address,
  });

  const { data: musdcBalance, isLoading: musdcLoading } = useBalance({
    address,
    token: MUSDC_ADDRESS,
  });

  // Approve tx
  const { writeContract: writeApprove, data: approveTxHash } = useWriteContract();
  const { isSuccess: approveConfirmed } = useWaitForTransactionReceipt({ hash: approveTxHash });

  // Repay tx
  const { writeContract: writeRepay, data: repayTxHash } = useWriteContract();
  const { isSuccess: repayConfirmed } = useWaitForTransactionReceipt({ hash: repayTxHash });

  /* ---------- Fetch loan + repayment info ---------- */

  useEffect(() => {
    if (!address) return;

    const fetchLoan = async () => {
      try {
        setLoanLoading(true);
        const loanData = await getLoanStatus(address);
        setLoan(loanData);

        if (loanData?.has_active_loan) {
          const repayData = await getRepaymentInfo(address);
          setRepaymentInfo(repayData);
        }
      } catch (err) {
        console.error("Failed to fetch loan status:", err);
      } finally {
        setLoanLoading(false);
      }
    };

    fetchLoan();
  }, [address]);

  /* ---------- After approve confirmed, call repay ---------- */

  useEffect(() => {
    if (approveConfirmed && settleStep === "approving") {
      setSettleStep("repaying");
      writeRepay({
        address: LENDING_ADDRESS,
        abi: LENDING_ABI,
        functionName: "repay",
      });
    }
  }, [approveConfirmed, settleStep, writeRepay]);

  /* ---------- After repay confirmed ---------- */

  useEffect(() => {
    if (repayConfirmed && settleStep === "repaying") {
      setSettleStep("done");
      // Refresh loan status
      if (address) {
        getLoanStatus(address).then(setLoan).catch(() => {});
      }
    }
  }, [repayConfirmed, settleStep, address]);

  /* ---------- Handlers ---------- */

  const handleRequestScore = async () => {
    if (!address) return;

    try {
      setCreditProcessing(true);
      const score = await processCreditScore(address);
      setCredit(score);
    } catch (err) {
      console.error(err);
      setError("Failed to generate credit score");
    } finally {
      setCreditProcessing(false);
    }
  };

  const handleEvaluateLoan = async () => {
    if (!address || !loanAmount) return;

    try {
      setEvaluating(true);
      setEvalResult(null);
      const result = await evaluateLoan(address, Number(loanAmount));
      setEvalResult(result);
    } catch (err: any) {
      setEvalResult({ approved: false, reason: err?.message || "Evaluation failed" });
    } finally {
      setEvaluating(false);
    }
  };

  const handleSettleLoan = async () => {
    if (!repaymentInfo) return;

    try {
      setSettleStep("approving");
      setSettleError("");

      const amountWei = repaymentInfo.repayment.total_amount_wei;

      writeApprove({
        address: MUSDC_ADDRESS,
        abi: ERC20_ABI,
        functionName: "approve",
        args: [LENDING_ADDRESS, BigInt(amountWei)],
      });
    } catch (err: any) {
      setSettleStep("error");
      setSettleError(err?.message || "Transaction failed");
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

        {/* Loan Status - Always visible */}
        <motion.div variants={fadeUp}>
          <Card className="rounded-2xl border-blue-500/20 glow-blue">
            <CardContent className="p-6 space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <h2 className="text-2xl font-semibold text-white">
                    Loan Status
                  </h2>
                  {loan?.has_active_loan && (
                    <Badge className="bg-blue-500/20 text-blue-400 border-blue-500/30">
                      Active
                    </Badge>
                  )}
                  {loan && !loan.has_active_loan && (
                    <Badge className="bg-slate-500/20 text-slate-400 border-slate-500/30">
                      No Active Loan
                    </Badge>
                  )}
                </div>
                {loan?.has_active_loan && (
                  <button onClick={() => setLoanExpanded(!loanExpanded)}>
                    <motion.svg
                      width="24"
                      height="24"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      className="text-slate-400"
                      animate={{ rotate: loanExpanded ? 180 : 0 }}
                      transition={{ duration: 0.2 }}
                    >
                      <path d="M6 9l6 6 6-6" />
                    </motion.svg>
                  </button>
                )}
              </div>

              {loanLoading && (
                <div className="text-center py-4">
                  <p className="text-slate-400 text-sm">Loading loan status...</p>
                </div>
              )}

              {!loanLoading && !loan?.has_active_loan && (
                <div className="glass rounded-xl p-6 text-center space-y-2">
                  <p className="text-slate-400">No active loans found.</p>
                  <p className="text-slate-500 text-sm">
                    Request a credit score below to unlock borrowing power.
                  </p>
                </div>
              )}

              {loan?.has_active_loan && (
                <>
                  {/* Summary row */}
                  <div className="grid grid-cols-3 gap-4">
                    <div>
                      <p className="text-xs text-slate-500 uppercase tracking-wider">Borrowed</p>
                      <p className="text-lg font-semibold text-white mt-1">
                        {loan.amount_tokens} mUSDC
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-slate-500 uppercase tracking-wider">APR</p>
                      <p className="text-lg font-semibold text-white mt-1">
                        {loan.apr}%
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-slate-500 uppercase tracking-wider">Since</p>
                      <p className="text-lg font-semibold text-white mt-1">
                        {new Date(loan.borrowed_at * 1000).toLocaleDateString()}
                      </p>
                    </div>
                  </div>

                  {/* Expanded repayment details */}
                  <AnimatePresence>
                    {loanExpanded && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: "auto", opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.3, ease: "easeOut" as const }}
                        className="overflow-hidden"
                      >
                        <div className="pt-4 border-t border-white/5 space-y-4">
                          {repaymentInfo && (
                            <div className="space-y-3">
                              <h3 className="text-sm font-medium text-slate-300 uppercase tracking-wider">
                                Repayment Details
                              </h3>

                              <div className="grid grid-cols-2 gap-4">
                                <div className="glass rounded-xl p-4">
                                  <p className="text-xs text-slate-500">Interest Accrued</p>
                                  <p className="text-lg font-semibold text-white mt-1">
                                    {Number(repaymentInfo.repayment.interest).toFixed(4)} mUSDC
                                  </p>
                                </div>
                                <div className="glass rounded-xl p-4">
                                  <p className="text-xs text-slate-500">Total Repayment</p>
                                  <p className="text-lg font-semibold text-gradient mt-1">
                                    {Number(repaymentInfo.repayment.total_amount).toFixed(4)} mUSDC
                                  </p>
                                </div>
                                <div className="glass rounded-xl p-4">
                                  <p className="text-xs text-slate-500">Time Elapsed</p>
                                  <p className="text-lg font-semibold text-white mt-1">
                                    {Number(repaymentInfo.repayment.time_elapsed_days).toFixed(1)} days
                                  </p>
                                </div>
                                <div className="glass rounded-xl p-4">
                                  <p className="text-xs text-slate-500">Your Balance</p>
                                  <p className={`text-lg font-semibold mt-1 ${
                                    repaymentInfo.user_status.has_sufficient_balance
                                      ? "text-green-400"
                                      : "text-red-400"
                                  }`}>
                                    {Number(repaymentInfo.user_status.balance).toFixed(2)} mUSDC
                                  </p>
                                </div>
                              </div>

                              {settleStep === "done" && (
                                <motion.div
                                  className="glass rounded-xl p-4 border border-green-500/20 text-center"
                                  initial={{ opacity: 0, y: 10 }}
                                  animate={{ opacity: 1, y: 0 }}
                                >
                                  <p className="text-green-400 font-semibold">
                                    Loan settled successfully!
                                  </p>
                                </motion.div>
                              )}

                              {settleStep === "error" && (
                                <div className="glass rounded-xl p-4 border border-red-500/20 text-center">
                                  <p className="text-red-400 text-sm">{settleError || "Transaction failed"}</p>
                                </div>
                              )}

                              {settleStep !== "done" && (
                                <motion.button
                                  onClick={handleSettleLoan}
                                  disabled={
                                    settleStep === "approving" ||
                                    settleStep === "repaying" ||
                                    !repaymentInfo.user_status.has_sufficient_balance
                                  }
                                  className="w-full py-4 rounded-xl font-medium text-white transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed bg-gradient-to-r from-green-600 to-emerald-500 hover:from-green-500 hover:to-emerald-400 hover:shadow-lg hover:shadow-green-500/25 active:scale-[0.98]"
                                  whileHover={{
                                    scale:
                                      settleStep === "approving" || settleStep === "repaying"
                                        ? 1
                                        : 1.02,
                                  }}
                                  whileTap={{
                                    scale:
                                      settleStep === "approving" || settleStep === "repaying"
                                        ? 1
                                        : 0.98,
                                  }}
                                >
                                  {settleStep === "approving" ? (
                                    <span className="flex items-center justify-center gap-2">
                                      <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
                                      </svg>
                                      Approving tokens...
                                    </span>
                                  ) : settleStep === "repaying" ? (
                                    <span className="flex items-center justify-center gap-2">
                                      <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
                                      </svg>
                                      Repaying loan...
                                    </span>
                                  ) : !repaymentInfo.user_status.has_sufficient_balance ? (
                                    "Insufficient Balance"
                                  ) : (
                                    `Settle Loan - ${Number(repaymentInfo.repayment.total_amount).toFixed(4)} mUSDC`
                                  )}
                                </motion.button>
                              )}
                            </div>
                          )}

                          {!repaymentInfo && (
                            <div className="text-center py-4">
                              <p className="text-slate-400 text-sm">Loading repayment details...</p>
                            </div>
                          )}
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </>
              )}
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
                        info="Traditional finance creditworthiness score (0-1000) based on FICO, payment history, credit utilization, and debt-to-income ratio."
                      />
                    </motion.div>
                    <motion.div variants={fadeUp}>
                      <StatCard
                        label="Onchain Score"
                        value={credit.onchain_score}
                        info="Blockchain activity score (0-100) analyzing wallet age, transaction history, DeFi interactions, and token holdings."
                      />
                    </motion.div>
                    <motion.div variants={fadeUp}>
                      <StatCard
                        label="Risk Score"
                        value={credit.combined_risk_score}
                        info="Combined risk assessment (0-100). Lower is better. Scores above 60 are ineligible for borrowing."
                      />
                    </motion.div>
                    <motion.div variants={fadeUp}>
                      <StatCard
                        label="Max Borrow"
                        value={`${Number(credit.max_borrow_amount) / 1e18} mUSDC`}
                        info="Maximum amount you can borrow based on your combined credit profile and risk assessment."
                      />
                    </motion.div>
                    <motion.div variants={fadeUp}>
                      <StatCard
                        label="Expected APR"
                        value={`${credit.apr}%`}
                        info="Annual Percentage Rate for your loan. Based on your risk profile — lower risk scores get better rates."
                      />
                    </motion.div>
                  </div>
                </motion.div>
              )}

              {credit && (
                <Dialog onOpenChange={() => { setEvalResult(null); setDisburseResult(null); }}>
                  <DialogTrigger asChild>
                    <motion.button
                      className="btn-gradient w-full"
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                    >
                      Apply For Loan
                    </motion.button>
                  </DialogTrigger>

                  <DialogContent className="sm:max-w-xl">
                    <DialogHeader>
                      <DialogTitle className="text-white text-xl">
                        {evalResult ? "Loan Evaluation" : "Request Loan"}
                      </DialogTitle>
                    </DialogHeader>

                    {/* Step 1: Loan form */}
                    {!evalResult && (
                      <div className="space-y-5">
                        <div>
                          <Label className="text-slate-300 text-sm">Loan Amount</Label>
                          <Input
                            type="number"
                            placeholder="Enter amount"
                            value={loanAmount}
                            onChange={(e) => setLoanAmount(e.target.value)}
                            className="bg-white/5 border-white/10 text-white placeholder:text-slate-500 mt-2"
                          />
                        </div>

                        <div>
                          <Label className="text-slate-300 text-sm">Token</Label>
                          <select
                            value={loanToken}
                            onChange={(e) => setLoanToken(e.target.value)}
                            className="w-full p-3 rounded-xl text-sm mt-2"
                          >
                            <option>mUSDC</option>
                          </select>
                        </div>

                        <div>
                          <Label className="text-slate-300 text-sm">Loan Purpose</Label>
                          <select
                            value={loanType}
                            onChange={(e) => setLoanType(e.target.value)}
                            className="w-full p-3 rounded-xl text-sm mt-2"
                          >
                            <option>Business</option>
                            <option>Education</option>
                            <option>Emergency</option>
                            <option>Personal</option>
                          </select>
                        </div>

                        <button
                          onClick={handleEvaluateLoan}
                          disabled={evaluating || !loanAmount}
                          className="btn-gradient w-full disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          {evaluating ? (
                            <span className="flex items-center justify-center gap-2">
                              <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
                              </svg>
                              Evaluating...
                            </span>
                          ) : (
                            "Evaluate Loan"
                          )}
                        </button>
                      </div>
                    )}

                    {/* Step 2: Evaluation result */}
                    {evalResult && !disburseResult && (
                      <motion.div
                        className="space-y-5"
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.3 }}
                      >
                        {/* Status banner */}
                        <div className={`rounded-xl p-4 border text-center ${
                          evalResult.approved
                            ? "bg-green-500/10 border-green-500/20"
                            : "bg-red-500/10 border-red-500/20"
                        }`}>
                          <p className={`text-lg font-semibold ${
                            evalResult.approved ? "text-green-400" : "text-red-400"
                          }`}>
                            {evalResult.approved ? "Loan Approved" : "Loan Rejected"}
                          </p>
                        </div>

                        {/* Details */}
                        <div className="space-y-3">
                          <div className="flex justify-between items-center py-2 border-b border-white/5">
                            <span className="text-slate-400 text-sm">Amount</span>
                            <span className="text-white font-semibold">{loanAmount} {loanToken}</span>
                          </div>

                          {evalResult.adjusted_apr != null && (
                            <div className="flex justify-between items-center py-2 border-b border-white/5">
                              <span className="text-slate-400 text-sm">APR</span>
                              <span className="text-white font-semibold">{evalResult.adjusted_apr}%</span>
                            </div>
                          )}

                          <div className="flex justify-between items-center py-2 border-b border-white/5">
                            <span className="text-slate-400 text-sm">Purpose</span>
                            <span className="text-white font-semibold">{loanType}</span>
                          </div>
                        </div>

                        {/* Reason */}
                        {evalResult.reason && (
                          <div className="glass rounded-xl p-4">
                            <p className="text-xs text-slate-500 uppercase tracking-wider mb-2">Details</p>
                            <p className="text-sm text-slate-300 leading-relaxed">{evalResult.reason}</p>
                          </div>
                        )}

                        {/* Action buttons */}
                        <div className="flex gap-3">
                          <button
                            onClick={() => setEvalResult(null)}
                            className="flex-1 py-3 rounded-xl font-medium text-slate-300 glass glass-hover"
                          >
                            Back
                          </button>

                          {evalResult.approved && (
                            <motion.button
                              className="flex-1 py-3 rounded-xl font-medium text-white bg-gradient-to-r from-green-600 to-emerald-500 hover:from-green-500 hover:to-emerald-400 hover:shadow-lg hover:shadow-green-500/25 disabled:opacity-50 disabled:cursor-not-allowed"
                              whileHover={{ scale: disbursing ? 1 : 1.02 }}
                              whileTap={{ scale: disbursing ? 1 : 0.98 }}
                              disabled={disbursing}
                              onClick={async () => {
                                if (!address) return;
                                try {
                                  setDisbursing(true);
                                  const result = await disburseLoan(address, Number(loanAmount));
                                  setDisburseResult(result);
                                } catch (err: any) {
                                  setDisburseResult({ success: false, message: err?.message || "Disbursement failed" });
                                } finally {
                                  setDisbursing(false);
                                }
                              }}
                            >
                              {disbursing ? (
                                <span className="flex items-center justify-center gap-2">
                                  <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
                                  </svg>
                                  Disbursing...
                                </span>
                              ) : (
                                "Proceed with Loan"
                              )}
                            </motion.button>
                          )}
                        </div>
                      </motion.div>
                    )}

                    {/* Step 3: Disbursement result */}
                    {disburseResult && (
                      <motion.div
                        className="space-y-5"
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.3 }}
                      >
                        <div className={`rounded-xl p-4 border text-center ${
                          disburseResult.success
                            ? "bg-green-500/10 border-green-500/20"
                            : "bg-red-500/10 border-red-500/20"
                        }`}>
                          <p className={`text-lg font-semibold ${
                            disburseResult.success ? "text-green-400" : "text-red-400"
                          }`}>
                            {disburseResult.success ? "Loan Disbursed!" : "Disbursement Failed"}
                          </p>
                          <p className="text-sm text-slate-400 mt-1">{disburseResult.message}</p>
                        </div>

                        {disburseResult.success && (
                          <div className="space-y-3">
                            <div className="flex justify-between items-center py-2 border-b border-white/5">
                              <span className="text-slate-400 text-sm">Amount</span>
                              <span className="text-white font-semibold">{disburseResult.amount_tokens} {loanToken}</span>
                            </div>
                            {disburseResult.tx_hash && (
                              <div className="flex justify-between items-center py-2 border-b border-white/5">
                                <span className="text-slate-400 text-sm">Tx Hash</span>
                                <span className="text-blue-400 font-mono text-xs">
                                  {disburseResult.tx_hash.slice(0, 10)}...{disburseResult.tx_hash.slice(-8)}
                                </span>
                              </div>
                            )}
                          </div>
                        )}

                        <button
                          onClick={() => {
                            setEvalResult(null);
                            setDisburseResult(null);
                            setLoanAmount("");
                            // Refresh loan status
                            if (address) {
                              getLoanStatus(address).then(data => {
                                setLoan(data);
                                if (data?.has_active_loan) {
                                  getRepaymentInfo(address).then(setRepaymentInfo).catch(() => {});
                                }
                              }).catch(() => {});
                            }
                          }}
                          className="btn-gradient w-full"
                        >
                          Done
                        </button>
                      </motion.div>
                    )}
                  </DialogContent>
                </Dialog>
              )}
            </CardContent>
          </Card>
        </motion.div>

      </div>
    </motion.div>
  );
}
