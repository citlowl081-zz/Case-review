import React from 'react';
import ReactMarkdown from 'react-markdown';

interface Props {
  text: string;
}

export default function StreamText({ text }: Props) {
  return (
    <div className="stream-text">
      <ReactMarkdown>{text}</ReactMarkdown>
      {text && (
        <span
          className="stream-cursor"
          style={{
            display: 'inline-block',
            width: 2,
            height: 18,
            backgroundColor: '#1677ff',
            marginLeft: 2,
            animation: 'blink 1s step-end infinite',
            verticalAlign: 'text-bottom',
          }}
        />
      )}
      <style>{`
        @keyframes blink {
          0%, 100% { opacity: 1; }
          50% { opacity: 0; }
        }
        .stream-text p { margin-bottom: 8px; }
        .stream-text p:last-child { margin-bottom: 0; }
        .stream-text table { border-collapse: collapse; margin: 8px 0; }
        .stream-text th, .stream-text td {
          border: 1px solid #e0e0e0;
          padding: 4px 8px;
          text-align: left;
        }
        .stream-text th { background: #f5f5f5; font-weight: 600; }
      `}</style>
    </div>
  );
}
