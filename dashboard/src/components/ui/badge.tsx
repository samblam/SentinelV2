import * as React from 'react';

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'outline' | 'secondary';
}

function Badge({ className = '', variant = 'default', ...props }: BadgeProps) {
  const baseStyles = 'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-tactical-accent focus:ring-offset-2';

  const variantStyles = {
    default: 'bg-tactical-accent text-white',
    outline: 'border border-tactical-border bg-transparent text-tactical-text',
    secondary: 'bg-tactical-hover text-tactical-text',
  };

  const combinedClassName = `${baseStyles} ${variantStyles[variant]} ${className}`;

  return <div className={combinedClassName} {...props} />;
}

export { Badge };
