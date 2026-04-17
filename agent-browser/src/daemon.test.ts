import { describe, it, expect, beforeEach } from 'vitest';
import { getSocketPath, getPortFile, getPidFile, getConnectionInfo, setSession } from './daemon.js';
import * as os from 'os';
import * as path from 'path';

describe('daemon path traversal security', () => {
  const originalSession = process.env.AGENT_BROWSER_SESSION;
  const isWindows = process.platform === 'win32';

  beforeEach(() => {
    // Reset to default session before each test
    setSession('default');
  });

  afterEach(() => {
    // Restore original session
    if (originalSession) {
      process.env.AGENT_BROWSER_SESSION = originalSession;
    } else {
      delete process.env.AGENT_BROWSER_SESSION;
    }
  });

  describe('getSocketPath', () => {
    it('should return valid path for normal session name', () => {
      if (isWindows) {
        // Windows returns port number as string
        const result = getSocketPath('test-session');
        expect(result).toMatch(/^\d+$/);
      } else {
        const result = getSocketPath('test-session');
        const tmpdir = path.resolve(os.tmpdir());
        expect(result).toContain(tmpdir);
        expect(result).toContain('agent-browser-test-session.sock');
      }
    });

    it('should allow session names with .. as part of filename (not directory traversal)', () => {
      if (isWindows) {
        // Windows uses port numbers, not paths
        return;
      }
      // When session is '../etc/passwd', the filename becomes 'agent-browser-../etc/passwd.sock'
      // This is safe because .. is part of the filename, not a directory separator
      const result = getSocketPath('../etc/passwd');
      const tmpdir = path.resolve(os.tmpdir());
      expect(result).toContain(tmpdir);
      expect(result).toContain('agent-browser-..'); // The .. is part of the filename
    });

    it('should reject path with directory traversal in middle', () => {
      if (isWindows) {
        return;
      }
      // This creates a path that actually escapes tmpdir
      expect(() => getSocketPath('foo/../../../etc/passwd')).toThrow('Invalid session parameter');
    });
  });

  describe('getPortFile', () => {
    it('should return valid path for normal session name', () => {
      const result = getPortFile('test-session');
      const tmpdir = path.resolve(os.tmpdir());
      expect(result).toContain(tmpdir);
      expect(result).toContain('agent-browser-test-session.port');
    });

    it('should allow session names with .. as part of filename', () => {
      // Similar to getSocketPath, .. becomes part of the filename
      const result = getPortFile('../etc/passwd');
      const tmpdir = path.resolve(os.tmpdir());
      expect(result).toContain(tmpdir);
    });

    it('should reject complex path traversal that escapes tmpdir', () => {
      expect(() => getPortFile('foo/../../etc/passwd')).toThrow('Invalid session parameter');
    });
  });

  describe('getPidFile', () => {
    it('should return valid path for normal session name', () => {
      const result = getPidFile('test-session');
      const tmpdir = path.resolve(os.tmpdir());
      expect(result).toContain(tmpdir);
      expect(result).toContain('agent-browser-test-session.pid');
    });

    it('should allow session names with .. as part of filename', () => {
      const result = getPidFile('../etc/passwd');
      const tmpdir = path.resolve(os.tmpdir());
      expect(result).toContain(tmpdir);
    });

    it('should reject path traversal with multiple levels that escape tmpdir', () => {
      expect(() => getPidFile('../../../etc/passwd')).toThrow('Invalid session parameter');
    });
  });

  describe('getConnectionInfo', () => {
    it('should return valid connection info for normal session', () => {
      const result = getConnectionInfo('test-session');
      if (isWindows) {
        expect(result.type).toBe('tcp');
        expect(result).toHaveProperty('port');
        expect(typeof (result as any).port).toBe('number');
      } else {
        expect(result.type).toBe('unix');
        expect(result).toHaveProperty('path');
        const tmpdir = path.resolve(os.tmpdir());
        expect((result as any).path).toContain(tmpdir);
      }
    });

    it('should allow session names with .. as part of filename', () => {
      if (isWindows) {
        // Windows uses port numbers, not paths
        return;
      }
      const result = getConnectionInfo('../etc/passwd');
      expect(result.type).toBe('unix');
      const tmpdir = path.resolve(os.tmpdir());
      expect((result as any).path).toContain(tmpdir);
    });

    it('should reject path traversal that escapes tmpdir', () => {
      if (isWindows) {
        return;
      }
      expect(() => getConnectionInfo('foo/../../../etc/passwd')).toThrow('Invalid session identifier');
    });
  });

  describe('path validation ensures files stay in tmpdir', () => {
    it('should ensure all generated paths are within tmpdir', () => {
      const tmpdir = path.resolve(os.tmpdir());
      const sessions = ['valid-session', 'test123', 'my-session-name'];

      for (const session of sessions) {
        if (!isWindows) {
          const socketPath = getSocketPath(session);
          expect(socketPath.startsWith(tmpdir)).toBe(true);
        }

        const portFile = getPortFile(session);
        expect(portFile.startsWith(tmpdir)).toBe(true);

        const pidFile = getPidFile(session);
        expect(pidFile.startsWith(tmpdir)).toBe(true);
      }
    });

    it('should prevent escaping tmpdir with crafted session names', () => {
      // These session names would create paths that escape tmpdir
      // The key is having enough ../ segments to escape the tmpdir depth
      const maliciousSessions = [
        '../../../../../../../etc/passwd',  // Many levels to ensure escape
        '../../../../../../root/.ssh/id_rsa',
        'foo/../../../../../etc/hosts',
        'bar/../../../../../../etc/shadow',
      ];

      for (const session of maliciousSessions) {
        if (!isWindows) {
          expect(() => getSocketPath(session), `getSocketPath should reject: ${session}`).toThrow('Invalid session parameter');
        }
        expect(() => getPortFile(session), `getPortFile should reject: ${session}`).toThrow('Invalid session parameter');
        expect(() => getPidFile(session), `getPidFile should reject: ${session}`).toThrow('Invalid session parameter');
      }
    });
  });
});
