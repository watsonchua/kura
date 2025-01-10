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
          Select conversations.json
        </Button>
      </div>

      <Button
        variant="default"
        size="sm"
        className="text-xs"
        disabled={isLoading || !selectedFile}
        onClick={handleSubmit}
      >
        {isLoading ? "Uploading..." : "Submit File"}
      </Button>
    </div>
  );
}
