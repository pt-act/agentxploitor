import { describe, it, expect, beforeEach } from 'vitest';
import * as path from 'path';
import * as os from 'os';
import {
  getSocketPath,
  getPortFile,
  getPidFile,
  getConnectionInfo,
  setSession,
  getSession,
} from './daemon.js';

// Platform detection
const isWindows = process.platform === 'win32';

describe('daemon path traversal security', () => {
  const originalSession = getSession();

  beforeEach(() => {
    // Reset to default session before each test
    setSession('default');
  });

  describe('getSocketPath', () => {
    it('should return valid path for normal session', () => {
      if (isWindows) {
        // On Windows, returns port number as string
        const result = getSocketPath('test-session');
        expect(Number(result)).toBeGreaterThan(0);
      } else {
        const result = getSocketPath('test-session');
        expect(result).toContain('agent-browser-test-session.sock');
      }
    });

    it('should reject path traversal attempting to escape tmpdir', () => {
      if (isWindows) {
        // Windows uses TCP ports, not file paths
        return;
      }
      // This attempts to traverse up from tmpdir
      const maliciousSession = '../../../etc/passwd';
      expect(() => getSocketPath(maliciousSession)).toThrow('Invalid session parameter');
    });

    it('should reject absolute path injection', () => {
      if (isWindows) {
        // Windows uses TCP ports, not file paths
        return;
      }
      // When an absolute path is used as session, path.resolve treats it as part of the filename
      // The security check ensures the result stays within tmpdir
      // So /etc/passwd becomes agent-browser-/etc/passwd.sock in tmpdir (safe)
      // But we should test that the path stays in tmpdir
      const maliciousSession = '/etc/passwd';
      const result = getSocketPath(maliciousSession);
      const tmpDir = path.resolve(os.tmpdir());
      // The result should still be within tmpdir (security property)
      expect(result.startsWith(tmpDir)).toBe(true);
    });

    it('should accept alphanumeric session names', () => {
      if (isWindows) {
        const result = getSocketPath('session123');
        expect(Number(result)).toBeGreaterThan(0);
      } else {
        const result = getSocketPath('session123');
        expect(result).toContain('agent-browser-session123.sock');
      }
    });

    it('should accept session names with hyphens', () => {
      if (isWindows) {
        const result = getSocketPath('my-session-name');
        expect(Number(result)).toBeGreaterThan(0);
      } else {
        const result = getSocketPath('my-session-name');
        expect(result).toContain('agent-browser-my-session-name.sock');
      }
    });

    it('should accept session names with underscores', () => {
      if (isWindows) {
        const result = getSocketPath('my_session_name');
        expect(Number(result)).toBeGreaterThan(0);
      } else {
        const result = getSocketPath('my_session_name');
        expect(result).toContain('agent-browser-my_session_name.sock');
      }
    });

    it('should ensure path stays within tmpdir', () => {
      if (isWindows) {
        return;
      }
      // Valid session should produce path within tmpdir
      const result = getSocketPath('valid-session');
      const tmpDir = path.resolve(os.tmpdir());
      expect(result.startsWith(tmpDir)).toBe(true);
    });
  });

  describe('getPortFile', () => {
    it('should return valid path for normal session', () => {
      const result = getPortFile('test-session');
      expect(result).toContain('agent-browser-test-session.port');
    });

    it('should reject path traversal attempting to escape tmpdir', () => {
      const maliciousSession = '../../../etc/passwd';
      expect(() => getPortFile(maliciousSession)).toThrow('Invalid session parameter');
    });

    it('should reject absolute path injection', () => {
      // When an absolute path is used as session, path.resolve treats it as part of the filename
      // The security check ensures the result stays within tmpdir
      const maliciousSession = '/etc/passwd';
      const result = getPortFile(maliciousSession);
      const tmpDir = path.resolve(os.tmpdir());
      // The result should still be within tmpdir (security property)
      expect(result.startsWith(tmpDir)).toBe(true);
    });

    it('should accept alphanumeric session names', () => {
      const result = getPortFile('session123');
      expect(result).toContain('agent-browser-session123.port');
    });

    it('should ensure path stays within tmpdir', () => {
      const result = getPortFile('valid-session');
      const tmpDir = path.resolve(os.tmpdir());
      expect(result.startsWith(tmpDir)).toBe(true);
    });
  });

  describe('getPidFile', () => {
    it('should return valid path for normal session', () => {
      const result = getPidFile('test-session');
      expect(result).toContain('agent-browser-test-session.pid');
    });

    it('should reject path traversal attempting to escape tmpdir', () => {
      const maliciousSession = '../../../etc/passwd';
      expect(() => getPidFile(maliciousSession)).toThrow('Invalid session parameter');
    });

    it('should reject absolute path injection', () => {
      // When an absolute path is used as session, path.resolve treats it as part of the filename
      // The security check ensures the result stays within tmpdir
      const maliciousSession = '/etc/passwd';
      const result = getPidFile(maliciousSession);
      const tmpDir = path.resolve(os.tmpdir());
      // The result should still be within tmpdir (security property)
      expect(result.startsWith(tmpDir)).toBe(true);
    });

    it('should accept alphanumeric session names', () => {
      const result = getPidFile('session123');
      expect(result).toContain('agent-browser-session123.pid');
    });

    it('should ensure path stays within tmpdir', () => {
      const result = getPidFile('valid-session');
      const tmpDir = path.resolve(os.tmpdir());
      expect(result.startsWith(tmpDir)).toBe(true);
    });
  });

  describe('getConnectionInfo', () => {
    it('should return valid connection info for normal session', () => {
      const result = getConnectionInfo('test-session');
      expect(result).toBeDefined();
      if (result.type === 'unix') {
        expect(result.path).toContain('agent-browser-test-session.sock');
      } else {
        expect(result.port).toBeGreaterThan(0);
      }
    });

    it('should reject path traversal attempting to escape tmpdir', () => {
      if (isWindows) {
        // Windows uses TCP ports, not file paths
        return;
      }
      const maliciousSession = '../../../etc/passwd';
      expect(() => getConnectionInfo(maliciousSession)).toThrow('Invalid session');
    });

    it('should reject absolute path injection', () => {
      if (isWindows) {
        // Windows uses TCP ports, not file paths
        return;
      }
      // When an absolute path is used as session, path.resolve treats it as part of the filename
      // The security check ensures the result stays within tmpdir
      const maliciousSession = '/etc/passwd';
      const result = getConnectionInfo(maliciousSession);
      if (result.type === 'unix') {
        const tmpDir = path.resolve(os.tmpdir());
        // The result should still be within tmpdir (security property)
        expect(result.path.startsWith(tmpDir)).toBe(true);
      }
    });

    it('should accept alphanumeric session names', () => {
      const result = getConnectionInfo('session123');
      expect(result).toBeDefined();
    });

    it('should ensure unix socket path stays within tmpdir', () => {
      if (isWindows) {
        return;
      }
      const result = getConnectionInfo('valid-session');
      if (result.type === 'unix') {
        const tmpDir = path.resolve(os.tmpdir());
        expect(result.path.startsWith(tmpDir)).toBe(true);
      }
    });
  });

  describe('session management', () => {
    it('should set and get session', () => {
      setSession('my-test-session');
      expect(getSession()).toBe('my-test-session');
    });

    it('should use current session when no session parameter provided', () => {
      if (isWindows) {
        setSession('current-session');
        const result = getSocketPath();
        expect(Number(result)).toBeGreaterThan(0);
      } else {
        setSession('current-session');
        const result = getSocketPath();
        expect(result).toContain('agent-browser-current-session.sock');
      }
    });

    it('should restore original session', () => {
      setSession(originalSession);
      expect(getSession()).toBe(originalSession);
    });
  });

  describe('path validation security properties', () => {
    it('should prevent directory traversal attacks', () => {
      if (isWindows) {
        return;
      }
      // Test various directory traversal patterns
      const attacks = [
        '../../../etc/passwd',
        '../../../../etc/shadow',
        '../../../root/.ssh/id_rsa',
      ];

      for (const attack of attacks) {
        expect(() => getSocketPath(attack)).toThrow('Invalid session parameter');
        expect(() => getPortFile(attack)).toThrow('Invalid session parameter');
        expect(() => getPidFile(attack)).toThrow('Invalid session parameter');
        expect(() => getConnectionInfo(attack)).toThrow('Invalid session');
      }
    });

    it('should prevent absolute path injection', () => {
      // Test absolute path injection - these should NOT escape tmpdir
      // The security fix ensures all paths stay within tmpdir
      const attacks = ['/etc/passwd', '/root/.ssh/id_rsa', '/tmp/malicious'];

      for (const attack of attacks) {
        const tmpDir = path.resolve(os.tmpdir());
        
        // All functions should return paths within tmpdir
        const portFile = getPortFile(attack);
        const pidFile = getPidFile(attack);
        expect(portFile.startsWith(tmpDir)).toBe(true);
        expect(pidFile.startsWith(tmpDir)).toBe(true);

        if (!isWindows) {
          const socketPath = getSocketPath(attack);
          expect(socketPath.startsWith(tmpDir)).toBe(true);
          
          const connInfo = getConnectionInfo(attack);
          if (connInfo.type === 'unix') {
            expect(connInfo.path.startsWith(tmpDir)).toBe(true);
          }
        }
      }
    });

    it('should allow safe session names', () => {
      // Test that legitimate session names work correctly
      const safeSessions = [
        'default',
        'session-1',
        'my_session',
        'test123',
        'user-session-2024',
      ];

      for (const session of safeSessions) {
        expect(() => {
          if (!isWindows) {
            getSocketPath(session);
          }
          getPortFile(session);
          getPidFile(session);
          getConnectionInfo(session);
        }).not.toThrow();
      }
    });

    it('should validate that returned paths are within tmpdir', () => {
      const tmpDir = path.resolve(os.tmpdir());
      const session = 'test-session';

      // All file paths should be within tmpdir
      const portFile = getPortFile(session);
      const pidFile = getPidFile(session);

      expect(portFile.startsWith(tmpDir)).toBe(true);
      expect(pidFile.startsWith(tmpDir)).toBe(true);

      if (!isWindows) {
        const socketPath = getSocketPath(session);
        expect(socketPath.startsWith(tmpDir)).toBe(true);

        const connInfo = getConnectionInfo(session);
        if (connInfo.type === 'unix') {
          expect(connInfo.path.startsWith(tmpDir)).toBe(true);
        }
      }
    });
  });
});
