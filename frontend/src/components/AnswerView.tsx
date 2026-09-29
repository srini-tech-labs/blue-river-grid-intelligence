import Markdown, { type Components } from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { linkifyCitations } from '../lib/citations'


interface Props {
  answer: string
  validLabels: Set<string>
  onCite: (label: string) => void
}

export function AnswerView({ answer, validLabels, onCite }: Props) {
  const components: Components = {
    a: ({ href, children }) => {
      const m = href?.match(/^#cite-(S1|D\d+)$/)
      if (!m) return <span>{children}</span> // never render model-supplied external links
      const l = m[1]
      const known = validLabels.has(l)
      return (
        <button
          type="button"
          className={`cite-chip ${l === 'S1' ? 'structured' : ''} ${known ? '' : 'unknown'}`}
          onClick={() => known && onCite(l)}
          title={known ? `Show source ${l}` : `${l} does not match any retrieved source`}
          aria-label={known ? `Citation ${l}` : `Unverified citation ${l}`}
        >
          {l}
        </button>
      )
    },
  }
  return (
    <div className="answer-md">
      <Markdown remarkPlugins={[remarkGfm]} components={components} disallowedElements={['img']}>
        {linkifyCitations(answer)}
      </Markdown>
    </div>
  )
}
