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
            relative border-2 border-dashed rounded-2xl transition-all duration-300 bg-white/5 backdrop-blur-lg text-white
            ${isDragging 
              ? "neon-border scale-[1.02]" 
              : "border-white/40 hover:border-white hover:scale-[1.01]"
            }
          `}
        >
          <div className="p-12 text-center">
            <div className="mb-6 flex justify-center">
              <div className={`
                transition-all duration-300 p-4 rounded-full bg-white/10 border border-white/50
                ${isDragging ? "neon-glow scale-110" : ""}
              `}>
                <CloudUpload className="w-16 h-16 text-white" strokeWidth={1.5} />
              </div>
            </div>
            
            <p className="text-xl text-white mb-2 font-semibold tracking-wide">
              Drag & Drop Image Here
            </p>
            <p className="text-lg text-white/70">
              or Click to Upload
            </p>
          </div>
        </div>
      </label>
    </div>
  );
};
