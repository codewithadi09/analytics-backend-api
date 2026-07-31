export function ComingSoon({ title }: { title: string }) {
  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">{title}</h1>
      </div>
      <div className="card flex items-center justify-center py-16">
        <p className="empty-state">This page is built in the next phase.</p>
      </div>
    </div>
  );
}
