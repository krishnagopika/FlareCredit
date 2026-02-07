"use client";

import { useAccount, useChainId } from 'wagmi';

export default function Dashboard() {
  const { address, isConnected } = useAccount();
  const chainId = useChainId();

  if (!isConnected) {
    return <div>Please connect your wallet.</div>;
  }

  return (
    <div>
      <h2>Wallet</h2>
      <p>{address}</p>
      <p>Chain ID: {chainId}</p>
    </div>
  );
}
