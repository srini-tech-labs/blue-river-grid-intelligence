const CITE_RE = /\[(S1|D\d+)\](?!\()/g

/** Turn [S1]/[D#] labels into internal anchors the answer renderer maps to chips. */
export function linkifyCitations(answer: string): string {
  return answer.replace(CITE_RE, (_, l: string) => `[${l}](#cite-${l})`)
}
