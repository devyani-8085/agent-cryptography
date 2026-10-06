import { useState } from 'react';

const enc = new TextEncoder();

const TESTS = {
  'RSA-OAEP 2048 encrypt': async () => {
    const k = await crypto.subtle.generateKey(
      { name: 'RSA-OAEP', modulusLength: 2048, publicExponent: new Uint8Array([1, 0, 1]), hash: 'SHA-256' },
      true, ['encrypt', 'decrypt']);
    const c = await crypto.subtle.encrypt({ name: 'RSA-OAEP' }, k.publicKey, enc.encode('demo-payload'));
    return `ciphertext ${c.byteLength} bytes`;
  },
  'ECDSA P-256 sign': async () => {
    const k = await crypto.subtle.generateKey({ name: 'ECDSA', namedCurve: 'P-256' }, true, ['sign', 'verify']);
    const s = await crypto.subtle.sign({ name: 'ECDSA', hash: 'SHA-256' }, k.privateKey, enc.encode('demo'));
    return `signature ${s.byteLength} bytes`;
  },
  'ECDH P-256 key exchange': async () => {
    const a = await crypto.subtle.generateKey({ name: 'ECDH', namedCurve: 'P-256' }, true, ['deriveBits']);
    const b = await crypto.subtle.generateKey({ name: 'ECDH', namedCurve: 'P-256' }, true, ['deriveBits']);
    const bits = await crypto.subtle.deriveBits({ name: 'ECDH', public: b.publicKey }, a.privateKey, 256);
    return `shared secret ${bits.byteLength} bytes`;
  },
  'RSASSA-PKCS1 2048 + SHA-1 sign (legacy)': async () => {
    const k = await crypto.subtle.generateKey(
      { name: 'RSASSA-PKCS1-v1_5', modulusLength: 2048, publicExponent: new Uint8Array([1, 0, 1]), hash: 'SHA-1' },
      true, ['sign', 'verify']);
    const s = await crypto.subtle.sign('RSASSA-PKCS1-v1_5', k.privateKey, enc.encode('demo'));
    return `signature ${s.byteLength} bytes`;
  },
  'AES-CBC 128 encrypt (legacy)': async () => {
    const k = await crypto.subtle.generateKey({ name: 'AES-CBC', length: 128 }, true, ['encrypt']);
    const c = await crypto.subtle.encrypt({ name: 'AES-CBC', iv: crypto.getRandomValues(new Uint8Array(16)) }, k, enc.encode('demo'));
    return `ciphertext ${c.byteLength} bytes`;
  },
  'SHA-1 digest (legacy)': async () => {
    const d = await crypto.subtle.digest('SHA-1', enc.encode('demo'));
    return `digest ${d.byteLength} bytes`;
  },
};

export default function CryptoLab() {
  const [log, setLog] = useState([]);
  const [running, setRunning] = useState(false);

  const run = async (name) => {
    try {
      setLog((l) => [...l, `✓ ${name}: ${''}`]);
      const result = await TESTS[name]();
      setLog((l) => {
        const updated = [...l];
        updated[updated.length - 1] = `✓ ${name}: ${result}`;
        return updated;
      });
    } catch (e) {
      setLog((l) => {
        const updated = [...l];
        updated[updated.length - 1] = `✗ ${name}: ${e.message}`;
        return updated;
      });
    }
  };

  const runAll = async () => {
    setRunning(true);
    setLog([]);
    for (const name of Object.keys(TESTS)) {
      await run(name);
    }
    setRunning(false);
  };

  return (
    <div style={{
      padding: 32,
      fontFamily: "'Segoe UI', system-ui, sans-serif",
      maxWidth: 720,
      margin: '0 auto',
    }}>
      <div style={{
        background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)',
        borderRadius: 16,
        padding: 32,
        color: '#fff',
        marginBottom: 24,
      }}>
        <h2 style={{ margin: '0 0 8px', fontSize: 28 }}>🧪 Crypto Lab</h2>
        <p style={{ margin: 0, opacity: 0.8, fontSize: 14 }}>
          Test fixture — dummy data only. Exercises WebCrypto algorithms for runtime scanner validation.
        </p>
      </div>

      <div style={{
        background: '#fff3cd',
        border: '1px solid #ffc107',
        borderRadius: 8,
        padding: '12px 16px',
        marginBottom: 24,
        fontSize: 13,
        color: '#856404',
      }}>
        ⚠️ <strong>Test Fixture Notice:</strong> These operations use dummy payloads and are intentionally
        insecure for scanner testing purposes. Do not use in production.
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginBottom: 24 }}>
        <button
          onClick={runAll}
          disabled={running}
          style={{
            padding: '12px 20px',
            background: running ? '#6c757d' : 'linear-gradient(135deg, #e94560, #c23616)',
            color: '#fff',
            border: 'none',
            borderRadius: 8,
            cursor: running ? 'not-allowed' : 'pointer',
            fontWeight: 600,
            fontSize: 15,
          }}
        >
          {running ? '⏳ Running all tests…' : '▶ Run All Tests'}
        </button>

        {Object.keys(TESTS).map((n) => (
          <button
            key={n}
            onClick={() => run(n)}
            disabled={running}
            style={{
              padding: '10px 16px',
              background: '#f8f9fa',
              border: '1px solid #dee2e6',
              borderRadius: 8,
              cursor: running ? 'not-allowed' : 'pointer',
              textAlign: 'left',
              fontSize: 13,
              color: '#212529',
              transition: 'background 0.15s',
            }}
            onMouseOver={(e) => !running && (e.target.style.background = '#e9ecef')}
            onMouseOut={(e) => (e.target.style.background = '#f8f9fa')}
          >
            {n}
          </button>
        ))}
      </div>

      {log.length > 0 && (
        <div style={{ marginBottom: 16 }}>
          <h3 style={{ fontSize: 16, marginBottom: 8 }}>Results</h3>
          <pre style={{
            background: '#1a1a2e',
            color: '#7effc3',
            padding: 20,
            borderRadius: 10,
            fontSize: 13,
            lineHeight: 1.8,
            overflow: 'auto',
            maxHeight: 400,
          }}>
            {log.join('\n')}
          </pre>
        </div>
      )}

      <button
        onClick={() => setLog([])}
        style={{
          padding: '8px 16px',
          background: 'transparent',
          border: '1px solid #adb5bd',
          borderRadius: 6,
          cursor: 'pointer',
          fontSize: 13,
          color: '#6c757d',
        }}
      >
        Clear Log
      </button>
    </div>
  );
}
