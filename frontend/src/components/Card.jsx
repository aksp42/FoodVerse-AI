export default function Card({ as: Tag = 'section', title, subtitle, action, padded = true, className = '', children, ...rest }) {
  return (
    <Tag className={`card ${padded ? '' : 'card--flush'} ${className}`} {...rest}>
      {(title || action) && (
        <header className="card__head">
          <div>
            {title && <h3 className="card__title">{title}</h3>}
            {subtitle && <p className="card__subtitle">{subtitle}</p>}
          </div>
          {action}
        </header>
      )}
      {children}
    </Tag>
  );
}
