/**
 * Component Size Audit
 * 
 * Verifies all components are under 400 lines as per Orion OS requirements.
 * Run with: npx vitest run src/tests/component-audit.test.ts
 */

import { describe, it, expect } from 'vitest';
import * as fs from 'fs';
import * as path from 'path';

const COMPONENTS_DIR = path.join(__dirname, '../components');
const MAX_LINES = 400;

describe('Component Size Audit', () => {
  // Get all TSX files in components directory
  const componentFiles = fs.readdirSync(COMPONENTS_DIR)
    .filter(f => f.endsWith('.tsx'))
    .filter(f => !f.includes('.test.') && !f.includes('.spec.'));
  
  for (const file of componentFiles) {
    const filePath = path.join(COMPONENTS_DIR, file);
    const content = fs.readFileSync(filePath, 'utf-8');
    const lineCount = content.split('\n').length;
    
    it(`${file} is under ${MAX_LINES} lines`, () => {
      expect(lineCount).toBeLessThanOrEqual(MAX_LINES);
    });
  }
});

describe('Component Audit Summary', () => {
  it('should list all components and their sizes', () => {
    const componentFiles = fs.readdirSync(COMPONENTS_DIR)
      .filter(f => f.endsWith('.tsx'))
      .filter(f => !f.includes('.test.') && !f.includes('.spec.'));
    
    console.log('\n📊 Component Size Audit:');
    console.log('─'.repeat(50));
    
    let oversized: string[] = [];
    
    for (const file of componentFiles) {
      const filePath = path.join(COMPONENTS_DIR, file);
      const content = fs.readFileSync(filePath, 'utf-8');
      const lineCount = content.split('\n').length;
      
      const status = lineCount > MAX_LINES ? '⚠️ OVERSIZED' : '✅';
      console.log(`${status} ${file}: ${lineCount} lines`);
      
      if (lineCount > MAX_LINES) {
        oversized.push(`${file} (${lineCount} lines)`);
      }
    }
    
    console.log('─'.repeat(50));
    console.log(`Total: ${componentFiles.length} components`);
    
    if (oversized.length > 0) {
      console.log('\n⚠️  Oversized components need refactoring:');
      oversized.forEach(c => console.log(`  - ${c}`));
    }
    
    expect(oversized.length).toBe(0);
  });
});
