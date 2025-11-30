import { Loader2, Cpu } from "lucide-react";

export const ProcessingState = () => {
  return (
    <div className="flex flex-col items-center justify-center py-20 px-4 animate-fade-in min-h-[calc(100vh-200px)]">
      <div className="relative mb-8">
        <div className="absolute inset-0 bg-primary/20 rounded-full blur-3xl animate-pulse"></div>
        <div className="relative p-8 rounded-full bg-card/50 border border-primary/30 neon-glow backdrop-blur-sm">
          <Cpu className="w-20 h-20 text-primary animate-pulse" />
        </div>
      </div>
      
      <div className="flex items-center gap-3 mb-4">
        <Loader2 className="w-6 h-6 animate-spin text-primary" />
        <h2 className="text-3xl font-bold text-foreground tracking-wider">PROCESSING</h2>
      </div>
      
      <p className="text-muted-foreground text-center max-w-md mb-8 text-lg">
        Analyzing your PCB layout and optimizing chip placement...
      </p>
      
      <div className="w-80 h-3 bg-secondary/50 rounded-full overflow-hidden backdrop-blur-sm border border-border">
        <div 
          className="h-full bg-gradient-to-r from-primary to-accent rounded-full transition-all duration-1000 ease-out neon-glow" 
          style={{ width: '65%' }}
        />
      </div>
    </div>
  );
};
