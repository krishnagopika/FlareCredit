"use client";

import { useAccount, useBalance } from "wagmi";
import { useEffect, useState } from "react";

import {
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

const MUSDC_ADDRESS = "0x45c7B48d002D014D0F8C8dff55045016AD28ACCB";

/* ---------- Reusable Stat Card ---------- */

function StatCard({
  label,
  value,
}: {
  label: string;
  value: string | number;
}) {
  return (
    <Card className="rounded-2xl">
      <CardContent className="p-5">
        <p className="text-sm text-muted-foreground">
          {label}
        </p>

        <p className="text-2xl font-semibold mt-1">
          {value}
        </p>
      </CardContent>
    </Card>
  );
}

/* ---------- Dashboard ---------- */

export default function Dashboard() {
  const { address, isConnected } = useAccount();

  const [credit, setCredit] = useState<any>(null);
  const [loan, setLoan] = useState<any>(null);

  const [creditProcessing, setCreditProcessing] = useState(false);
  const [loanAmount, setLoanAmount] = useState("");
  const [evaluating, setEvaluating] = useState(false);
  const [error, setError] = useState("");

  /* ---------- Wallet Balances ---------- */

  const { data: gasBalance, isLoading: gasLoading } = useBalance({
    address,
  });

  const { data: musdcBalance, isLoading: musdcLoading } = useBalance({
    address,
    token: MUSDC_ADDRESS,
  });

  /* ---------- Fetch Loan Only (no auto credit) ---------- */

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

  /* ---------- Trigger Agents ---------- */

 const handleRequestScore = async () => {
  if (!address) return;

  try {
    setCreditProcessing(true);

    // ✅ backend returns the score directly
    const score = await processCreditScore(address);

    // update UI instantly
    setCredit(score);

  } catch (err) {
    console.error(err);
    setError("Failed to generate credit score");
  } finally {
    setCreditProcessing(false);
  }
};

  /* ---------- Evaluate Loan ---------- */

  const handleEvaluateLoan = async () => {
    if (!address || !loanAmount) return;

    try {
      setEvaluating(true);

      const result = await evaluateLoan(
        address,
        Number(loanAmount)
      );

      alert(
        result.approved
          ? `✅ Approved! APR: ${result.adjusted_apr}%`
          : `❌ Rejected: ${result.reason}`
      );
    } finally {
      setEvaluating(false);
    }
  };

  if (!isConnected) {
    return (
      <div className="p-10">
        Please connect your wallet.
      </div>
    );
  }

  return (
    <div className="p-10 max-w-5xl mx-auto space-y-8">

      {/* ---------- WALLET ---------- */}

      <Card className="rounded-2xl">
        <CardContent className="p-6">
          <h2 className="text-2xl font-semibold">
            My Wallet
          </h2>

          <p className="font-mono text-sm text-muted-foreground mt-1">
            {address?.slice(0,6)}...{address?.slice(-4)}
          </p>
        </CardContent>
      </Card>

      {/* ---------- FINANCIAL PROFILE ---------- */}

      <Card className="rounded-2xl">
        <CardContent className="p-6 space-y-6">

          <div>
            <h2 className="text-2xl font-semibold">
              Financial Profile
            </h2>

            <p className="text-muted-foreground text-sm">
              Live wallet balances
            </p>
          </div>

          <div className="grid grid-cols-2 gap-4">

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

      {/* ---------- CREDIT INTELLIGENCE ---------- */}

      <Card className="rounded-2xl">
        <CardContent className="p-6 space-y-6">

          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-semibold">
                Credit Intelligence
              </h2>

              <p className="text-muted-foreground text-sm">
                Agent-verified borrowing power
              </p>
            </div>

            {credit && (
              <Badge className="bg-green-100 text-green-700">
                Approved
              </Badge>
            )}
          </div>

          {!credit ? (
            <Button
              onClick={handleRequestScore}
              disabled={creditProcessing}
              className="w-full"
              size="lg"
            >
              {creditProcessing
                ? "Running credit agents..."
                : "Request Credit Score"}
            </Button>
          ) : (
            <div className="grid grid-cols-2 gap-4">

              <StatCard label="TradFi Score" value={credit.tradfi_score} />
              <StatCard label="Onchain Score" value={credit.onchain_score} />
              <StatCard label="Risk Score" value={credit.combined_risk_score} />

              <StatCard
                label="Max Borrow"
                value={`${Number(credit.max_borrow_amount) / 1e18} mUSDC`}
              />

              <StatCard
                label="APR"
                value={`${credit.apr}%`}
              />

            </div>
          )}

          {/* ---------- APPLY FOR LOAN ---------- */}

          {credit && (
            <Dialog>

              <DialogTrigger asChild>
                <Button size="lg" className="w-full">
                  Apply For Loan
                </Button>
              </DialogTrigger>

              <DialogContent>

                <DialogHeader>
                  <DialogTitle>
                    Request Loan
                  </DialogTitle>
                </DialogHeader>

                <div className="space-y-4">

                  <div>
                    <Label>Amount</Label>

                    <Input
                      placeholder="Enter amount"
                      value={loanAmount}
                      onChange={(e) =>
                        setLoanAmount(e.target.value)
                      }
                    />
                  </div>

                  <Button
                    onClick={handleEvaluateLoan}
                    disabled={evaluating}
                    className="w-full"
                  >
                    {evaluating
                      ? "Evaluating..."
                      : "Evaluate Loan"}
                  </Button>

                </div>

              </DialogContent>
            </Dialog>
          )}

        </CardContent>
      </Card>

      {/* ---------- ACTIVE LOAN ---------- */}

      {loan?.has_active_loan && (
        <Card className="rounded-2xl">
          <CardContent className="p-6 space-y-6">

            <h2 className="text-2xl font-semibold">
              Active Loan
            </h2>

            <div className="grid grid-cols-2 gap-4">

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
      )}

    </div>
  );
}
