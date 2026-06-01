export function DataCard({ children, className = '', title, action }) {
  return (
    <div className={`card ${className}`}>
      {title && (
        <div className="px-5 py-4 border-b border-[var(--border-primary)] flex items-center justify-between">
          <span className="section-label">{title}</span>
          {action}
        </div>
      )}
      <div className="p-5">{children}</div>
    </div>
  );
}