"use client";

import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';
import 'highlight.js/styles/github-dark.css';

interface MarkdownRendererProps {
  content: string | null;
  className?: string;
  variant?: 'default' | 'error';
}

/**
 * Detects if content contains markdown syntax
 */
function isMarkdown(content: string): boolean {
  // Check for common markdown patterns
  const markdownPatterns = [
    /^#{1,6}\s/m,           // Headers
    /\*\*.*\*\*/,           // Bold
    /\*.*\*/,               // Italic
    /__.*__/,               // Bold (alternative)
    /_.*_/,                 // Italic (alternative)
    /```[\s\S]*?```/,       // Code blocks
    /`[^`]+`/,              // Inline code
    /^\s*[-*+]\s/m,         // Unordered lists
    /^\s*\d+\.\s/m,         // Ordered lists
    /\[.*\]\(.*\)/,         // Links
    /!\[.*\]\(.*\)/,        // Images
    /^\s*>\s/m,             // Blockquotes
    /\|.*\|/,               // Tables
    /~~.*~~/,               // Strikethrough
    /^\s*-{3,}\s*$/m,       // Horizontal rules
    /^\s*\*{3,}\s*$/m,      // Horizontal rules (alternative)
  ];

  return markdownPatterns.some(pattern => pattern.test(content));
}

export const MarkdownRenderer = React.memo(({
  content,
  className = '',
  variant = 'default'
}: MarkdownRendererProps) => {
  const textColor = variant === 'error' ? 'text-red-400' : 'text-[var(--mc-text-primary)]';

  // Handle null or empty content
  if (!content) {
    return null;
  }

  // If content doesn't look like markdown, render as plain text
  if (!isMarkdown(content)) {
    return (
      <pre className={`text-sm ${textColor} whitespace-pre-wrap font-mono ${className}`}>
        {content}
      </pre>
    );
  }

  // Render as markdown
  return (
    <div className={`markdown-content ${textColor} ${className}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeHighlight]}
        components={{
          // Headings
          h1: ({ children }) => (
            <h1 className="text-2xl font-bold text-[var(--mc-text-primary)] mb-4 pb-2 border-b border-[var(--mc-border)]">
              {children}
            </h1>
          ),
          h2: ({ children }) => (
            <h2 className="text-xl font-bold text-[var(--mc-text-primary)] mb-3 pb-2 border-b border-[var(--mc-border)]">
              {children}
            </h2>
          ),
          h3: ({ children }) => (
            <h3 className="text-lg font-bold text-[var(--mc-text-primary)] mb-2">
              {children}
            </h3>
          ),
          h4: ({ children }) => (
            <h4 className="text-base font-bold text-[var(--mc-text-primary)] mb-2">
              {children}
            </h4>
          ),
          h5: ({ children }) => (
            <h5 className="text-sm font-bold text-[var(--mc-text-primary)] mb-2">
              {children}
            </h5>
          ),
          h6: ({ children }) => (
            <h6 className="text-xs font-bold text-[var(--mc-text-primary)] mb-2">
              {children}
            </h6>
          ),

          // Paragraphs
          p: ({ children }) => (
            <p className="mb-4 leading-relaxed">
              {children}
            </p>
          ),

          // Code blocks
          pre: ({ children }) => (
            <pre className="bg-[var(--mc-bg-tertiary)] rounded-md p-4 mb-4 overflow-x-auto border border-[var(--mc-border)]">
              {children}
            </pre>
          ),
          code: ({ inline, className, children, ...props }: any) => {
            if (inline) {
              return (
                <code
                  className="bg-[var(--mc-bg-tertiary)] text-[var(--mc-accent-blue)] px-1.5 py-0.5 rounded text-sm font-mono"
                  {...props}
                >
                  {children}
                </code>
              );
            }
            return (
              <code className={`${className || ''} text-sm`} {...props}>
                {children}
              </code>
            );
          },

          // Links
          a: ({ href, children }) => (
            <a
              href={href}
              target="_blank"
              rel="noopener noreferrer"
              className="text-[var(--mc-accent-blue)] hover:opacity-80 underline decoration-[var(--mc-accent-blue)]/30 hover:decoration-[var(--mc-accent-blue)] transition-colors"
            >
              {children}
            </a>
          ),

          // Lists
          ul: ({ children }) => (
            <ul className="list-disc list-inside mb-4 space-y-1 ml-4">
              {children}
            </ul>
          ),
          ol: ({ children }) => (
            <ol className="list-decimal list-inside mb-4 space-y-1 ml-4">
              {children}
            </ol>
          ),
          li: ({ children }) => (
            <li className="leading-relaxed">
              {children}
            </li>
          ),

          // Blockquotes
          blockquote: ({ children }) => (
            <blockquote className="border-l-4 border-[var(--mc-accent-blue)] pl-4 py-2 mb-4 italic text-[var(--mc-text-secondary)] bg-[var(--mc-bg-tertiary)] rounded-r">
              {children}
            </blockquote>
          ),

          // Tables
          table: ({ children }) => (
            <div className="overflow-x-auto mb-4">
              <table className="min-w-full border-collapse border border-[var(--mc-border)]">
                {children}
              </table>
            </div>
          ),
          thead: ({ children }) => (
            <thead className="bg-[var(--mc-bg-tertiary)]">
              {children}
            </thead>
          ),
          tbody: ({ children }) => (
            <tbody>
              {children}
            </tbody>
          ),
          tr: ({ children }) => (
            <tr className="border-b border-[var(--mc-border)] hover:bg-[var(--mc-bg-tertiary)] transition-colors">
              {children}
            </tr>
          ),
          th: ({ children }) => (
            <th className="border border-[var(--mc-border)] px-4 py-2 text-left font-semibold text-[var(--mc-text-primary)]">
              {children}
            </th>
          ),
          td: ({ children }) => (
            <td className="border border-[var(--mc-border)] px-4 py-2 text-[var(--mc-text-primary)]">
              {children}
            </td>
          ),

          // Horizontal rule
          hr: () => (
            <hr className="border-t border-[var(--mc-border)] my-6" />
          ),

          // Strong and emphasis
          strong: ({ children }) => (
            <strong className="font-bold text-[var(--mc-text-primary)]">
              {children}
            </strong>
          ),
          em: ({ children }) => (
            <em className="italic text-[var(--mc-text-primary)]">
              {children}
            </em>
          ),

          // Strikethrough (from GFM)
          del: ({ children }) => (
            <del className="line-through text-[var(--mc-text-tertiary)]">
              {children}
            </del>
          ),

          // Task list items (from GFM)
          input: ({ type, checked, disabled }) => {
            if (type === 'checkbox') {
              return (
                <input
                  type="checkbox"
                  checked={checked}
                  disabled={disabled}
                  className="mr-2 accent-[var(--mc-accent-blue)]"
                  readOnly
                />
              );
            }
            return <input type={type} />;
          },
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
});

MarkdownRenderer.displayName = 'MarkdownRenderer';
