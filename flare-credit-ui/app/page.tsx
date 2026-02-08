"use client";

import { ConnectButton } from '@rainbow-me/rainbowkit';
import { useAccount, useBalance } from 'wagmi';
import { useRouter } from 'next/navigation';

const MUSDC_ADDRESS = "0x45c7B48d002D014D0F8C8dff55045016AD28ACCB"; // replace

export default function Landing() {

  const { address, isConnected } = useAccount();
  const router = useRouter();

  const { data: flareBalance, isLoading: flareLoading } = useBalance({
    address,
  });

  const { data: musdcBalance, isLoading: musdcLoading } = useBalance({
    address,
    token: MUSDC_ADDRESS,
  });

  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-6">

      <h1 className="text-5xl font-bold">
        Flare Credit Oracle
      </h1>

      <p className="text-xl">
        Unlock lower collateral loans using verifiable credit data.
      </p>

      <ConnectButton />

      {/* ⭐ Wallet Overview */}
      {isConnected && (
        <div className="border rounded-2xl p-6 w-[360px] text-center space-y-2 shadow-sm">

          <p className="text-sm text-gray-500">
            Wallet Connected
          </p>

          <p className="font-mono text-xs break-all">
            {address}
          </p>

          <div className="pt-3 space-y-1">

            <p>
              {flareLoading
                ? "Loading..."
                : `${Number(flareBalance?.formatted).toFixed(2)} ${flareBalance?.symbol}`}
            </p>

            <p>
              {musdcLoading
                ? "Loading..."
                : `${Number(musdcBalance?.formatted).toLocaleString()} ${musdcBalance?.symbol}`}
            </p>

          </div>
        </div>
      )}

      {isConnected && (
        <button
          onClick={() => router.push('/dashboard')}
          className="bg-black text-white px-6 py-3 rounded-xl hover:scale-105 transition"
        >
          Enter Dashboard →
        </button>
      )}

    </main>
  );
}
