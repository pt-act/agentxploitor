"use client";

interface ResolutionStep {
  tier: number;
  name: string;
  description: string;
  status: 'pending' | 'searching' | 'found' | 'not_found';
}

interface TargetResolutionStatusProps {
  currentTier: number;
  rawInput: string;
}

const RESOLUTION_STEPS: ResolutionStep[] = [
  {
    tier: 0,
    name: 'Input Detection',
    description: 'Analyzing input type',
    status: 'pending',
  },
  {
    tier: 1,
    name: 'Warpcast Search',
    description: 'Searching for miniapp',
    status: 'pending',
  },
  {
    tier: 2,
    name: 'GitHub Search',
    description: 'Searching repositories',
    status: 'pending',
  },
  {
    tier: 3,
    name: 'Manual Input',
    description: 'Requires direct URL',
    status: 'pending',
  },
];

export default function TargetResolutionStatus({
  currentTier,
  rawInput,
}: TargetResolutionStatusProps) {
  const getStepStatus = (tier: number): ResolutionStep['status'] => {
    if (tier < currentTier) return 'found';
    if (tier === currentTier) return 'searching';
    return 'pending';
  };

  const getStatusIcon = (status: ResolutionStep['status']) => {
    switch (status) {
      case 'searching':
        return '🔄';
      case 'found':
        return '✅';
      case 'not_found':
        return '❌';
      default:
        return '⏳';
    }
  };

  const getStatusColor = (status: ResolutionStep['status']) => {
    switch (status) {
      case 'searching':
        return 'text-blue-400';
      case 'found':
        return 'text-[#00ff41]';
      case 'not_found':
        return 'text-red-400';
      default:
        return 'text-gray-500';
    }
  };

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-white">Resolving Target</h3>
      <p className="text-sm text-gray-400">
        Searching for &ldquo;{rawInput}&rdquo;
      </p>

      <div className="space-y-3">
        {RESOLUTION_STEPS.map((step) => {
          const status = getStepStatus(step.tier);
          return (
            <div
              key={step.tier}
              className={`
                flex items-center gap-3 p-3 rounded-lg border
                ${
                  status === 'searching'
                    ? 'border-blue-500/50 bg-blue-500/10'
                    : status === 'found'
                    ? 'border-[#00ff41]/50 bg-[#00ff41]/5'
                    : 'border-gray-800 bg-[#0a0e27]'
                }
              `}
            >
              <span className="text-xl animate-pulse">
                {getStatusIcon(status)}
              </span>
              <div className="flex-1">
                <div className={`font-medium ${getStatusColor(status)}`}>
                  {step.name}
                </div>
                <div className="text-xs text-gray-500">{step.description}</div>
              </div>
              {status === 'searching' && (
                <div className="flex gap-1">
                  <span className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                  <span className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                  <span className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
              )}
            </div>
          );
        })}
      </div>

      {currentTier === 3 && (
        <div className="p-4 rounded-lg bg-yellow-500/10 border border-yellow-500/50">
          <div className="flex items-start gap-3">
            <span className="text-xl">⚠️</span>
            <div>
              <div className="font-medium text-yellow-400">Could not resolve automatically</div>
              <p className="text-sm text-gray-400 mt-1">
                Please provide a direct URL or contract address
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
