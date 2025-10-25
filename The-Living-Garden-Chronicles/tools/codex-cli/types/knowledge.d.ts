export interface KiraKnowledge {
  echo_state: { alpha:number; beta:number; gamma:number; order:string[] };
  memory: { total:number; narrative:number; tags: { tag:string; count:number }[] };
  ledger: { total:number; by_type: Record<string,number> };
  mantras: { canonical:string[]; persona_ordered:string[] };
  recommendations: string[];
  generated_at: string;
}
