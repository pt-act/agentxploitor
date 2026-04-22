#!/usr/bin/env node
/**
 * generate-account-association.mjs
 *
 * Generates a new Farcaster accountAssociation for the .well-known/farcaster.json file.
 *
 * SUPPORTS TWO SIGNING TYPES:
 *
 * 1. app_key (RECOMMENDED — no crypto needed)
 *    Uses Ed25519 key pair via @farcaster/miniapp-node JFS module.
 *    The app key must be registered with your FID via the Farcaster developer dashboard.
 *
 * 2. custody (requires Ethereum wallet)
 *    Uses Ethereum personal_sign (EIP-191) over the concatenation of base64(header) + "." + base64(payload).
 *    Requires your Farcaster custody address private key.
 *
 * Usage:
 *   # Generate new app_key association (recommended)
 *   node scripts/generate-account-association.mjs --fid 12142 --domain agentxploitor.netlify.app
 *
 *   # Reuse an existing Ed25519 private key
 *   node scripts/generate-account-association.mjs --fid 12142 --domain agentxploitor.netlify.app --private-key <hex>
 *
 *   # Generate custody-type association using Ethereum wallet
 *   node scripts/generate-account-association.mjs --fid 12142 --domain agentxploitor.netlify.app --type custody --eth-private-key <hex>
 *
 * After running, copy the accountAssociation output into:
 *   miniapp/src/app/.well-known/farcaster.json/route.ts
 */

import { createJsonFarcasterSignature } from '@farcaster/miniapp-node/dist/jfs.js';
import { ed25519 } from '@noble/curves/ed25519';
import { bytesToHex, hexToBytes } from '@noble/hashes/utils';

// ─── CLI Args ─────────────────────────────────────────────────────────────────

const args = process.argv.slice(2);
function getArg(name) {
  const idx = args.indexOf(`--${name}`);
  return idx >= 0 && idx + 1 < args.length ? args[idx + 1] : null;
}

const domain = getArg('domain') || 'agentxploitor.netlify.app';
const fid = parseInt(getArg('fid') || '0', 10);
const keyType = getArg('type') || 'app_key'; // 'app_key' or 'custody'
// Private keys: prefer env vars (safer — not visible in process listings), fall back to CLI args
const ed25519PrivateKeyHex = process.env.FARCASTER_PRIVATE_KEY || getArg('private-key');
const ethPrivateKeyHex = process.env.FARCASTER_ETH_PRIVATE_KEY || getArg('eth-private-key');

if (getArg('private-key')) console.warn('⚠️  --private-key visible in process listings. Prefer FARCASTER_PRIVATE_KEY env var.');
if (getArg('eth-private-key')) console.warn('⚠️  --eth-private-key visible in process listings. Prefer FARCASTER_ETH_PRIVATE_KEY env var.');

if (!fid) {
  console.error('❌ --fid is required (your Farcaster FID number)');
  console.error('');
  console.error('Usage:');
  console.error('  # App key (recommended — no crypto needed):');
  console.error('  node scripts/generate-account-association.mjs --fid 12142 --domain agentxploitor.netlify.app');
  console.error('');
  console.error('  # Custody (requires Ethereum private key):');
  console.error('  node scripts/generate-account-association.mjs --fid 12142 --domain agentxploitor.netlify.app --type custody --eth-private-key <hex>');
  console.error('');
  console.error('  Environment (preferred — not visible in process listings):');
  console.error('  FARCASTER_PRIVATE_KEY=<hex>   node scripts/generate-account-association.mjs --fid 12142 ...');
  console.error('  FARCASTER_ETH_PRIVATE_KEY=<hex> node scripts/generate-account-association.mjs --fid 12142 --type custody ...');
  process.exit(1);
}

// ─── Base64 helpers ────────────────────────────────────────────────────────────

function toBase64(str) {
  return Buffer.from(str, 'utf-8').toString('base64');
}


// ─── App Key Type (Ed25519 / JFS) ─────────────────────────────────────────────

