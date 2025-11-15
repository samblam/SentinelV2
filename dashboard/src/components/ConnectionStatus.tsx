// src/components/ConnectionStatus.tsx

import { Wifi, WifiOff } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ConnectionStatusProps {
  isConnected: boolean;
}

export function ConnectionStatus({ isConnected }: ConnectionStatusProps) {
  return (
    <div className="flex items-center gap-2">
      {isConnected ? (
        <>
          <Wifi className="w-5 h-5 text-tactical-success" />
          <span className="text-sm text-tactical-success font-medium">
            Connected
          </span>
        </>
      ) : (
        <>
          <WifiOff className="w-5 h-5 text-tactical-danger" />
          <span className="text-sm text-tactical-danger font-medium">
            Disconnected
          </span>
        </>
      )}
      <div
        className={cn(
          'w-2 h-2 rounded-full',
          isConnected ? 'bg-tactical-success animate-pulse' : 'bg-tactical-danger'
        )}
      />
    </div>
  );
}
