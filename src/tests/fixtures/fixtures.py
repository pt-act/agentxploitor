"""
Test Fixtures - Contract Samples and Mock Data

Provides reusable test fixtures for integration tests.
"""

import os
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
import pytest


FIXTURES_DIR = Path(__file__).parent


@dataclass
class ContractFixture:
    """A contract fixture for testing."""
    name: str
    source: str
    language: str = "solidity"
    version: str = "0.8.0"
    vulnerabilities: List[str] = field(default_factory=list)
    expected_findings: int = 0


SAMPLE_CONTRACTS: Dict[str, ContractFixture] = {
    'reentrancy_vulnerable': ContractFixture(
        name='ReentrancyVulnerable',
        language='solidity',
        vulnerabilities=['reentrancy'],
        expected_findings=1,
        source='''
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract ReentrancyVulnerable {
    mapping(address => uint256) public balances;
    
    function deposit() external payable {
        balances[msg.sender] += msg.value;
    }
    
    function withdraw() external {
        uint256 amount = balances[msg.sender];
        require(amount > 0, "No balance");
        
        // Vulnerable: state change after external call
        (bool success, ) = msg.sender.call{value: amount}("");
        require(success, "Transfer failed");
        
        balances[msg.sender] = 0;
    }
    
    function getBalance() external view returns (uint256) {
        return address(this).balance;
    }
}
''',
    ),
    'overflow_vulnerable': ContractFixture(
        name='OverflowVulnerable',
        language='solidity',
        vulnerabilities=['integer_overflow'],
        expected_findings=1,
        source='''
// SPDX-License-Identifier: MIT
pragma solidity ^0.7.0;  // Pre-0.8.0, no overflow protection

contract OverflowVulnerable {
    uint256 public totalSupply;
    mapping(address => uint256) public balances;
    
    function mint(address to, uint256 amount) external {
        // Vulnerable: no overflow check
        totalSupply += amount;
        balances[to] += amount;
    }
    
    function transfer(address to, uint256 amount) external {
        require(balances[msg.sender] >= amount, "Insufficient balance");
        balances[msg.sender] -= amount;
        balances[to] += amount;
    }
}
''',
    ),
    'access_control_vulnerable': ContractFixture(
        name='AccessControlVulnerable',
        language='solidity',
        vulnerabilities=['access_control'],
        expected_findings=1,
        source='''
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract AccessControlVulnerable {
    address public owner;
    uint256 public value;
    
    constructor() {
        owner = msg.sender;
    }
    
    // Vulnerable: no access control
    function setValue(uint256 _value) external {
        value = _value;
    }
    
    // Vulnerable: tx.origin check
    function withdraw() external {
        require(tx.origin == owner, "Not owner");
        payable(owner).transfer(address(this).balance);
    }
    
    receive() external payable {}
}
''',
    ),
    'safe_contract': ContractFixture(
        name='SafeContract',
        language='solidity',
        vulnerabilities=[],
        expected_findings=0,
        source='''
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract SafeContract is ReentrancyGuard, Ownable {
    mapping(address => uint256) public balances;
    
    function deposit() external payable {
        balances[msg.sender] += msg.value;
    }
    
    function withdraw() external nonReentrant {
        uint256 amount = balances[msg.sender];
        require(amount > 0, "No balance");
        
        balances[msg.sender] = 0;
        
        (bool success, ) = msg.sender.call{value: amount}("");
        require(success, "Transfer failed");
    }
    
    function emergencyWithdraw() external onlyOwner {
        payable(owner()).transfer(address(this).balance);
    }
    
    receive() external payable {}
}
''',
    ),
    'flash_loan_vulnerable': ContractFixture(
        name='FlashLoanVulnerable',
        language='solidity',
        vulnerabilities=['flash_loan', 'price_manipulation'],
        expected_findings=2,
        source='''
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

interface IERC20 {
    function transfer(address to, uint256 amount) external returns (bool);
    function balanceOf(address account) external view returns (uint256);
}

contract FlashLoanVulnerable {
    IERC20 public token;
    uint256 public price;
    
    constructor(address _token) {
        token = IERC20(_token);
    }
    
    // Vulnerable: uses spot price without TWAP
    function getPrice() public view returns (uint256) {
        return token.balanceOf(address(this)) * price;
    }
    
    function setPrice(uint256 _price) external {
        price = _price;
    }
    
    function swap(uint256 amount) external {
        // Vulnerable: no slippage protection
        uint256 output = amount * getPrice();
        token.transfer(msg.sender, output);
    }
}
''',
    ),
}


