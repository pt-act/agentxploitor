"""
E2B Sandbox Runner for AgentxploiTor

Provides isolated execution environment for dynamic analysis:
- AIExploitGenerator outputs
- Dynamic contract interaction
- Tool execution that requires network/filesystem

Environment Variables:
- E2B_API_KEY: Your E2B API key (required)
- E2B_TIMEOUT: Max sandbox lifetime in seconds (default: 300 = 5 minutes)
"""

import os
import asyncio
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime

try:
    import e2b
except ImportError:
    e2b = None


# ─── Config ───────────────────────────────────────────────────────────────────

SANDBOX_TIMEOUT = int(os.getenv("E2B_TIMEOUT", "300"))  # 5 minutes max
SANDBOX_TEMPLATE = "python3"  # Base Python template

# Install these tools in every sandbox
DEFAULT_PACKAGES = [
    "slither-analyzer",
    "mythril",
    "web3",
    "eth-abi",
]


# ─── Types ────────────────────────────────────────────────────────────────────

@dataclass
class SandboxResult:
    success: bool
    stdout: str
    stderr: str
    exit_code: int
    duration_ms: int
    error: Optional[str] = None


@dataclass
class SandboxConfig:
    timeout: int = SANDBOX_TIMEOUT
    packages: Optional[List[str]] = None
    env: Optional[Dict[str, str]] = None

    def __post_init__(self):
        if self.packages is None:
            self.packages = DEFAULT_PACKAGES.copy()
        if self.env is None:
            self.env = {}


# ─── Sandbox Runner ───────────────────────────────────────────────────────────

