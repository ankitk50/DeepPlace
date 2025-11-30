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

  const floatingShapes = [
    { top: "6%", left: "8%", size: 80, rotate: "-8deg", opacity: 0.2 },
    { top: "14%", right: "12%", size: 70, rotate: "12deg", opacity: 0.25 },
    { bottom: "15%", left: "6%", size: 110, rotate: "-18deg", opacity: 0.15 },
    { bottom: "8%", right: "8%", size: 120, rotate: "22deg", opacity: 0.2 },
  ];

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
    <div className="min-h-screen relative overflow-hidden bg-[#089145] text-white">
      {floatingShapes.map((shape, index) => (
        <div
          key={index}
          className="absolute border-4 rounded-xl opacity-40"
          style={{
            top: shape.top,
            right: shape.right,
            bottom: shape.bottom,
            left: shape.left,
            width: `${shape.size}px`,
            height: `${shape.size}px`,
            transform: `rotate(${shape.rotate})`,
            borderColor: `rgba(255,255,255,${shape.opacity})`,
          }}
        />
      ))}
      <Navigation />
      
      <div className="relative z-10">
        {/* Main Content */}
        <main className="container mx-auto px-6 py-16">
          {state === "upload" && (
            <div className="grid lg:grid-cols-2 gap-12 items-center min-h-[calc(100vh-220px)]">
              <div className="space-y-8">
                <div className="space-y-4">
                  <p className="uppercase tracking-[0.35em] text-white/80 text-sm">Revolutionizing spatial optimization</p>
                  <h1 className="text-5xl lg:text-6xl font-bold leading-tight drop-shadow-md flex flex-wrap items-center gap-2">
                    <span>DEE</span>
                    <span className="inline-flex items-center gap-3">
                      P
                      <span className="grid grid-cols-2 gap-1 auto-rows-[1rem]">
                        {Array.from({ length: 6 }).map((_, index) => {
                          const filledIndices = new Set([0, 2, 4, 5]); // L-shape
                          return filledIndices.has(index) ? (
                            <span key={index} className="w-4 h-4 border border-white rounded-sm inline-block" />
                          ) : (
                            <span key={index} className="w-4 h-4 inline-block" />
                          );
                        })}
                      </span>
                    </span>
                    <span>lace</span>
                  </h1>
                  <p className="text-xl text-white/90">Revolutionizing Spatial Optimization (with Flux)</p>
                </div>
                <p className="text-lg text-white/80 max-w-xl">
                  Upload your PCB layout and let DeePlace minimize area while keeping every chip in perfect harmony. Flux-powered intelligence, simple workflow.
                </p>
              </div>

              <div className="bg-white/10 backdrop-blur-md rounded-3xl border border-white/20 p-8 shadow-2xl">
                {error && (
                  <div className="text-red-200 bg-red-500/10 border border-red-200/40 rounded-lg p-4 text-left mb-6">
                    <p className="font-semibold mb-1">Upload failed</p>
                    <p className="text-sm">{error}</p>
                  </div>
                )}
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
