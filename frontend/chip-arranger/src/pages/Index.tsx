import { useState } from "react";
import { UploadZone } from "@/components/UploadZone";
import { ProcessingState } from "@/components/ProcessingState";
import { ResultsView } from "@/components/ResultsView";
import { Navigation } from "@/components/Navigation";

type AppState = "upload" | "processing" | "results";

const API_BASE_URL = "http://127.0.0.1:8000";

const Index = () => {
  const [state, setState] = useState<AppState>("upload");
  const [originalImage, setOriginalImage] = useState<string>("");
  const [optimizedImage, setOptimizedImage] = useState<string>("");
  const [error, setError] = useState<string | null>(null);

  const uploadToBackend = async (file: File) => {
    const formData = new FormData();
    formData.append("image", file);
    formData.append("aspect", "1:1");
    formData.append("num", "5");
    formData.append("sleep", "0.75");
    formData.append("timeout", "300");

    const response = await fetch(`${API_BASE_URL}/generate`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      let message = "Failed to generate optimized layout.";
      try {
        const errorJson = await response.json();
        message = errorJson?.detail ?? message;
      } catch {
        // ignore if response is not JSON
      }
      throw new Error(message);
    }

    const data = await response.json();
    if (!data?.image_url) {
      const fallbackMessage = data?.message || "Best candidate missing from response.";
      throw new Error(fallbackMessage);
    }
    const imageUrl = new URL(data.image_url, API_BASE_URL).toString();
    return imageUrl;
  };

  const handleFileSelect = async (file: File) => {
    setError(null);
    const reader = new FileReader();
    reader.onload = (e) => {
      const result = e.target?.result as string;
      setOriginalImage(result);
    };
    reader.readAsDataURL(file);

    setState("processing");
    try {
      const optimizedResult = await uploadToBackend(file);
      setOptimizedImage(optimizedResult);
      setState("results");
    } catch (err) {
      console.error(err);
      setError(err instanceof Error ? err.message : "Something went wrong.");
      setOriginalImage("");
      setOptimizedImage("");
      setState("upload");
    }
  };

  const handleReset = () => {
    setState("upload");
    setOriginalImage("");
    setOptimizedImage("");
    setError(null);
  };

  return (
    <div className="min-h-screen bg-background tech-stars gradient-mesh relative overflow-hidden">
      <Navigation />
      
      <div className="relative z-10">
        {/* Main Content */}
        <main className="container mx-auto px-6 py-16">
          {state === "upload" && (
            <div className="flex items-center justify-center min-h-[calc(100vh-200px)]">
              {/* Content */}
              <div className="space-y-8 animate-fade-in max-w-2xl w-full">
                {error && (
                  <div className="text-destructive bg-destructive/10 border border-destructive/30 rounded-lg p-4 text-left">
                    <p className="font-semibold mb-1">Upload failed</p>
                    <p className="text-sm text-destructive">{error}</p>
                  </div>
                )}
                <div className="space-y-6 text-center">
                  <h1 className="text-5xl lg:text-6xl font-bold leading-tight">
                    <span className="text-primary">AI Chip Placement</span>
                    <br />
                    <span className="text-foreground">Optimization for PCBs</span>
                  </h1>
                  <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
                    Minimize PCB area and maximize efficiency. Upload your current chaotic layout, and we generate the optimal, minimized chip arrangement.
                  </p>
                </div>
                
                <UploadZone onFileSelect={handleFileSelect} />
              </div>
            </div>
          )}

          {state === "processing" && <ProcessingState />}

          {state === "results" && (
            <ResultsView
              originalImage={originalImage}
              optimizedImage={optimizedImage}
              onReset={handleReset}
            />
          )}
        </main>
      </div>
    </div>
  );
};

export default Index;
