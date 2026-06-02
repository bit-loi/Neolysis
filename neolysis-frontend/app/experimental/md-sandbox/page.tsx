import { MolecularDynamicsSandbox } from '@/components/experimental/MolecularDynamicsSandbox';

export const metadata = {
  title: 'Experimental MD Sandbox - Neolysis',
  description:
    'Experimental Rust/WASM molecular dynamics sandbox for future structure-aware enzyme engineering.',
};

export default function ExperimentalMDSandboxPage() {
  return <MolecularDynamicsSandbox />;
}
