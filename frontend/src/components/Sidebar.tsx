import Link from 'next/link';

export default function Sidebar() {
  return (
    <div className="w-64 h-screen glass border-r flex flex-col p-6">
      <div className="mb-10">
        <h1 className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-primary to-accent">
          EPC-Intel
        </h1>
        <p className="text-xs text-gray-400 mt-1">Data Centre Delivery</p>
      </div>

      <nav className="flex-1 space-y-2">
        <Link href="/dashboard" className="block px-4 py-3 rounded-xl hover:bg-white/10 transition-colors">
          Dashboard
        </Link>
        <Link href="/upload" className="block px-4 py-3 rounded-xl hover:bg-white/10 transition-colors">
          Upload Document
        </Link>
        <Link href="/compliance" className="block px-4 py-3 rounded-xl hover:bg-white/10 transition-colors">
          Compliance Review
        </Link>
        <Link href="/rfi" className="block px-4 py-3 rounded-xl hover:bg-white/10 transition-colors">
          RFI Chat
        </Link>
      </nav>

      <div className="mt-auto">
        <Link href="/" className="block px-4 py-3 rounded-xl text-red-400 hover:bg-white/10 transition-colors">
          Logout
        </Link>
      </div>
    </div>
  );
}