class E2BSandboxRunner:
    """
    Manages E2B sandbox instances for secure dynamic analysis.
    
    Features:
    - Automatic cleanup on timeout/completion
    - Tool installation before analysis
    - Timeout enforcement
    - STDERR capture
    """

    def __init__(self, config: Optional[SandboxConfig] = None):
        if e2b is None:
            raise ImportError(
                "E2B package not installed. Install with: pip install e2b"
            )

        self.config = config or SandboxConfig()
        self._sandbox: Optional[Any] = None
        self._started_at: Optional[datetime] = None

    async def __aenter__(self):
        """Context manager entry - creates sandbox"""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensures cleanup"""
        await self.stop()

    async def start(self) -> None:
        """Start a new E2B sandbox instance"""
        if self._sandbox is not None:
            return

        api_key = os.getenv("E2B_API_KEY")
        if not api_key:
            raise ValueError("E2B_API_KEY environment variable is required")

        try:
            # Create sandbox with timeout
            self._sandbox = await e2b.AsyncSandbox.create(
                timeout=self.config.timeout,
                # template=SANDBOX_TEMPLATE,  # Use default Python template
            )
            self._started_at = datetime.utcnow()

            # Install default security tools
            await self._install_packages()

        except Exception as e:
            self._sandbox = None
            raise RuntimeError(f"Failed to create E2B sandbox: {e}")

    async def stop(self) -> None:
        """Stop and cleanup the sandbox"""
        if self._sandbox is not None:
            try:
                await self._sandbox.kill()
            except Exception:
                pass  # Best effort cleanup
            finally:
                self._sandbox = None
                self._started_at = None

    async def _install_packages(self) -> None:
        """Install security analysis tools in sandbox"""
        if not self._sandbox:
            return

        # Install pip first
        await self._sandbox.commands.run("pip install --upgrade pip")

        # Install packages in batches to avoid timeouts
        packages = self.config.packages or []
        for package in packages:
            try:
                result = await self._sandbox.commands.run(
                    f"pip install {package} --quiet",
                    timeout=60  # 1 min per package
                )
                if result.exit_code != 0:
                    print(f"Warning: Failed to install {package}: {result.stderr}")
            except Exception as e:
                print(f"Warning: Error installing {package}: {e}")

    async def run_command(
        self,
        command: str,
        timeout: Optional[int] = None
    ) -> SandboxResult:
        """
        Execute a command in the sandbox.
        
        Args:
            command: Shell command to run
            timeout: Override default timeout (seconds)
            
        Returns:
            SandboxResult with stdout, stderr, exit code
        """
        if not self._sandbox:
            raise RuntimeError("Sandbox not started. Call start() first.")

        start_time = datetime.utcnow()
        effective_timeout = timeout or (self.config.timeout // 2)  # Half of sandbox lifetime

        try:
            result = await self._sandbox.commands.run(
                command,
                timeout=effective_timeout
            )

            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

            return SandboxResult(
                success=result.exit_code == 0,
                stdout=result.stdout or "",
                stderr=result.stderr or "",
                exit_code=result.exit_code,
                duration_ms=duration_ms,
            )

        except asyncio.TimeoutError:
            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            return SandboxResult(
                success=False,
                stdout="",
                stderr=f"Command timed out after {effective_timeout}s",
                exit_code=-1,
                duration_ms=duration_ms,
                error="timeout"
            )

        except Exception as e:
            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            return SandboxResult(
                success=False,
                stdout="",
                stderr=str(e),
                exit_code=-1,
                duration_ms=duration_ms,
                error=str(e)
            )

    async def run_slither(self, contract_code: str) -> SandboxResult:
        """
        Run Slither static analysis on contract code.
        
        Args:
            contract_code: Solidity contract source code
            
        Returns:
            SandboxResult with Slither JSON output
        """
        # Write contract to temp file
        write_result = await self.run_command(
            f"cat > /tmp/contract.sol << 'EOF'\n{contract_code}\nEOF"
        )
        if not write_result.success:
            return write_result

        # Run Slither
        return await self.run_command(
            "slither /tmp/contract.sol --json -",
            timeout=120
        )

    async def run_mythril(self, contract_address: str, chain: str = "base") -> SandboxResult:
        """
        Run Mythril symbolic analysis on a contract.
        
        Args:
            contract_address: EVM contract address
            chain: Blockchain name (base, ethereum, etc.)
            
        Returns:
            SandboxResult with Mythril analysis output
        """
        return await self.run_command(
            f"mythril analyze -a {contract_address} --chain {chain} --json",
            timeout=180
        )


# ─── Helper Functions ─────────────────────────────────────────────────────────

async def run_in_sandbox(
    command: str,
    timeout: Optional[int] = None,
    config: Optional[SandboxConfig] = None
) -> SandboxResult:
    """
    Convenience function to run a command in an ephemeral sandbox.
    
    Usage:
        result = await run_in_sandbox("slither /tmp/contract.sol --json -")
        if result.success:
            print(result.stdout)
    """
    async with E2BSandboxRunner(config) as runner:
        return await runner.run_command(command, timeout)


# ─── HexStrike Integration Hook ─────────────────────────────────────────────

# This would be called by HexStrike's AIExploitGenerator
# when it needs to execute dynamic analysis:

async def hexstrike_dynamic_analysis(
    contract_address: str,
    analysis_type: str,
    chain: str = "base"
) -> Dict[str, Any]:
    """
    HexStrike hook for dynamic analysis in E2B sandbox.
    
    Called by AIExploitGenerator when it wants to:
    - Execute contract functions
    - Run symbolic analysis
    - Generate proof-of-concept exploits
    """
    async with E2BSandboxRunner() as runner:
        if analysis_type == "slither":
            result = await runner.run_mythril(contract_address, chain)
        elif analysis_type == "mythril":
            result = await runner.run_mythril(contract_address, chain)
        else:
            return {
                "success": False,
                "error": f"Unknown analysis type: {analysis_type}"
            }

        return {
            "success": result.success,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.exit_code,
            "duration_ms": result.duration_ms,
        }


# ─── Main (Testing) ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    async def test():
        print("Testing E2B sandbox...")
        
        # Check API key
        if not os.getenv("E2B_API_KEY"):
            print("WARNING: E2B_API_KEY not set. Set it to run tests.")
            print("Get your API key from https://e2b.dev/dashboard")
            return

        async with E2BSandboxRunner() as runner:
            # Test command
            result = await runner.run_command("echo 'Hello from E2B!'")
            print(f"Result: {result.stdout}")
            print(f"Success: {result.success}")

    asyncio.run(test())
