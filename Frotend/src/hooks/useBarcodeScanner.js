import { useState } from 'react';

export function useBarcodeScanner() {
  const [scanning, setScanning] = useState(false);
  const [code, setCode] = useState('');

  const startScan = () => {
    // For demo, use prompt; replace with real QR reader later
    const input = prompt('Scan barcode (or enter manually):');
    if (input) {
      setCode(input);
      setScanning(false);
    }
  };

  return { scanning, code, startScan };
}
