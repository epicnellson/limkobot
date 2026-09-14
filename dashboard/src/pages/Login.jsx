export default function Login() {
  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-100">
      <div className="bg-white p-8 rounded-lg shadow-md w-80">
        <h1 className="text-xl font-bold mb-4 text-center">Admin Login</h1>
        <input
          type="tel"
          placeholder="Phone number"
          className="w-full border rounded px-3 py-2 mb-4"
        />
        <button className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700">
          Send OTP
        </button>
      </div>
    </div>
  );
}