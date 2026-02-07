"use client";

import { ConnectButton } from '@rainbow-me/rainbowkit';
import { useAccount } from 'wagmi';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';

export default function Landing() {

  const { isConnected } = useAccount();
  const router = useRouter();

 

  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-6">

      <h1 className="text-5xl font-bold">
        Flare Credit Oracle
      </h1>

      <p className="text-xl">
        Unlock lower collateral loans using verifiable credit data.
      </p>

      <ConnectButton />

      {isConnected && (
  <button
    onClick={() => router.push('/dashboard')}
    className="bg-black text-white px-6 py-3 rounded-xl"
  >
    Enter Dashboard →
  </button>
)}

    </main>
  );
}
