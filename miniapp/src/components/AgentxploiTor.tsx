"use client";

import { useRouter } from 'next/navigation';
import { Button } from './ui/Button';

export default function AgentxploiTor() {
  const router = useRouter();
  
  return (
    <div className="min-h-screen bg-gradient-to-b from-[#0a0e27] to-[#1a1f3a] text-white">
      
      {/* Header */}
      <header className="border-b border-gray-800 bg-[#0a0e27]/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-[#00ff41] rounded-lg flex items-center justify-center">
              <span className="text-[#0a0e27] font-bold text-lg">A</span>
            </div>
            <h1 className="text-xl font-bold">AgentxploiTor</h1>
          </div>
          <Button 
            onClick={() => router.push('/request')}
            className="bg-[#00ff41] text-[#0a0e27] hover:bg-[#00dd35]"
          >
            Request Audit
          </Button>
        </div>
      </header>

      {/* Hero Section */}
      <section className="container mx-auto px-4 py-16 text-center">
        <div className="max-w-4xl mx-auto">
          <div className="inline-block px-4 py-1 bg-[#00ff41]/10 border border-[#00ff41] rounded-full text-[#00ff41] text-sm mb-6">
            ⚡ First AI Security Agent with Visual Verification
          </div>
          
          <h1 className="text-5xl md:text-6xl font-bold mb-6 bg-gradient-to-r from-[#00ff41] to-[#00aaff] bg-clip-text text-transparent">
            Autonomous Security<br />
            Audits for Solana
          </h1>
          
          <p className="text-xl text-gray-400 mb-8 max-w-2xl mx-auto">
            The only AI agent that can <span className="text-[#00ff41]">see</span> vulnerabilities, 
            <span className="text-[#00ff41]"> prove</span> they work, and 
            <span className="text-[#00ff41]"> verify</span> exploits—all autonomously.
          </p>

          <div className="flex gap-4 justify-center">
            <Button 
              onClick={() => router.push('/request')}
              className="bg-[#00ff41] text-[#0a0e27] hover:bg-[#00dd35] text-lg px-8 py-6"
            >
              Request Security Audit
            </Button>
            <Button 
              onClick={() => router.push('/audit/demo-123/results')}
              variant="outline" 
              className="border-[#00ff41] text-[#00ff41] hover:bg-[#00ff41]/10 text-lg px-8 py-6"
            >
              View Demo
            </Button>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="container mx-auto px-4 py-12">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-4xl mx-auto">
          <div className="bg-[#1a1f3a] border border-gray-800 rounded-lg p-6 text-center">
            <div className="text-4xl font-bold text-[#00ff41] mb-2">4</div>
            <div className="text-gray-400">Vulnerabilities Found</div>
            <div className="text-sm text-gray-500 mt-1">In real Solana programs</div>
          </div>
          
          <div className="bg-[#1a1f3a] border border-gray-800 rounded-lg p-6 text-center">
            <div className="text-4xl font-bold text-[#00ff41] mb-2">100%</div>
            <div className="text-gray-400">Success Rate</div>
            <div className="text-sm text-gray-500 mt-1">Autonomous verification</div>
          </div>
          
          <div className="bg-[#1a1f3a] border border-gray-800 rounded-lg p-6 text-center">
            <div className="text-4xl font-bold text-[#00ff41] mb-2">92%</div>
            <div className="text-gray-400">Confidence Score</div>
            <div className="text-sm text-gray-500 mt-1">Self-evaluation avg</div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="container mx-auto px-4 py-16">
        <h2 className="text-3xl font-bold text-center mb-12">What Makes AgentxploiTor Unique</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-6xl mx-auto">
          
          {/* Feature 1: Visual Verification */}
          <div className="bg-[#1a1f3a] border border-gray-800 rounded-lg p-8 hover:border-[#00ff41] transition-colors">
            <div className="w-12 h-12 bg-[#00ff41]/10 rounded-lg flex items-center justify-center mb-4">
              <span className="text-2xl">📸</span>
            </div>
            <h3 className="text-xl font-bold mb-3 text-[#00ff41]">Visual Proof</h3>
            <p className="text-gray-400">
              First agent that <strong>sees</strong> what it creates. Captures before/after 
              screenshots to prove exploits work—no human verification needed.
            </p>
          </div>

          {/* Feature 2: Autonomous */}
          <div className="bg-[#1a1f3a] border border-gray-800 rounded-lg p-8 hover:border-[#00ff41] transition-colors">
            <div className="w-12 h-12 bg-[#00ff41]/10 rounded-lg flex items-center justify-center mb-4">
              <span className="text-2xl">🤖</span>
            </div>
            <h3 className="text-xl font-bold mb-3 text-[#00ff41]">Autonomous</h3>
            <p className="text-gray-400">
              Makes intelligent decisions without human oversight. Discovers, exploits, 
              verifies, and reports—completely autonomously.
            </p>
          </div>

          {/* Feature 3: Solana Expert */}
          <div className="bg-[#1a1f3a] border border-gray-800 rounded-lg p-8 hover:border-[#00ff41] transition-colors">
            <div className="w-12 h-12 bg-[#00ff41]/10 rounded-lg flex items-center justify-center mb-4">
              <span className="text-2xl">⚡</span>
            </div>
            <h3 className="text-xl font-bold mb-3 text-[#00ff41]">Solana Expert</h3>
            <p className="text-gray-400">
              Specialized in Solana security. SPL tokens, DeFi protocols, NFTs—knows 
              common attack patterns and verification methods.
            </p>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="container mx-auto px-4 py-16 bg-[#0a0e27]">
        <h2 className="text-3xl font-bold text-center mb-12">How It Works</h2>
        
        <div className="max-w-4xl mx-auto">
          <div className="space-y-8">
            
            <div className="flex gap-6 items-start">
              <div className="w-12 h-12 bg-[#00ff41] rounded-full flex items-center justify-center flex-shrink-0 font-bold text-[#0a0e27]">
                1
              </div>
              <div>
                <h3 className="text-xl font-bold mb-2">Request Audit</h3>
                <p className="text-gray-400">
                  Submit your Solana program URL or contract address. Choose audit scope 
                  and priority. Pay with BNKR tokens on BASE.
                </p>
              </div>
            </div>

            <div className="flex gap-6 items-start">
              <div className="w-12 h-12 bg-[#00ff41] rounded-full flex items-center justify-center flex-shrink-0 font-bold text-[#0a0e27]">
                2
              </div>
              <div>
                <h3 className="text-xl font-bold mb-2">Agent Audits</h3>
                <p className="text-gray-400">
                  AgentxploiTor autonomously scans your code, identifies vulnerabilities, 
                  generates exploits, and executes them in a safe browser environment.
                </p>
              </div>
            </div>

            <div className="flex gap-6 items-start">
              <div className="w-12 h-12 bg-[#00ff41] rounded-full flex items-center justify-center flex-shrink-0 font-bold text-[#0a0e27]">
                3
              </div>
              <div>
                <h3 className="text-xl font-bold mb-2">Visual Verification</h3>
                <p className="text-gray-400">
                  Agent captures before/after screenshots showing the exploit worked. 
                  Compares visual state to verify success—sees what it creates.
                </p>
              </div>
            </div>

            <div className="flex gap-6 items-start">
              <div className="w-12 h-12 bg-[#00ff41] rounded-full flex items-center justify-center flex-shrink-0 font-bold text-[#0a0e27]">
                4
              </div>
              <div>
                <h3 className="text-xl font-bold mb-2">Report Delivered</h3>
                <p className="text-gray-400">
                  Receive comprehensive report with vulnerability details, visual proof, 
                  confidence scores, and remediation recommendations.
                </p>
              </div>
            </div>
          </div>

          <div className="mt-12 text-center">
            <Button 
              onClick={() => router.push('/request')}
              className="bg-[#00ff41] text-[#0a0e27] hover:bg-[#00dd35] text-lg px-12 py-6"
            >
              Start Your Audit Now
            </Button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-gray-800 bg-[#0a0e27] py-8">
        <div className="container mx-auto px-4 text-center text-gray-500">
          <p>MIT Licensed | Built on BASE | Powered by AgentxploiTor</p>
          <p className="text-sm mt-2">
            Autonomous AI Security • Visual Exploit Verification • Solana Expertise
          </p>
        </div>
      </footer>

    </div>
  );
}
