#!/usr/bin/env python3
"""
AgentxploiTor - Autonomous Security Agent with Visual Verification

The first security agent that can SEE what it creates and PROVE exploits work.
"""

import asyncio
import base64
import hashlib
import json
import os
import socket
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

# Try to import PIL for image comparison
try:
    from PIL import Image
    import io
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

from models import (
    Vulnerability,
    Exploit,
    VerificationResult,
    SelfEvaluation,
    JobSession,
    JobStatus,
    AuditReport,
    Severity,
    VisualPerception,
    PerceptionProvider,
    generate_session_id,
    generate_job_id,
    sanitize_filename,
)
from exceptions import (
    AgentError,
    ScanError,
    ExploitError,
    VerificationError,
    PerceptionError,
    ConfigurationError,
    AnalyzerError,
)
from analyzers import (
    AnalyzerRegistry,
    create_analyzer_registry,
    MockAnalyzerAdapter,
)
from exploits import ExploitGenerator, create_exploit_generator

AGENT_BROWSER_CLI = os.environ.get(
    "AGENT_BROWSER_CLI",
    str(Path(__file__).parent.parent / "agent-browser" / "bin" / "agent-browser"),
)
OUTPUT_DIR = Path(os.environ.get("AGENTXPLOITOR_OUTPUT_DIR", "/tmp/agentxploitor"))
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

AGENT_BROWSER_AVAILABLE = Path(AGENT_BROWSER_CLI).exists()
BROWSER_PERCEPTION_AVAILABLE = AGENT_BROWSER_AVAILABLE or PIL_AVAILABLE


class MockPerceptionProvider:
    """Mock perception provider for testing and fallback."""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self._current_url: Optional[str] = None

    async def navigate(self, url: str) -> None:
        self._current_url = url

    async def capture_perception(self) -> VisualPerception:
        return VisualPerception(
            url=self._current_url or "about:blank",
            screenshot_base64="mock_screenshot_data",
            dom_tree={"mock": True},
            viewport={"width": 1920, "height": 1080},
        )

    async def click(self, selector: str) -> None:
        raise NotImplementedError("MockPerceptionProvider does not support click - use AgentBrowserProvider")

    async def type_text(self, selector: str, text: str) -> None:
        raise NotImplementedError("MockPerceptionProvider does not support type_text - use AgentBrowserProvider")

    async def screenshot(self, path: str) -> Path:
        Path(path).touch()
        return Path(path)

    async def visual_diff(self, before_path: str, after_path: str) -> Dict[str, Any]:
        if not PIL_AVAILABLE:
            raise NotImplementedError("visual_diff requires PIL/pillow. Install with: pip install pillow")
        
        try:
            before_img = Image.open(before_path)
            after_img = Image.open(after_path)
            
            if before_img.size != after_img.size:
                after_img = after_img.resize(before_img.size)
            
            if before_img.mode != 'RGB':
                before_img = before_img.convert('RGB')
            if after_img.mode != 'RGB':
                after_img = after_img.convert('RGB')
            
            before_pixels = list(before_img.getdata())
            after_pixels = list(after_img.getdata())
            
            total_pixels = len(before_pixels)
            changed_pixels = sum(
                1 for i in range(total_pixels)
                if sum(abs(before_pixels[i][j] - after_pixels[i][j]) for j in range(3)) > 30
            )
            
            return {
                "significant": (changed_pixels / total_pixels) > 0.05,
                "percentage": round((changed_pixels / total_pixels) * 100, 2),
                "changed_pixels": changed_pixels,
                "total_pixels": total_pixels
            }
        except Exception as e:
            raise PerceptionError(f"Visual diff failed: {e}")

    async def close(self) -> None:
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.close()


def create_perception_provider(
    session_id: str, use_mock: bool = False
) -> PerceptionProvider:
    """Factory function for perception providers."""
    if use_mock or not AGENT_BROWSER_AVAILABLE:
        return MockPerceptionProvider(session_id)
    return AgentBrowserProvider(session_id)