async function generateAppKeyAssociation() {
  let privateKeyBytes;

  if (ed25519PrivateKeyHex) {
    const cleaned = ed25519PrivateKeyHex.replace(/^0x/, '');
    if (cleaned.length !== 64) {
      console.error('❌ Ed25519 private key must be 32 bytes (64 hex chars)');
      process.exit(1);
    }
    privateKeyBytes = hexToBytes(cleaned);
  } else {
    privateKeyBytes = ed25519.utils.randomPrivateKey();
    const publicKey = ed25519.getPublicKey(privateKeyBytes);

    console.log('🔑 Generated new Ed25519 key pair:');
    console.log(`   Private key: 0x${bytesToHex(privateKeyBytes)}`);
    console.log(`   Public key:  0x${bytesToHex(publicKey)}`);
    console.log('');
    console.log('⚠️  SAVE the private key! You need it to regenerate or update associations.');
    console.log('   Re-run with --private-key 0x... to reuse this key.');
    console.log('');
  }

  const payload = new TextEncoder().encode(JSON.stringify({ domain }));

  const result = createJsonFarcasterSignature({
    fid,
    type: 'app_key',
    privateKey: privateKeyBytes,
    payload,
  });

  const publicKey = ed25519.getPublicKey(privateKeyBytes);

  console.log('✅ App key association generated!\n');
  console.log('── Verification ──');
  console.log(`   Domain: ${domain}`);
  console.log(`   FID:    ${fid}`);
  console.log(`   Type:   app_key`);
  console.log(`   Key:    0x${bytesToHex(publicKey)}\n`);

  console.log('── Copy into route.ts ──\n');
  console.log('    accountAssociation: {');
  console.log(`      header: "${result.header}",`);
  console.log(`      payload: "${result.payload}",`);
  console.log(`      signature: "${result.signature}",`);
  console.log('    },\n');

  console.log('── Next Steps ──');
  console.log('1. Register this app key with your FID in the Farcaster developer dashboard');
  console.log('2. Copy the accountAssociation block into miniapp/src/app/.well-known/farcaster.json/route.ts');
  console.log('3. Deploy and verify at https://agentxploitor.netlify.app/.well-known/farcaster.json\n');

  return result;
}

// ─── Custody Type (Ethereum personal_sign) ─────────────────────────────────────

async function generateCustodyAssociation() {
  if (!ethPrivateKeyHex) {
    console.error('❌ Custody type requires --eth-private-key (your Ethereum custody address private key)');
    console.error('   This is the private key for the address that owns your Farcaster FID on-chain.');
    console.error('');
    console.error('   ⚠️  Never share or commit this key. Use it only for signing, then discard from memory.');
    process.exit(1);
  }

  // Dynamically import viem (already in project dependencies)
  const { privateKeyToAccount } = await import('viem/accounts');

  const cleanedKey = ethPrivateKeyHex.replace(/^0x/, '');
  if (cleanedKey.length !== 64) {
    console.error('❌ Ethereum private key must be 32 bytes (64 hex chars)');
    process.exit(1);
  }

  const account = privateKeyToAccount(`0x${cleanedKey}`);
  const custodyAddress = account.address;

  console.log(`🔑 Using custody address: ${custodyAddress}`);
  console.log(`   Make sure this address owns FID ${fid} on the Farcaster ID Registry.\n`);

  // Build header and payload (standard base64, NOT base64url)
  const headerObj = { fid, type: 'custody', key: custodyAddress };
  const payloadObj = { domain };

  const headerB64 = toBase64(JSON.stringify(headerObj));
  const payloadB64 = toBase64(JSON.stringify(payloadObj));

  // Sign header.payload using personal_sign (EIP-191)
  // privateKeyToAccount already has signMessage — no wallet client needed for local signing
  const message = `${headerB64}.${payloadB64}`;

  const signature = await account.signMessage({ message });

  // Encode signature as base64
  const signatureB64 = Buffer.from(signature.slice(2), 'hex').toString('base64');

  console.log('✅ Custody association generated!\n');
  console.log('── Verification ──');
  console.log(`   Domain: ${domain}`);
  console.log(`   FID:    ${fid}`);
  console.log(`   Type:   custody`);
  console.log(`   Key:    ${custodyAddress}\n`);

  console.log('── Copy into route.ts ──\n');
  console.log('    accountAssociation: {');
  console.log(`      header: "${headerB64}",`);
  console.log(`      payload: "${payloadB64}",`);
  console.log(`      signature: "${signatureB64}",`);
  console.log('    },\n');

  return { header: headerB64, payload: payloadB64, signature: signatureB64 };
}

// ─── Main ─────────────────────────────────────────────────────────────────────

if (keyType === 'custody') {
  generateCustodyAssociation().catch(err => {
    console.error('❌ Failed:', err.message);
    process.exit(1);
  });
} else if (keyType === 'app_key') {
  generateAppKeyAssociation().catch(err => {
    console.error('❌ Failed:', err.message);
    process.exit(1);
  });
} else {
  console.error(`❌ Unknown type "${keyType}". Use "app_key" or "custody".`);
  process.exit(1);
}
