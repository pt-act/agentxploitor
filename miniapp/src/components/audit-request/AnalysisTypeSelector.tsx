"use client";

export type AnalysisType = 'contract' | 'frontend' | 'full_stack';

interface AnalysisOption {
  id: AnalysisType;
  title: string;
  description: string;
  icon: string;
  surfaces: string[];
  price: {
    eth: string;
    bnkr: string;
  };
}

const ANALYSIS_OPTIONS: AnalysisOption[] = [
  {
    id: 'contract',
    title: 'Smart Contract',
    description: 'Static analysis of smart contracts',
    icon: '📜',
    surfaces: ['Slither', 'Mythril', 'Bytecode'],
    price: { eth: '$79', bnkr: '$63' },
  },
  {
    id: 'frontend',
    title: 'Frontend UI',
    description: 'Browser-based security analysis',
    icon: '🖥️',
    surfaces: ['CSP Headers', 'Wallet Connect', 'XSS Vectors'],
    price: { eth: '$79', bnkr: '$63' },
  },
  {
    id: 'full_stack',
    title: 'Full Stack',
    description: 'Complete audit of contracts + frontend',
    icon: '🎯',
    surfaces: ['All Contract Checks', 'All UI Checks', 'Integration'],
    price: { eth: '$349', bnkr: '$279' },
  },
];

interface AnalysisTypeSelectorProps {
  value?: AnalysisType;
  onChange: (type: AnalysisType) => void;
  allowedTypes?: AnalysisType[];
  disabled?: boolean;
}

export default function AnalysisTypeSelector({
  value,
  onChange,
  allowedTypes,
  disabled,
}: AnalysisTypeSelectorProps) {
  const availableTypes = allowedTypes
    ? ANALYSIS_OPTIONS.filter((opt) => allowedTypes.includes(opt.id))
    : ANALYSIS_OPTIONS;

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-white">Analysis Type</h3>
      <p className="text-sm text-gray-400">
        Choose what to audit
      </p>

      <div className="grid gap-4 sm:grid-cols-3">
        {availableTypes.map((option) => (
          <button
            key={option.id}
            type="button"
            onClick={() => !disabled && onChange(option.id)}
            disabled={disabled}
            className={`
              relative p-4 rounded-xl border-2 text-left transition-all
              ${
                value === option.id
                  ? 'border-[#00ff41] bg-[#00ff41]/10'
                  : 'border-gray-700 bg-[#0a0e27] hover:border-gray-600'
              }
              ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
            `}
          >
            <div className="text-2xl mb-2">{option.icon}</div>
            <h4 className="font-semibold text-white">{option.title}</h4>
            <p className="text-xs text-gray-400 mt-1">{option.description}</p>

            <div className="mt-3 space-y-1">
              {option.surfaces.map((surface, idx) => (
                <div key={idx} className="text-xs text-gray-500 flex items-center gap-1">
                  <span className="text-[#00ff41]">•</span>
                  {surface}
                </div>
              ))}
            </div>

            <div className="mt-4 pt-3 border-t border-gray-700">
              <div className="flex justify-between items-center">
                <span className="text-xs text-gray-500">ETH/USDC</span>
                <span className="font-bold text-white">{option.price.eth}</span>
              </div>
              <div className="flex justify-between items-center mt-1">
                <span className="text-xs text-gray-500">BNKR (20% off)</span>
                <span className="font-bold text-[#00ff41]">{option.price.bnkr}</span>
              </div>
            </div>

            {value === option.id && (
              <div className="absolute top-2 right-2 w-3 h-3 bg-[#00ff41] rounded-full animate-pulse" />
            )}
          </button>
        ))}
      </div>
    </div>
  );
}

export { ANALYSIS_OPTIONS };
