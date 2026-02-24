export interface Preset {
  name: string;
  description: string;
  constraints: string[];
  config: import('./run').RunConfig;
}
