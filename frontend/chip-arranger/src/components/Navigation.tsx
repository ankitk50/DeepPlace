import { Cpu } from "lucide-react";

export const Navigation = () => {
  return (
    <nav className="border-b border-white/20 backdrop-blur-xl bg-[#089145]/90 sticky top-0 z-50">
      <div className="container mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          {/* Logo */}
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-white/10 border border-white/40 flex items-center justify-center neon-glow">
              <Cpu className="w-6 h-6 text-white" />
            </div>
            <span className="text-2xl font-bold uppercase tracking-[0.35em] text-white drop-shadow-sm">
              DEEPLACE
            </span>
          </div>

          {/* Navigation Links */}
          <div className="hidden md:flex items-center gap-8">
            <a href="#home" className="text-white font-semibold tracking-wide border-b-2 border-white/60">
              HOME
            </a>
          </div>
        </div>
      </div>
    </nav>
  );
};
