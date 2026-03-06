"use client";

import { useState } from 'react';

export type Persona = 'researcher' | 'developer' | 'contract_dev';

interface PersonaOption {
  id: Persona;
  title: string;
  description: string;
  icon: string;
  features: string[];
}

const PERSONA_OPTIONS: PersonaOption[] = [
  {
    id: 'researcher',
    title: 'Security Researcher',
    description: 'Find bugs in other miniapps for bounties',
    icon: '🔍',
    features: [
      'Audit any public miniapp',
      'Generate responsible disclosure',
      'Build bug bounty portfolio',
    ],
  },
  {
    id: 'developer',
    title: 'Miniapp Developer',
    description: 'Audit your own app before launch',
    icon: '🛠️',
    features: [
      'Self-audit mode',
      'Priority support',
      'Fix recommendations',
    ],
  },
  {
    id: 'contract_dev',
    title: 'Contract Developer',
    description: 'Audit contracts for miniapp integrations',
    icon: '📜',
    features: [
      'Smart contract analysis',
      'Slither + Mythril reports',
      'Integration guidance',
    ],
  },
];

interface PersonaSelectorProps {
  value?: Persona;
  onChange: (persona: Persona) => void;
  disabled?: boolean;
}

export default function PersonaSelector({ value, onChange, disabled }: PersonaSelectorProps) {
  const [selected, setSelected] = useState<Persona | undefined>(value);

  const handleSelect = (persona: Persona) => {
    if (disabled) return;
    setSelected(persona);
    onChange(persona);
  };

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-white">Select Your Role</h3>
      <p className="text-sm text-gray-400">
        Choose how you want to use AgentxploiTor
      </p>

      <div className="grid gap-4 sm:grid-cols-3">
        {PERSONA_OPTIONS.map((option) => (
          <button
            key={option.id}
            type="button"
            onClick={() => handleSelect(option.id)}
            disabled={disabled}
            className={`
              relative p-4 rounded-xl border-2 text-left transition-all
              ${
                selected === option.id
                  ? 'border-[#00ff41] bg-[#00ff41]/10'
                  : 'border-gray-700 bg-[#0a0e27] hover:border-gray-600'
              }
              ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
            `}
          >
            <div className="text-2xl mb-2">{option.icon}</div>
            <h4 className="font-semibold text-white">{option.title}</h4>
            <p className="text-xs text-gray-400 mt-1">{option.description}</p>
            
            <ul className="mt-3 space-y-1">
              {option.features.map((feature, idx) => (
                <li key={idx} className="text-xs text-gray-500 flex items-center gap-1">
                  <span className="text-[#00ff41]">✓</span>
                  {feature}
                </li>
              ))}
            </ul>

            {selected === option.id && (
              <div className="absolute top-2 right-2 w-3 h-3 bg-[#00ff41] rounded-full animate-pulse" />
            )}
          </button>
        ))}
      </div>
    </div>
  );
}

export { PERSONA_OPTIONS };
