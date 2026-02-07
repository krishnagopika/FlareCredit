"use client";

import '@rainbow-me/rainbowkit/styles.css';

import {
  getDefaultConfig,
  RainbowKitProvider,
} from '@rainbow-me/rainbowkit';

import { WagmiProvider} from 'wagmi';
import { type Chain } from 'viem';
import { QueryClientProvider, QueryClient } from '@tanstack/react-query';


// ✅ Define Flare Coston2 properly
const flareCoston2: Chain = {
  id: 114,
  name: 'Flare Coston2',
  nativeCurrency: {
    decimals: 18,
    name: 'Coston2 Flare',
    symbol: 'C2FLR',
  },
  rpcUrls: {
    default: {
      http: ['https://coston2-api.flare.network/ext/C/rpc'],
    },
  },
  blockExplorers: {
    default: {
      name: 'Flare Explorer',
      url: 'https://coston2-explorer.flare.network',
    },
  },
  testnet: true,
};


// ✅ IMPORTANT: add ssr: true for Next.js
const config = getDefaultConfig({
  appName: 'Flare Credit Oracle',
  projectId: '180f66d36ba76dcba73fc82d692483ae',
  chains: [flareCoston2],
  ssr: true, 
});


// ✅ Prevent React from recreating client every render
const queryClient = new QueryClient();

export default function Providers({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <WagmiProvider config={config}>
      <QueryClientProvider client={queryClient}>
        <RainbowKitProvider >
          {children}
        </RainbowKitProvider>
      </QueryClientProvider>
    </WagmiProvider>
  );
}
