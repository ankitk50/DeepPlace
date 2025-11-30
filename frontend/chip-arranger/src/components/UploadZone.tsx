import { CloudUpload } from "lucide-react";
import { useCallback, useState } from "react";
import { Button } from "./ui/button";

interface UploadZoneProps {
  onFileSelect: (file: File) => void;
}

export const UploadZone = ({ onFileSelect }: UploadZoneProps) => {
  const [isDragging, setIsDragging] = useState(false);

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDragIn = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  }, []);

  const handleDragOut = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const files = e.dataTransfer.files;
    if (files && files[0]) {
      onFileSelect(files[0]);
    }
  }, [onFileSelect]);

  const handleFileInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files[0]) {
      onFileSelect(files[0]);
    }
  }, [onFileSelect]);

  return (
    <div className="space-y-6">
      <input
        type="file"
        id="file-upload"
        className="hidden"
        accept="image/*"
        onChange={handleFileInput}
      />
      <label htmlFor="file-upload" className="cursor-pointer block">
        <div
          onDragEnter={handleDragIn}
          onDragLeave={handleDragOut}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          className={`
            relative border-2 border-dashed rounded-xl transition-all duration-300 bg-card/30 backdrop-blur-sm
            ${isDragging 
              ? "neon-border scale-[1.02]" 
              : "border-border hover:border-primary/50 hover:scale-[1.01]"
            }
          `}
        >
          <div className="p-12 text-center">
            <div className="mb-6 flex justify-center">
              <div className={`
                transition-all duration-300 p-4 rounded-full bg-primary/10 border border-primary/30
                ${isDragging ? "neon-glow scale-110" : ""}
              `}>
                <CloudUpload className="w-16 h-16 text-primary" strokeWidth={1.5} />
              </div>
            </div>
            
            <p className="text-xl text-foreground mb-2 font-medium">
              Drag & Drop Image Here
            </p>
            <p className="text-lg text-muted-foreground">
              or Click to Upload
            </p>
          </div>
        </div>
      </label>
    </div>
  );
};
