import { ConnectButton } from '@rainbow-me/rainbowkit';

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-6 p-24">
      
      <h1 className="text-5xl font-bold text-center">
       Borrow Smarter with Verifiable Credit
      </h1>

      <p className="text-xl text-center max-w-2xl">
        Undercollateralized DeFi lending powered by verifiable off-chain credit data using Flare’s Data Connector.
      </p>

      
      <ConnectButton />

    </main>
  );
}
