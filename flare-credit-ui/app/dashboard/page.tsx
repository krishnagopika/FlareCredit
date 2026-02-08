// "use client";

// import { useAccount, useBalance } from "wagmi";
// import { useEffect, useState } from "react";


// import {
//   getOnchainData,
//   getCreditScore,
//   processCreditScore,
//   getLoanStatus,
// } from "@/lib/api";

// const MUSDC_ADDRESS = "0x45c7B48d002D014D0F8C8dff55045016AD28ACCB"; // replace

// function Stat({ label, value }: { label: string; value: any }) {
//   return (
//     <div className="border rounded-lg p-4">
//       <p className="text-sm text-gray-600">{label}</p>
//       <p className="text-lg font-bold">{value}</p>
//     </div>
//   );
// }

// export default function Dashboard() {
//   const { address, isConnected } = useAccount();

//   const [onchain, setOnchain] = useState<any>(null);
//   const [credit, setCredit] = useState<any>(null);
//   const [loan, setLoan] = useState<any>(null);

//   const [loading, setLoading] = useState(false);
//   const [creditProcessing, setCreditProcessing] = useState(false);
//   const [error, setError] = useState("");



// // Native token (C2FLR)
// const { data: gasBalance, isLoading: gasLoading } = useBalance({
//   address,
// });

// // ERC20 token (mUSDC)
// const { data: musdcBalance, isLoading: musdcLoading } = useBalance({
//   address,
//   token: MUSDC_ADDRESS,
// });

//   // ⭐ Move fetchData OUTSIDE useEffect
//   const fetchData = async () => {
//     if (!address) return;

//     try {
//       setLoading(true);

//       const [onchainData, creditData, loanData] = await Promise.all([
//         getOnchainData(address),
//         getCreditScore(address),
//         getLoanStatus(address),
//       ]);

//       setOnchain(onchainData);
//       setCredit(creditData);
//       setLoan(loanData);
//     } catch {
//       setError("Failed to load dashboard");
//     } finally {
//       setLoading(false);
//     }
//   };

//   useEffect(() => {
//     fetchData();
//   }, [address]);

//   // trigger credit score processing on chain and refetch data after
//   const handleProcessScore = async () => {
//     if (!address) return;

//     try {
//       setCreditProcessing(true);

//       await processCreditScore(address);

//       // Give agents time to write on-chain
//       setTimeout(fetchData, 5000);
//     } catch {
//       setError("Failed to process credit score");
//     } finally {
//       setCreditProcessing(false);
//     }
//   };

//   if (!isConnected) {
//     return <div className="p-10">Please connect your wallet.</div>;
//   }

//   return (
//     <div className="p-10 max-w-4xl mx-auto space-y-6">

//       {/* Wallet */}
//       <div className="border rounded-2xl p-6">
//         <h2 className="text-xl font-bold mb-2"> My Wallet</h2>
//         <p className="font-mono text-sm">{address}</p>
//       </div>

//      {isConnected && (
//   <div className="border rounded-2xl p-6 space-y-4">

//     <h2 className="text-xl font-bold">
//       Financial Profile
//     </h2>

//     <div className="grid grid-cols-2 gap-4">

//       <Stat
//         label="Gas Balance"
//         value={
//           gasLoading
//             ? "Loading..."
//             : `${Number(gasBalance?.formatted).toFixed(2)} ${gasBalance?.symbol}`
//         }
//       />

//       <Stat
//         label="Token Balance"
//         value={
//           musdcLoading
//             ? "Loading..."
//             : `${Number(musdcBalance?.formatted).toLocaleString()} ${musdcBalance?.symbol}`
//         }
//       />

//     </div>

//     <p className="text-xs text-gray-500 font-mono">
//       {address?.slice(0,6)}...{address?.slice(-4)}
//     </p>

//   </div>
// )}


//       {/* Credit Intelligence */}
//       <div className="border rounded-2xl p-6 space-y-4">
//         <h2 className="text-xl font-bold">
//           Credit Intelligence
//         </h2>

//         {!credit && (
//           <div className="space-y-3">
//             <p>No credit profile found.</p>

//             <button
//               onClick={handleProcessScore}
//               className="bg-black text-white px-4 py-2 rounded-xl"
//             >
//               {creditProcessing
//                 ? "Processing..."
//                 : "Request Credit Score"}
//             </button>
//           </div>
//         )}

//         {credit && (
//           <div className="grid grid-cols-2 gap-4">

//             <Stat label="TradFi Score" value={credit.tradfi_score} />
//             <Stat label="Onchain Score" value={credit.onchain_score} />
//             <Stat label="Risk Score" value={credit.combined_risk_score} />

//             <Stat
//               label="Max Borrow"
//               value={`${Number(credit.max_borrow_amount) / 1e18} tokens`}
//             />

//             <Stat label="APR" value={`${credit.apr}%`} />
//           </div>
//         )}
//       </div>

//       {/* Active Loan */}
//       {loan?.has_active_loan && (
//         <div className="border rounded-2xl p-6 space-y-4">
//           <h2 className="text-xl font-bold">
//             Active Loan
//           </h2>

//           <div className="grid grid-cols-2 gap-4">

//             <Stat
//               label="Borrowed"
//               value={`${loan.amount_tokens} tokens`}
//             />

//             <Stat
//               label="APR"
//               value={`${loan.apr}%`}
//             />

//             <Stat
//               label="Borrowed At"
//               value={new Date(
//                 loan.borrowed_at * 1000
//               ).toLocaleDateString()}
//             />

//           </div>
//         </div>
//       )}

//     </div>
//   );
// }

"use client";

import { useAccount, useBalance } from "wagmi";
import { useEffect, useState } from "react";

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

      await processCreditScore(address);

      // wait for agents to write on-chain
      setTimeout(async () => {
        const score = await getCreditScore(address);
        setCredit(score);
        setCreditProcessing(false);
      }, 5000);
    } catch {
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
