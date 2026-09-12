export default function KnowledgeBase() {
  const documents = [
    { id: 1, title: "Fee Schedule 2026", category: "Fees", updated: "2026-08-01" },
    { id: 2, title: "Academic Calendar", category: "Academics", updated: "2026-07-15" },
    { id: 3, title: "Student Handbook", category: "Policies", updated: "2026-06-20" },
    { id: 4, title: "Programme Catalog", category: "Programmes", updated: "2026-08-10" },
  ];

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-6">Knowledge Base</h1>
      <table className="w-full bg-white rounded-lg shadow overflow-hidden">
        <thead className="bg-gray-200 text-left">
          <tr>
            <th className="p-3">Title</th>
            <th className="p-3">Category</th>
            <th className="p-3">Last Updated</th>
          </tr>
        </thead>
        <tbody>
          {documents.map((doc) => (
            <tr key={doc.id} className="border-t">
              <td className="p-3">{doc.title}</td>
              <td className="p-3">{doc.category}</td>
              <td className="p-3">{doc.updated}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}