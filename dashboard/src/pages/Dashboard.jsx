export default function Dashboard() {
  const stats = [
    { label: "Total Students", value: 42 },
    { label: "Flagged Conversations", value: 3 },
    { label: "Knowledge Documents", value: 12 },
    { label: "Pending Document Requests", value: 5 },
  ];

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-6">Dashboard Overview</h1>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {stats.map((stat) => (
          <div key={stat.label} className="bg-white p-4 rounded-lg shadow">
            <p className="text-gray-500 text-sm">{stat.label}</p>
            <p className="text-3xl font-bold mt-2">{stat.value}</p>
          </div>
        ))}
      </div>
    </div>
  );
}