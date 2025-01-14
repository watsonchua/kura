"use client";

import { useState } from "react";
import { Upload } from "lucide-react";
import { Button } from "@/components/ui/button";
import { analyticsSchema, type Analytics } from "@/types/analytics";

interface UploadButtonProps {
  onSuccess: (data: Analytics) => void;
}

export function UploadButton({ onSuccess }: UploadButtonProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    if (file.type !== "application/json") {
      alert("Please upload a JSON file");
      return;
    }

    setSelectedFile(file);
  };

  const handleSubmit = async () => {
    if (!selectedFile) return;

    setIsLoading(true);
    try {
      const fileContent = await selectedFile.text();
      const jsonData = JSON.parse(fileContent);

      const response = await fetch("http://127.0.0.1:8000/api/analyse", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          data: jsonData,
        }),
      });

      if (!response.ok) {
        throw new Error("Upload failed");
      }

      const data = await response.json();
      const validatedData = analyticsSchema.parse(data);

      onSuccess(validatedData);
    } catch (error) {
      console.error(error);
      alert("Error uploading file");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex gap-2 justify-center my-8">
      <div className="relative">
        <input
          type="file"
          accept="application/json"
          onChange={handleFileChange}
          className="absolute inset-0 w-full opacity-0 cursor-pointer"
          disabled={isLoading}
        />
        <Button
          variant="outline"
          size="sm"
          className="text-xs"
          disabled={isLoading}
        >
          <Upload className="mr-2 h-3 w-3" />
          {selectedFile ? `${selectedFile.name}` : "Upload your conversations"}
        </Button>
      </div>

      <Button
        variant="default"
        size="sm"
        className="text-xs"
        disabled={isLoading || !selectedFile}
        onClick={handleSubmit}
      >
        {isLoading ? (
          <div className="flex items-center">
            <svg
              className="animate-spin -ml-1 mr-2 h-3 w-3"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              ></circle>
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              ></path>
            </svg>
            Processing...
          </div>
        ) : (
          "Submit File"
        )}
      </Button>
    </div>
  );
}
