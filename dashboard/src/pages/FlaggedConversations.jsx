export default function FlaggedConversations() {
  const flags = [
    { id: 1, student: "Aminata K.", severity: "High", message: "I don't know how much more I can take...", resolved: false },
    { id: 2, student: "Ibrahim S.", severity: "Medium", message: "Feeling really overwhelmed with exams", resolved: false },
    { id: 3, student: "Fatmata J.", severity: "Low", message: "Stressed about fees but managing", resolved: true },
  ];

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-6">Flagged Conversations</h1>
      <div className="space-y-4">
        {flags.map((flag) => (
          <div key={flag.id} className="bg-white p-4 rounded-lg shadow flex justify-between items-start">
            <div>
              <p className="font-semibold">{flag.student}</p>
              <p className="text-gray-600 text-sm mt-1">{flag.message}</p>
            </div>
            <div className="text-right">
              <span
                className={`px-2 py-1 rounded text-xs font-bold ${
                  flag.severity === "High"
                    ? "bg-red-100 text-red-700"
                    : flag.severity === "Medium"
                    ? "bg-yellow-100 text-yellow-700"
                    : "bg-green-100 text-green-700"
                }`}
              >
                {flag.severity}
              </span>
              <p className="text-xs text-gray-400 mt-2">
                {flag.resolved ? "Resolved" : "Pending"}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}