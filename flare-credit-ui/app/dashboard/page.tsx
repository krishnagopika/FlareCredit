"use client";

import { useAccount } from 'wagmi';
import { useState } from 'react';
import { useRouter } from 'next/navigation';

export default function Dashboard() {

  const { address } = useAccount();

  const [loading, setLoading] = useState(false);
  const [creditData, setCreditData] = useState<any>(null);
    const router = useRouter();

  const requestScore = () => {
    setLoading(true);

    // Fake backend delay (simulate oracle)
    setTimeout(() => {
      setCreditData({
        tradFi: 742,
        onchain: "Strong",
        approved:true,
        rating: "Excellent",
        maxBorrow: "$25,000",
        interest: "6.2%",
        collateral: "None 🎉",
      });

      setLoading(false);
    }, 2500);
  };

  return (
    <div className="p-10 max-w-4xl mx-auto space-y-6">

      {/* Wallet Card */}
      <div className="border rounded-2xl p-6">
        <h2 className="text-xl font-bold mb-2">Wallet</h2>
        <p className="font-mono">{address}</p>
        <p>Flare Coston2 🟢</p>
      </div>

      {/* Oracle Action */}
      {!creditData && !loading && (
        <div className="border rounded-2xl p-6 text-center">
          <h2 className="text-xl font-bold mb-4">
            Credit Oracle
          </h2>

          <button
            onClick={requestScore}
            className="bg-black text-white px-6 py-3 rounded-xl"
          >
            Request Verifiable Credit Score
          </button>
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="border rounded-2xl p-6 text-center">
          <p className="animate-pulse">
            Fetching data via Flare Data Connector...
          </p>
        </div>
      )}

      {/* Results */}
      {creditData && (
        <div className="border rounded-2xl p-6 space-y-4">

          <h2 className="text-2xl font-bold">
  {creditData.approved ? "✅ Approved" : "❌ Not Approved"}
</h2>


          <p>TradFi Score: <b>{creditData.tradFi}</b></p>
          <p>Onchain Score: <b>{creditData.onchain}</b></p>
          <p>Risk Rating: <b>{creditData.rating}</b></p>

          <hr />

          <p>Max Borrow: <b>{creditData.maxBorrow}</b></p>
          <p>Interest Rate: <b>{creditData.interest}</b></p>
          <p>
            Collateral Required:
            <b className="text-green-600"> {creditData.collateral}</b>
          </p>

            {creditData.approved && (
  <button
    onClick={() => router.push('/borrow')}
    className="bg-green-600 text-white px-6 py-3 rounded-xl w-full mt-4"
  >
    Apply for Loan →
  </button>
)}

{!creditData.approved && (
  <div className="mt-4 border rounded-xl p-4 bg-red-50">
    <p className="font-bold text-red-600">
      Not Approved
    </p>

    <p className="text-sm mt-2">
      Your current credit profile does not meet the minimum threshold.
    </p>

    <p className="text-sm mt-2 font-semibold">
      How to improve:
    </p>

    <ul className="text-sm list-disc ml-5">
      <li>Increase wallet activity</li>
      <li>Maintain consistent balances</li>
      <li>Reduce outstanding debt</li>
    </ul>
  </div>
)}


        </div>
      )}

    </div>
  );
}
