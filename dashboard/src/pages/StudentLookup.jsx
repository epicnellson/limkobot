export default function StudentLookup() {
  const students = [
    { id: 1, name: "Aminata Kamara", phone: "+23276123456", programme: "BSc Computer Science", verified: true },
    { id: 2, name: "Ibrahim Sesay", phone: "+23277234567", programme: "BSc Software Engineering", verified: true },
    { id: 3, name: "Fatmata Jalloh", phone: "+23278345678", programme: "BA Business Admin", verified: false },
  ];

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-6">Student Lookup</h1>
      <input
        type="text"
        placeholder="Search by name or phone number..."
        className="w-full border rounded px-3 py-2 mb-6"
      />
      <table className="w-full bg-white rounded-lg shadow overflow-hidden">
        <thead className="bg-gray-200 text-left">
          <tr>
            <th className="p-3">Name</th>
            <th className="p-3">Phone</th>
            <th className="p-3">Programme</th>
            <th className="p-3">OTP Verified</th>
          </tr>
        </thead>
        <tbody>
          {students.map((s) => (
            <tr key={s.id} className="border-t">
              <td className="p-3">{s.name}</td>
              <td className="p-3">{s.phone}</td>
              <td className="p-3">{s.programme}</td>
              <td className="p-3">{s.verified ? "✅" : "❌"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}