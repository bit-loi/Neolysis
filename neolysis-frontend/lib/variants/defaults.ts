import { TargetConditions } from '@/lib/enzyme-api';

export const defaultVariantConditions: TargetConditions = {
  temperature_c: 60,
  ph: 10,
  salinity_m_m: 250,
  solvent_exposure: 'moderate',
  use_case: 'detergent',
};

export const defaultVariantInput = 'V1: M1A\nV2: C75S\nV3: G120A';
