// Types for the EchoClient browser helper.
// Assumes echo-soulcode.d.ts is present (generated) and provides EchoSoulcode/EchoSoulcodeBundle.

declare namespace EchoClient {
  function getBundle(): EchoSoulcodeBundle | null;
  function getSoul(kind: 'ECHO_SQUIRREL' | 'ECHO_FOX' | 'ECHO_PARADOX'): EchoSoulcode | null;
  function getMemory(): { series: Array<{ t: number; L1: number; L2: number; L3: number }>; events: number } | null;
  function onBundle(cb: (bundle: EchoSoulcodeBundle) => void): () => void;
  function onMemory(cb: (mem: { series: Array<{ t: number; L1: number; L2: number; L3: number }>; events: number }) => void): () => void;
}

interface Window { EchoClient: typeof EchoClient; }

export {}; // ensure this file is treated as a module and not a script

