"use client";

import '@rainbow-me/rainbowkit/styles.css';

import {
  getDefaultConfig,
  RainbowKitProvider,
  darkTheme,
} from '@rainbow-me/rainbowkit';

import { WagmiProvider } from 'wagmi';
import { type Chain } from 'viem';
import { QueryClientProvider, QueryClient } from '@tanstack/react-query';

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

const config = getDefaultConfig({
  appName: 'FlareCredit',
  projectId: '180f66d36ba76dcba73fc82d692483ae',
  chains: [flareCoston2],
  ssr: true,
});

const queryClient = new QueryClient();

const customTheme = darkTheme({
  accentColor: '#3b82f6',
  accentColorForeground: 'white',
  borderRadius: 'large',
  fontStack: 'system',
  overlayBlur: 'small',
});

// Override specific tokens for glassmorphism look
customTheme.colors.connectButtonBackground = 'rgba(255,255,255,0.05)';
customTheme.colors.connectButtonInnerBackground = 'rgba(255,255,255,0.08)';
customTheme.colors.connectButtonText = '#f8fafc';
customTheme.colors.modalBackground = 'rgba(15,22,41,0.95)';
customTheme.colors.modalBorder = 'rgba(255,255,255,0.1)';
customTheme.colors.modalText = '#f8fafc';
customTheme.colors.modalTextSecondary = '#94a3b8';
customTheme.colors.profileForeground = 'rgba(15,22,41,0.95)';
customTheme.colors.actionButtonBorder = 'rgba(255,255,255,0.1)';
customTheme.colors.actionButtonSecondaryBackground = 'rgba(255,255,255,0.05)';
customTheme.colors.generalBorder = 'rgba(255,255,255,0.1)';
customTheme.colors.menuItemBackground = 'rgba(255,255,255,0.05)';
customTheme.colors.closeButton = '#94a3b8';
customTheme.colors.closeButtonBackground = 'rgba(255,255,255,0.05)';
customTheme.shadows.connectButton = '0 0 20px rgba(59,130,246,0.15)';
customTheme.shadows.dialog = '0 0 40px rgba(59,130,246,0.1)';
customTheme.shadows.profileDetailsAction = '0 0 10px rgba(59,130,246,0.1)';

export default function Providers({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <WagmiProvider config={config}>
      <QueryClientProvider client={queryClient}>
        <RainbowKitProvider theme={customTheme}>
          {children}
        </RainbowKitProvider>
      </QueryClientProvider>
    </WagmiProvider>
  );
}
