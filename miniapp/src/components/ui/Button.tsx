interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  children: React.ReactNode;
  isLoading?: boolean;
  variant?: 'default' | 'outline' | 'ghost' | 'destructive';
}

export function Button({ 
  children, 
  className = "", 
  isLoading = false, 
  variant = 'default',
  ...props 
}: ButtonProps) {
  const variantStyles = {
    default: 'bg-primary text-primary-foreground hover:bg-primary/90',
    outline: 'bg-transparent border border-gray-600 text-white hover:bg-gray-800',
    ghost: 'bg-transparent text-white hover:bg-gray-800/50',
    destructive: 'bg-red-600 text-white hover:bg-red-700',
  };
  
  return (
    <button
      className={`w-full max-w-xs mx-auto block py-3 px-6 rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 ${variantStyles[variant]} ${className}`}
      {...props}
    >
      {isLoading ? (
        <div className="flex items-center justify-center">
          <div className="animate-spin h-5 w-5 border-2 border-current border-t-transparent rounded-full" />
        </div>
      ) : (
        children
      )}
    </button>
  );
}
