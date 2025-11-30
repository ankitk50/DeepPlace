import logo from "@/assets/placeopt-logo.png";
import { Cpu } from "lucide-react";

export const Navigation = () => {
  return (
    <nav className="border-b border-border/50 backdrop-blur-xl bg-background/80 sticky top-0 z-50">
      <div className="container mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          {/* Logo */}
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-card/50 border border-primary/30 flex items-center justify-center neon-glow">
              <Cpu className="w-6 h-6 text-primary" />
            </div>
            <span className="text-2xl font-bold text-primary tracking-wider">
              PLACEOPT
            </span>
          </div>

          {/* Navigation Links */}
          <div className="hidden md:flex items-center gap-8">
            <a href="#home" className="text-primary font-semibold tracking-wide border-b-2 border-primary">
              HOME
            </a>
          </div>
        </div>
      </div>
    </nav>
  );
};