@dataclass
class JobFixture:
    """A job fixture for testing."""
    id: str
    target_url: str
    contract_address: Optional[str]
    scope: str
    priority: str
    wallet_address: str
    payment_amount: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'target_url': self.target_url,
            'contract_address': self.contract_address,
            'scope': self.scope,
            'priority': self.priority,
            'wallet_address': self.wallet_address,
            'payment_amount': self.payment_amount,
        }


SAMPLE_JOBS: Dict[str, JobFixture] = {
    'standard_audit': JobFixture(
        id='job-standard-001',
        target_url='https://etherscan.io/address/0x1234567890abcdef',
        contract_address='0x1234567890abcdef',
        scope='Full contract audit',
        priority='normal',
        wallet_address='0xabcdef1234567890',
        payment_amount='0.1',
    ),
    'high_priority_audit': JobFixture(
        id='job-priority-001',
        target_url='https://etherscan.io/address/0xfedcba0987654321',
        contract_address='0xfedcba0987654321',
        scope='Critical vulnerability assessment',
        priority='critical',
        wallet_address='0xabcdef1234567890',
        payment_amount='0.5',
    ),
}


@dataclass
class PaymentFixture:
    """A payment fixture for testing."""
    tx_hash: str
    amount: str
    from_address: str
    to_address: str
    confirmations: int
    block_number: int
    valid: bool = True


SAMPLE_PAYMENTS: Dict[str, PaymentFixture] = {
    'valid_payment': PaymentFixture(
        tx_hash='0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890',
        amount='100000000000000000',  # 0.1 ETH in wei
        from_address='0xabcdef1234567890',
        to_address='0x1234567890abcdef',
        confirmations=12,
        block_number=18000000,
        valid=True,
    ),
    'insufficient_payment': PaymentFixture(
        tx_hash='0xfedcba0987654321fedcba0987654321fedcba0987654321fedcba0987654321',
        amount='10000000000000000',  # 0.01 ETH - too low
        from_address='0xabcdef1234567890',
        to_address='0x1234567890abcdef',
        confirmations=12,
        block_number=18000001,
        valid=False,
    ),
    'unconfirmed_payment': PaymentFixture(
        tx_hash='0x1111111111111111111111111111111111111111111111111111111111111111',
        amount='100000000000000000',
        from_address='0xabcdef1234567890',
        to_address='0x1234567890abcdef',
        confirmations=1,  # Not enough confirmations
        block_number=18000100,
        valid=False,
    ),
}


@pytest.fixture
def contract_fixtures():
    """Provide contract fixtures."""
    return SAMPLE_CONTRACTS


@pytest.fixture
def job_fixtures():
    """Provide job fixtures."""
    return SAMPLE_JOBS


@pytest.fixture
def payment_fixtures():
    """Provide payment fixtures."""
    return SAMPLE_PAYMENTS


@pytest.fixture
def sample_contract():
    """Provide a single sample contract."""
    return SAMPLE_CONTRACTS['reentrancy_vulnerable']


@pytest.fixture
def sample_job():
    """Provide a single sample job."""
    return SAMPLE_JOBS['standard_audit']


@pytest.fixture
def valid_payment():
    """Provide a valid payment fixture."""
    return SAMPLE_PAYMENTS['valid_payment']


def get_contract_source(name: str) -> Optional[str]:
    """Get contract source by name."""
    fixture = SAMPLE_CONTRACTS.get(name)
    return fixture.source if fixture else None


def get_contract_fixture(name: str) -> Optional[ContractFixture]:
    """Get full contract fixture by name."""
    return SAMPLE_CONTRACTS.get(name)


def create_mock_analyzer_result(
    vulnerabilities: List[str],
    confidence: float = 0.9,
) -> Dict[str, Any]:
    """Create a mock analyzer result."""
    findings = []
    severities = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']
    
    for i, vuln in enumerate(vulnerabilities):
        findings.append({
            'id': f'finding-{i:03d}',
            'title': f'{vuln.replace("_", " ").title()} Vulnerability',
            'description': f'Detected {vuln} vulnerability in contract',
            'severity': severities[i % len(severities)],
            'confidence': confidence,
            'location': f'contracts/{vuln}.sol:{(i + 1) * 10}',
        })
    
    return {
        'success': True,
        'findings': findings,
        'analyzer': 'mock',
        'duration_ms': 1500,
    }