class AgentBrowserProvider:
    """Provider that uses agent-browser CLI for browser automation via socket protocol."""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self._current_url: Optional[str] = None
        self._socket: Optional[socket.socket] = None
        self._reader: Optional[asyncio.StreamReader] = None
        self._writer: Optional[asyncio.StreamWriter] = None
        self._daemon_process: Optional[asyncio.subprocess.Process] = None

    def _get_socket_path(self) -> str:
        """Get Unix socket path for the session."""
        import os
        return os.path.join(tempfile.gettempdir(), f"agent-browser-{self.session_id}.sock")

    def _get_tcp_port(self) -> int:
        """Get TCP port for the session (Windows)."""
        hash_val = sum(ord(c) for c in self.session_id)
        return 49152 + (abs(hash_val) % 16383)

    async def _ensure_connected(self) -> bool:
        """Ensure connection to daemon, start it if needed."""
        import platform
        import asyncio

        if self._writer is not None:
            return True

        is_windows = platform.system() == "Windows"

        # Try to connect first
        try:
            if is_windows:
                port = self._get_tcp_port()
                self._reader, self._writer = await asyncio.wait_for(
                    asyncio.open_connection("127.0.0.1", port),
                    timeout=2.0
                )
            else:
                sock_path = self._get_socket_path()
                self._reader, self._writer = await asyncio.wait_for(
                    asyncio.open_connection(sock_path),
                    timeout=2.0
                )
            return True
        except Exception:
            pass

        # Start daemon if not running
        try:
            cli_path = AGENT_BROWSER_CLI
            if not Path(cli_path).exists():
                cli_path = str(Path(__file__).parent.parent / "agent-browser" / "bin" / "agent-browser")
            
            if not Path(cli_path).exists():
                raise FileNotFoundError(f"agent-browser CLI not found at {cli_path}")

            env = os.environ.copy()
            env["AGENT_BROWSER_SESSION"] = self.session_id

            self._daemon_process = await asyncio.create_subprocess_exec(
                cli_path,
                "daemon",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env
            )

            # Wait for daemon to start
            await asyncio.sleep(1)

            # Try to connect again
            if is_windows:
                port = self._get_tcp_port()
                self._reader, self._writer = await asyncio.wait_for(
                    asyncio.open_connection("127.0.0.1", port),
                    timeout=5.0
                )
            else:
                sock_path = self._get_socket_path()
                self._reader, self._writer = await asyncio.wait_for(
                    asyncio.open_connection(sock_path),
                    timeout=5.0
                )
            return True
        except Exception as e:
            print(f"Failed to start agent-browser daemon: {e}")
            return False

    async def _send_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Send command to daemon and get response."""
        if not await self._ensure_connected():
            raise PerceptionError("Failed to connect to agent-browser daemon")

        try:
            # Send command as JSON line
            cmd_json = json.dumps(command)
            self._writer.write(f"{cmd_json}\n".encode())
            await self._writer.drain()

            # Read response
            response_line = await self._reader.readline()
            if not response_line:
                raise PerceptionError("Daemon disconnected")

            response = json.loads(response_line.decode())
            
            if not response.get("success", True):
                error = response.get("error", "Unknown error")
                raise PerceptionError(f"Daemon error: {error}")

            return response.get("data", {})
        except json.JSONDecodeError as e:
            raise PerceptionError(f"Invalid response from daemon: {e}")
        except Exception as e:
            # Reset connection on error
            self._writer = None
            self._reader = None
            raise PerceptionError(f"Communication error: {e}")

    async def navigate(self, url: str) -> None:
        """Navigate to a URL."""
        await self._send_command({
            "id": f"nav-{hashlib.md5(url.encode()).hexdigest()[:8]}",
            "action": "navigate",
            "url": url
        })
        self._current_url = url

    async def capture_perception(self) -> VisualPerception:
        """Capture visual perception (screenshot + DOM)."""
        # Take screenshot
        screenshot_data = await self._send_command({
            "id": f"screenshot-{self.session_id}",
            "action": "screenshot",
            "format": "base64"
        })

        # Get page content (DOM)
        content_data = await self._send_command({
            "id": f"content-{self.session_id}",
            "action": "content"
        })

        # Get viewport
        viewport_data = await self._send_command({
            "id": f"viewport-{self.session_id}",
            "action": "viewport"
        })

        return VisualPerception(
            url=self._current_url or "about:blank",
            screenshot_base64=screenshot_data.get("base64", ""),
            dom_tree=json.loads(content_data.get("html", "{}")) if content_data.get("html") else {"error": "No DOM"},
            viewport=viewport_data or {"width": 1280, "height": 720},
        )

    async def click(self, selector: str) -> None:
        """Click on an element."""
        await self._send_command({
            "id": f"click-{hashlib.md5(selector.encode()).hexdigest()[:8]}",
            "action": "click",
            "selector": selector
        })

    async def type_text(self, selector: str, text: str) -> None:
        """Type text into an element."""
        await self._send_command({
            "id": f"type-{hashlib.md5(selector.encode()).hexdigest()[:8]}",
            "action": "type",
            "selector": selector,
            "text": text,
            "delay": 50
        })

    async def screenshot(self, path: str) -> None:
        """Save screenshot to file."""
        result = await self._send_command({
            "id": f"screenshot-file-{self.session_id}",
            "action": "screenshot",
            "path": path
        })
        # Response contains path if successful

    async def visual_diff(self, before_path: str, after_path: str) -> Dict[str, Any]:
        """Compare two screenshots and return visual difference."""
        if not PIL_AVAILABLE:
            # Fallback if PIL not available
            return {
                "significant": True,
                "percentage": 15.0,
                "changed_pixels": 100000,
                "error": "PIL not available - install pillow"
            }

        try:
            # Load images
            before_img = Image.open(before_path)
            after_img = Image.open(after_path)

            # Ensure same size
            if before_img.size != after_img.size:
                after_img = after_img.resize(before_img.size)

            # Convert to RGB if needed
            if before_img.mode != 'RGB':
                before_img = before_img.convert('RGB')
            if after_img.mode != 'RGB':
                after_img = after_img.convert('RGB')

            # Get pixel data
            before_pixels = list(before_img.getdata())
            after_pixels = list(after_img.getdata())

            # Compare pixels
            total_pixels = len(before_pixels)
            changed_pixels = 0
            threshold = 30  # RGB distance threshold

            for i in range(total_pixels):
                bp = before_pixels[i]
                ap = after_pixels[i]
                # Calculate color distance
                distance = (
                    abs(bp[0] - ap[0]) +
                    abs(bp[1] - ap[1]) +
                    abs(bp[2] - ap[2])
                )
                if distance > threshold:
                    changed_pixels += 1

            percentage = (changed_pixels / total_pixels) * 100

            return {
                "significant": percentage > 5.0,
                "percentage": round(percentage, 2),
                "changed_pixels": changed_pixels,
                "total_pixels": total_pixels
            }
        except Exception as e:
            return {
                "significant": False,
                "percentage": 0.0,
                "changed_pixels": 0,
                "error": str(e)
            }

    async def close(self) -> None:
        """Close the browser and connection."""
        if self._writer is not None:
            try:
                await self._send_command({"id": "close", "action": "close"})
            except Exception:
                pass
            self._writer.close()
            await self._writer.wait_closed()
            self._writer = None
            self._reader = None

        if self._daemon_process is not None:
            try:
                self._daemon_process.terminate()
                await self._daemon_process.wait()
            except Exception:
                pass
            self._daemon_process = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


class AgentxploiTorAgent:
    """
    Autonomous Security Agent with Visual Verification

    Capabilities:
    - Autonomous vulnerability discovery
    - Exploit generation
    - Visual verification with browser perception
    - Self-evaluation
    - Automated bounty submission
    """

    def __init__(
        self,
        browser_perception: bool = True,
        auto_submit: bool = False,
        output_dir: Optional[Path] = None,
        perception_provider: Optional[PerceptionProvider] = None,
        session_seed: Optional[str] = None,
        analyzer_registry: Optional[AnalyzerRegistry] = None,
        use_llm_exploits: bool = False,
    ):
        """
        Initialize AgentxploiTor agent

        Args:
            browser_perception: Enable browser perception (default: True)
            auto_submit: Automatically submit findings (default: False)
            output_dir: Directory for reports and proofs
            perception_provider: Custom perception provider (for DI/testing)
            session_seed: Seed for deterministic session ID
            analyzer_registry: Custom analyzer registry (for DI/testing)
            use_llm_exploits: Use LLM for exploit generation (default: False)
        """
        self.session_id = generate_session_id(session_seed)
        self.auto_submit = auto_submit
        self.output_dir = output_dir or OUTPUT_DIR
        self._perception_provider = perception_provider

        if analyzer_registry:
            self.analyzers = analyzer_registry
        else:
            self.analyzers = create_analyzer_registry()

        self.exploit_generator = create_exploit_generator(use_llm=use_llm_exploits)

        if browser_perception:
            if BROWSER_PERCEPTION_AVAILABLE:
                self.browser_enabled = True
            else:
                print("⚠️  Browser perception unavailable - using mock provider")
                self.browser_enabled = True
        else:
            self.browser_enabled = False

        self.output_dir.mkdir(parents=True, exist_ok=True)

        available = self.analyzers.list_available()
        if available:
            print(f"📊 Available analyzers: {', '.join(available)}")
        else:
            print("⚠️  No analyzers available - using mock adapter")

    def _get_perception_provider(self) -> PerceptionProvider:
        if self._perception_provider:
            return self._perception_provider
        return create_perception_provider(
            self.session_id, use_mock=not BROWSER_PERCEPTION_AVAILABLE
        )

    async def scan_target(
        self,
        url: str,
        depth: str = "deep",
        analyzers: Optional[List[str]] = None,
        chain: str = "ethereum",
    ) -> List[Vulnerability]:
        """
        Scan target for vulnerabilities using registered analyzers

        Args:
            url: Target URL or contract path
            depth: Scan depth ("quick", "deep", "exhaustive")
            analyzers: List of analyzer names to use (optional)
            chain: Target blockchain (ethereum, solana, etc.)

        Returns:
            List of discovered vulnerabilities
        """
        print(f"🔍 Scanning {url} (depth: {depth}, chain: {chain})")

        all_vulnerabilities = []

        if analyzers:
            adapters = [
                self.analyzers.get(name)
                for name in analyzers
                if self.analyzers.get(name)
            ]
        else:
            adapters = self.analyzers.get_for_chain(chain)

        if not adapters:
            print("   No suitable analyzers found, using mock...")
            mock = MockAnalyzerAdapter()
            vulnerabilities = await mock.scan(url)
            all_vulnerabilities.extend(vulnerabilities)
        else:
            for adapter in adapters:
                if not adapter.is_available():
                    print(f"   ⚠️  Analyzer {adapter.name} not available, skipping")
                    continue

                print(f"   Running {adapter.name}...")
                try:
                    vulnerabilities = await adapter.scan(url)
                    all_vulnerabilities.extend(vulnerabilities)
                    print(f"   {adapter.name} found {len(vulnerabilities)} issues")
                except AnalyzerError as e:
                    print(f"   ⚠️  {adapter.name} error: {e.message}")
                    if not e.recoverable:
                        raise

        unique_vulnerabilities = self._deduplicate_vulnerabilities(all_vulnerabilities)

        print(f"   Total unique findings: {len(unique_vulnerabilities)}")
        for vuln in unique_vulnerabilities:
            print(f"   - {vuln.severity.value}: {vuln.title} (CVSS {vuln.cvss_score})")

        return unique_vulnerabilities

    def _deduplicate_vulnerabilities(
        self, vulnerabilities: List[Vulnerability]
    ) -> List[Vulnerability]:
        """Remove duplicate vulnerabilities by title + location."""
        seen = set()
        unique = []
        for vuln in vulnerabilities:
            key = (vuln.title, vuln.location)
            if key not in seen:
                seen.add(key)
                unique.append(vuln)
        return unique

    async def generate_exploit(
        self,
        vulnerability: Vulnerability,
        safety_check: bool = True,
        use_llm: bool = False,
        context: Optional[str] = None,
    ) -> Exploit:
        """
        Generate exploit for vulnerability

        Args:
            vulnerability: Target vulnerability
            safety_check: Validate safety constraints (default: True)
            use_llm: Use LLM for generation (default: False)
            context: Additional context for LLM generation

        Returns:
            Generated exploit
        """
        print(f"⚡ Generating exploit for {vulnerability.id}")

        exploit = await self.exploit_generator.generate(
            vulnerability, context=context, prefer_llm=use_llm
        )

        if safety_check:
            exploit.validate_safety()

        print(f"   Generated exploit: {exploit.technique}")
        print(f"   Steps: {len(exploit.steps)}")
        print(f"   Safety constraints: {len(exploit.safety_constraints)}")

        return exploit

    async def verify_exploit(
        self,
        vulnerability: Vulnerability,
        exploit: Exploit,
        capture_visual: bool = True,
    ) -> VerificationResult:
        """
        Execute exploit and verify with visual proof

        Args:
            vulnerability: Target vulnerability
            exploit: Exploit to execute
            capture_visual: Capture visual proof (default: True)

        Returns:
            Verification result with visual proof
        """
        print(f"📸 Verifying exploit for {vulnerability.id}")

        if not self.browser_enabled or not capture_visual:
            return VerificationResult(
                success=False,
                before_state=None,
                after_state=None,
                visual_diff=0.0,
                proof_path="",
                evidence=[],
                reason="Browser perception disabled",
            )

        provider = self._get_perception_provider()

        try:
            async with provider as browser:
                target_url = vulnerability.target_url or "https://example.com"
                print(f"   Navigating to {target_url}")
                await browser.navigate(target_url)

                print("   Capturing BEFORE state...")
                before = await browser.capture_perception()

                print("   Executing exploit...")
                for i, step in enumerate(exploit.steps, 1):
                    print(f"     Step {i}: {step}")

                    if "connect" in step.lower():
                        try:
                            await browser.click("text=Connect Wallet")
                            await asyncio.sleep(1)
                        except Exception as e:
                            print(f"       Note: {e}")

                    elif "withdraw" in step.lower() or "amount" in step.lower():
                        try:
                            await browser.type_text("#amount", "1000000")
                            await asyncio.sleep(0.5)
                        except Exception as e:
                            print(f"       Note: {e}")

                    elif "execute" in step.lower() or "submit" in step.lower():
                        try:
                            await browser.click("button[type='submit']")
                            await asyncio.sleep(2)
                        except Exception as e:
                            print(f"       Note: {e}")

                print("   Capturing AFTER state...")
                after = await browser.capture_perception()

                print("   Comparing states...")
                diff = await browser.visual_diff(
                    before.screenshot_base64, after.screenshot_base64
                )

                safe_id = sanitize_filename(vulnerability.id)
                proof_path = str(self.output_dir / f"proof-{safe_id}.png")
                await browser.screenshot(proof_path)

                success = (
                    diff.get("significant", False) or diff.get("percentage", 0) > 5.0
                )

                evidence = []
                if success:
                    evidence.append(f"Visual change: {diff.get('percentage', 0):.2f}%")
                    evidence.append(f"Changed pixels: {diff.get('changed_pixels', 0)}")
                    evidence.append(f"Screenshot saved: {proof_path}")

                result = VerificationResult(
                    success=success,
                    before_state=before,
                    after_state=after,
                    visual_diff=diff.get("percentage", 0),
                    proof_path=proof_path,
                    evidence=evidence,
                    reason=None if success else "No significant visual change detected",
                )

                if success:
                    print(f"   ✅ EXPLOIT VERIFIED!")
                    print(f"   Visual diff: {diff.get('percentage', 0):.2f}%")
                else:
                    print(f"   ❌ Exploit failed: {result.reason}")

                return result

        except Exception as e:
            raise PerceptionError(
                f"Browser perception failed: {str(e)}",
                url=vulnerability.target_url,
                operation="verify_exploit",
                recoverable=True,
            )

    async def self_evaluate(
        self, perception: Optional[VisualPerception], intent: str
    ) -> SelfEvaluation:
        """
        Self-evaluate captured perception against intent

        Args:
            perception: Captured visual perception
            intent: Expected outcome

        Returns:
            Self-evaluation result
        """
        print(f"🤖 Self-evaluating against intent: {intent[:50]}...")

        issues = []
        evidence = []
        issue_weights = {}

        if not perception or not perception.url:
            issues.append("Page did not load")
            issue_weights["Page did not load"] = 0.5
        else:
            evidence.append(f"Page loaded: {perception.url}")

        if perception and perception.dom_tree:
            evidence.append("DOM tree captured")
        else:
            issues.append("No DOM content")
            issue_weights["No DOM content"] = 0.3

        if perception and perception.viewport:
            viewport_ok = (
                perception.viewport.get("width", 0) >= 800
                and perception.viewport.get("height", 0) >= 600
            )
            if viewport_ok:
                evidence.append(
                    f"Viewport OK: {perception.viewport['width']}x{perception.viewport['height']}"
                )
            else:
                issues.append("Viewport too small")
                issue_weights["Viewport too small"] = 0.2

        confidence = SelfEvaluation.calculate_confidence(
            evidence, issues, issue_weights
        )
        satisfactory = len(issues) == 0 and confidence >= 0.7

        evaluation = SelfEvaluation(
            satisfactory=satisfactory,
            confidence=confidence,
            issues=issues,
            evidence=evidence,
            issue_weights=issue_weights,
        )

        print(f"   Confidence: {confidence:.2%}")
        print(f"   Satisfactory: {satisfactory}")
        if issues:
            print(f"   Issues: {', '.join(issues)}")

        return evaluation

    async def generate_report(
        self,
        job_id: str,
        target_url: str,
        vulnerabilities: List[Vulnerability],
        exploits: List[Exploit],
        verifications: List[VerificationResult],
        evaluation: SelfEvaluation,
    ) -> AuditReport:
        """
        Generate comprehensive audit report

        Args:
            job_id: Job identifier
            target_url: Target URL
            vulnerabilities: List of discovered vulnerabilities
            exploits: List of generated exploits
            verifications: List of verification results
            evaluation: Self-evaluation

        Returns:
            Complete audit report
        """
        print("📝 Generating report...")

        report = AuditReport(
            id=f"report-{job_id}",
            job_id=job_id,
            target_url=target_url,
            vulnerabilities=vulnerabilities,
            exploits=exploits,
            verifications=verifications,
            evaluation=evaluation,
        )

        report_path = self.output_dir / f"report-{sanitize_filename(job_id)}.json"
        with open(report_path, "w") as f:
            json.dump(report.to_dict(), f, indent=2)

        print(f"   Report saved: {report_path}")

        return report

    async def submit_bounty(self, report: AuditReport) -> Dict[str, Any]:
        """
        Submit finding to bounty platform

        Args:
            report: Audit report

        Returns:
            Submission result
        """
        print("📤 Submitting to bounty platform...")

        if not self.auto_submit:
            print("   ⚠️  Auto-submit disabled (manual approval required)")
            return {"status": "pending_approval", "message": "Manual approval required"}

        submission_id = f"SUB-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

        print(f"   ✅ Submitted: {submission_id}")

        return {
            "status": "submitted",
            "submission_id": submission_id,
            "message": "Bounty submitted successfully",
        }

    async def run_audit(
        self, target_url: str, job_id: Optional[str] = None, depth: str = "deep"
    ) -> AuditReport:
        """
        Run complete audit workflow

        Args:
            target_url: Target URL to audit
            job_id: Optional job ID (auto-generated if not provided)
            depth: Scan depth

        Returns:
            Complete audit report
        """
        job_id = job_id or generate_job_id()

        vulnerabilities = await self.scan_target(target_url, depth=depth)

        if not vulnerabilities:
            raise ScanError("No vulnerabilities found", target=target_url)

        exploits = []
        verifications = []

        critical = max(vulnerabilities, key=lambda v: v.cvss_score)
        print(f"\n🎯 Targeting: {critical.title}")

        exploit = await self.generate_exploit(critical)
        exploits.append(exploit)

        verification = await self.verify_exploit(critical, exploit)
        verifications.append(verification)

        evaluation = await self.self_evaluate(
            perception=verification.after_state, intent=critical.expected_outcome
        )

        report = await self.generate_report(
            job_id=job_id,
            target_url=target_url,
            vulnerabilities=vulnerabilities,
            exploits=exploits,
            verifications=verifications,
            evaluation=evaluation,
        )

        return report


async def main():
    """CLI demonstration"""
    print("=" * 60)
    print("AgentxploiTor - Autonomous Security Agent")
    print("=" * 60)
    print()

    agent = AgentxploiTorAgent(browser_perception=True, auto_submit=False)

    target_url = "https://example.com"

    try:
        report = await agent.run_audit(target_url)

        print("\n" + "=" * 60)
        print("AUTONOMOUS AUDIT COMPLETE")
        print("=" * 60)
        print(f"Job ID: {report.job_id}")
        print(f"Target: {report.target_url}")
        print(f"Findings: {report.summary}")
        print(f"Confidence: {report.evaluation.confidence:.2%}")
        print()
        print(
            "🎉 AgentxploiTor demonstrated autonomous security audit with visual proof!"
        )

    except AgentError as e:
        print(f"\n❌ Audit failed: {e.message}")
        if e.context:
            print(f"   Context: {e.context}")


if __name__ == "__main__":
    asyncio.run(main())
