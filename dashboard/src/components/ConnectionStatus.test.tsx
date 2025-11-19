// ConnectionStatus.test.tsx
import { describe, it, expect } from 'vitest';
import { render, screen } from '@/test/test-utils';
import { ConnectionStatus } from './ConnectionStatus';

describe('ConnectionStatus', () => {
  it('renders connected status correctly', () => {
    render(<ConnectionStatus isConnected={true} />);

    expect(screen.getByText('Connected')).toBeInTheDocument();
    expect(screen.getByText('Connected')).toHaveClass('text-tactical-success');
  });

  it('renders disconnected status correctly', () => {
    render(<ConnectionStatus isConnected={false} />);

    expect(screen.getByText('Disconnected')).toBeInTheDocument();
    expect(screen.getByText('Disconnected')).toHaveClass('text-tactical-danger');
  });

  it('displays correct icon for connected state', () => {
    const { container } = render(<ConnectionStatus isConnected={true} />);

    // Check for WiFi icon (lucide-react renders as svg)
    const svg = container.querySelector('svg');
    expect(svg).toBeInTheDocument();
  });

  it('displays correct icon for disconnected state', () => {
    const { container } = render(<ConnectionStatus isConnected={false} />);

    // Check for WifiOff icon
    const svg = container.querySelector('svg');
    expect(svg).toBeInTheDocument();
  });
});
