import { Download, RotateCcw, CheckCircle2 } from "lucide-react";
import { Button } from "./ui/button";
import { Card } from "./ui/card";

interface ResultsViewProps {
  originalImage: string;
  optimizedImage: string;
  onReset: () => void;
}

export const ResultsView = ({ originalImage, optimizedImage, onReset }: ResultsViewProps) => {
  const handleDownload = () => {
    const link = document.createElement('a');
    link.href = optimizedImage;
    link.download = 'optimized-pcb.png';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="w-full space-y-8 animate-fade-in min-h-[calc(100vh-200px)] py-12">
      <div className="flex items-center justify-center gap-3 mb-8">
        <CheckCircle2 className="w-8 h-8 text-primary neon-glow" />
        <h2 className="text-4xl font-bold text-foreground tracking-wider">OPTIMIZATION COMPLETE</h2>
      </div>

      <div className="grid md:grid-cols-2 gap-6 max-w-6xl mx-auto">
        <Card className="p-6 space-y-4 bg-card/30 backdrop-blur-sm border-border/50">
          <h3 className="text-lg font-semibold text-muted-foreground tracking-wider">ORIGINAL LAYOUT</h3>
          <div className="relative aspect-square rounded-lg overflow-hidden border border-border bg-secondary/30">
            <img 
              src={originalImage} 
              alt="Original PCB layout" 
              className="w-full h-full object-contain"
            />
          </div>
        </Card>

        <Card className="p-6 space-y-4 bg-card/30 backdrop-blur-sm neon-border">
          <h3 className="text-lg font-semibold text-primary tracking-wider">OPTIMIZED LAYOUT</h3>
          <div className="relative aspect-square rounded-lg overflow-hidden border border-primary/50 bg-secondary/30">
            <img 
              src={optimizedImage} 
              alt="Optimized PCB layout" 
              className="w-full h-full object-contain"
            />
          </div>
        </Card>
      </div>

      <div className="flex gap-4 justify-center pt-4">
        <Button 
          onClick={handleDownload} 
          size="lg"
          className="rounded-full px-8 neon-glow hover:scale-105 transition-transform font-semibold tracking-wide border border-primary/50"
        >
          <Download className="w-5 h-5 mr-2" />
          DOWNLOAD RESULT
        </Button>
        <Button 
          onClick={onReset} 
          variant="outline"
          size="lg"
          className="rounded-full px-8 hover:scale-105 transition-transform font-semibold tracking-wide border-primary/50 hover:bg-primary/10"
        >
          <RotateCcw className="w-5 h-5 mr-2" />
          OPTIMIZE ANOTHER
        </Button>
      </div>
    </div>
  );
};
