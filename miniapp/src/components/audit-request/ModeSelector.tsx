"use client";

import { Persona } from './PersonaSelector';

export type AuditMode = 'self_audit' | 'research' | 'contract';

interface ModeOption {
  id: AuditMode;
  title: string;
  description: string;
  icon: string;
  rateLimit: string;
  requirements: string[];
  persona: Persona[];
}

const MODE_OPTIONS: ModeOption[] = [
  {
    id: 'self_audit',
    title: 'Self-Audit',
    description: 'Audit your own miniapp or contracts',
    icon: '🔐',
    rateLimit: '20 audits/hour',
    requirements: ['You own the target', 'No discovery needed'],
    persona: ['developer'],
  },
  {
    id: 'research',
    title: 'Research',
    description: 'Audit other miniapps responsibly',
    icon: '🔬',
    rateLimit: '5 audits/hour',
    requirements: ['Public targets only', 'Responsible disclosure'],
    persona: ['researcher'],
  },
  {
    id: 'contract',
    title: 'Contract Audit',
    description: 'Deep contract analysis',
    icon: '📋',
    rateLimit: '10 audits/hour',
    requirements: ['Any contract address', 'GitHub repo optional'],
    persona: ['contract_dev', 'developer'],
  },
];

interface ModeSelectorProps {
  value?: AuditMode;
  onChange: (mode: AuditMode) => void;
  allowedModes?: AuditMode[];
  disabled?: boolean;
}

export default function ModeSelector({ 
  value, 
  onChange, 
  allowedModes,
  disabled 
}: ModeSelectorProps) {
  const availableModes = allowedModes 
    ? MODE_OPTIONS.filter(m => allowedModes.includes(m.id))
    : MODE_OPTIONS;

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-white">Audit Mode</h3>
      <p className="text-sm text-gray-400">
        Select the type of audit you want to perform
      </p>

      <div className="space-y-3">
        {availableModes.map((option) => (
          <button
            key={option.id}
            type="button"
            onClick={() => !disabled && onChange(option.id)}
            disabled={disabled}
            className={`
              w-full p-4 rounded-xl border-2 text-left transition-all
              ${
                value === option.id
                  ? 'border-[#00ff41] bg-[#00ff41]/10'
                  : 'border-gray-700 bg-[#0a0e27] hover:border-gray-600'
              }
              ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
            `}
          >
            <div className="flex items-start gap-3">
              <span className="text-2xl">{option.icon}</span>
              <div className="flex-1">
                <div className="flex items-center justify-between">
                  <h4 className="font-semibold text-white">{option.title}</h4>
                  <span className="text-xs text-gray-500">{option.rateLimit}</span>
                </div>
                <p className="text-sm text-gray-400 mt-1">{option.description}</p>
                
                <div className="flex flex-wrap gap-2 mt-2">
                  {option.requirements.map((req, idx) => (
                    <span 
                      key={idx}
                      className="text-xs px-2 py-1 bg-gray-800 text-gray-300 rounded"
                    >
                      {req}
                    </span>
                  ))}
                </div>
              </div>
            </div>

            {value === option.id && (
              <div className="absolute top-2 right-2 w-3 h-3 bg-[#00ff41] rounded-full" />
            )}
          </button>
        ))}
      </div>
    </div>
  );
}

export { MODE_OPTIONS };
