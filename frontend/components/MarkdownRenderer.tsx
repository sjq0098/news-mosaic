import React from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import rehypeHighlight from 'rehype-highlight'
import rehypeRaw from 'rehype-raw'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { tomorrow } from 'react-syntax-highlighter/dist/cjs/styles/prism'
import 'highlight.js/styles/github.css'

interface MarkdownRendererProps {
  content: string
  className?: string
}

const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({ content, className = '' }) => {
  return (
    <div className={`markdown-content ${className}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeHighlight, rehypeRaw]}
        components={{
          // 自定义代码块渲染
          code({ node, className, children, ...props }: any) {
            const match = /language-(\w+)/.exec(className || '')
            const inline = (props as any)?.inline
            return !inline && match ? (
              <SyntaxHighlighter
                style={tomorrow as any}
                language={match[1]}
                PreTag="div"
                {...props}
              >
                {String(children).replace(/\n$/, '')}
              </SyntaxHighlighter>
            ) : (
              <code className={className ? className : "markdown-inline-code"} {...props}>
                {children}
              </code>
            )
          },
          // 自定义标题渲染
          h1: ({ children }) => (
            <h1 className="markdown-h1">{children}</h1>
          ),
          h2: ({ children }) => (
            <h2 className="markdown-h2">{children}</h2>
          ),
          h3: ({ children }) => (
            <h3 className="markdown-h3">{children}</h3>
          ),
          h4: ({ children }) => (
            <h4 className="markdown-h4">{children}</h4>
          ),
          h5: ({ children }) => (
            <h5 className="markdown-h5">{children}</h5>
          ),
          h6: ({ children }) => (
            <h6 className="markdown-h6">{children}</h6>
          ),
          // 自定义段落渲染
          p: ({ children }) => (
            <p className="markdown-paragraph">{children}</p>
          ),
          // 自定义列表渲染
          ul: ({ children }) => (
            <ul className="markdown-ul">{children}</ul>
          ),
          ol: ({ children }) => (
            <ol className="markdown-ol">{children}</ol>
          ),
          li: ({ children }) => (
            <li className="markdown-li">{children}</li>
          ),
          // 自定义链接渲染
          a: ({ href, children }) => (
            <a 
              href={href} 
              className="markdown-link" 
              target="_blank" 
              rel="noopener noreferrer"
            >
              {children}
            </a>
          ),
          // 自定义引用块渲染
          blockquote: ({ children }) => (
            <blockquote className="markdown-blockquote">{children}</blockquote>
          ),
          // 自定义表格渲染
          table: ({ children }) => (
            <div className="markdown-table-wrapper">
              <table className="markdown-table">{children}</table>
            </div>
          ),
          thead: ({ children }) => (
            <thead className="markdown-thead">{children}</thead>
          ),
          tbody: ({ children }) => (
            <tbody className="markdown-tbody">{children}</tbody>
          ),
          tr: ({ children }) => (
            <tr className="markdown-tr">{children}</tr>
          ),
          th: ({ children }) => (
            <th className="markdown-th">{children}</th>
          ),
          td: ({ children }) => (
            <td className="markdown-td">{children}</td>
          ),
          // 自定义强调渲染
          strong: ({ children }) => (
            <strong className="markdown-strong">{children}</strong>
          ),
          em: ({ children }) => (
            <em className="markdown-em">{children}</em>
          ),
          // 自定义删除线渲染
          del: ({ children }) => (
            <del className="markdown-del">{children}</del>
          ),
          // 自定义水平线渲染
          hr: () => (
            <hr className="markdown-hr" />
          ),

        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  )
}

export default MarkdownRenderer
