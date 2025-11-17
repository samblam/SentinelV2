import * as React from 'react';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'default' | 'outline' | 'ghost';
  size?: 'default' | 'sm' | 'lg';
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className = '', variant = 'default', size = 'default', ...props }, ref) => {
    const baseStyles = 'inline-flex items-center justify-center rounded-md font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-tactical-accent disabled:opacity-50 disabled:pointer-events-none';

    const variantStyles = {
      default: 'bg-tactical-accent text-white hover:bg-tactical-accentHover',
      outline: 'border border-tactical-border bg-transparent hover:bg-tactical-hover text-tactical-text',
      ghost: 'hover:bg-tactical-hover text-tactical-text',
    };

    const sizeStyles = {
      default: 'h-10 py-2 px-4',
      sm: 'h-9 px-3 rounded-md',
      lg: 'h-11 px-8 rounded-md',
    };

    const combinedClassName = `${baseStyles} ${variantStyles[variant]} ${sizeStyles[size]} ${className}`;

    return <button className={combinedClassName} ref={ref} {...props} />;
  }
);

Button.displayName = 'Button';

export { Button };
