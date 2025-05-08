export default function MenuCard({ children }: { children: React.ReactNode }) {
  return (
    <div className="mx-auto w-full h-full pt-6 pb-6 pl-6">
      <div className="relative h-full">
        {/* Bottom shadow layer */}
        <div className="absolute -bottom-2 -right-2 w-full h-full bg-gray-300 rounded-xl"></div>

        {/* Middle shadow layer */}
        <div className="absolute -bottom-1 -right-1 w-full h-full bg-gray-200 rounded-xl"></div>

        {/* Main card */}
        <div className="relative bg-neutral-50 text-gray-900 rounded-xl p-6 shadow-lg border border-gray-100 w-full h-full overflow-y-auto">
          {children}
        </div>
      </div>
    </div>
  );
}
