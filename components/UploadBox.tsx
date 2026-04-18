"use client";

import { useState, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { AlertCircle, CheckCircle, Loader } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";

interface UploadStatus {
  filename: string;
  status: "pending" | "uploading" | "success" | "error";
  message: string;
  data?: any;
  progress: number;
}

export default function UploadBox() {
  const [uploads, setUploads] = useState<UploadStatus[]>([]);
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleUpload = async (files: FileList | null) => {
    if (!files) return;

    for (let i = 0; i < files.length; i++) {
      const file = files[i];

      // Validate file type
      const allowedTypes = [
        "application/pdf",
        "image/jpeg",
        "image/png",
        "text/plain",
      ];

      if (!allowedTypes.includes(file.type)) {
        setUploads((prev) => [
          ...prev,
          {
            filename: file.name,
            status: "error",
            message: "Invalid file type. Please upload PDF, image, or text.",
            progress: 0,
          },
        ]);
        continue;
      }

      // Add pending upload
      const uploadId = `${file.name}-${Date.now()}`;
      setUploads((prev) => [
        ...prev,
        {
          filename: file.name,
          status: "uploading",
          message: "Uploading...",
          progress: 30,
        },
      ]);

      try {
        const formData = new FormData();
        formData.append("file", file);

        const response = await fetch("http://localhost:8000/api/upload/analyze", {
          method: "POST",
          body: formData,
        });

        if (!response.ok) {
          throw new Error(`Upload failed: ${response.status}`);
        }

        const data = await response.json();

        // Update to success
        setUploads((prev) =>
          prev.map((u) =>
            u.filename === file.name
              ? {
                  ...u,
                  status: "success",
                  message: "Analysis complete",
                  data: data,
                  progress: 100,
                }
              : u
          )
        );
      } catch (error) {
        setUploads((prev) =>
          prev.map((u) =>
            u.filename === file.name
              ? {
                  ...u,
                  status: "error",
                  message:
                    error instanceof Error
                      ? error.message
                      : "Upload failed",
                  progress: 0,
                }
              : u
          )
        );
      }
    }
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files) {
      handleUpload(e.dataTransfer.files);
    }
  };

  return (
    <Card className="w-full h-full flex flex-col">
      <CardHeader>
        <CardTitle className="text-lg">Upload Medical Reports</CardTitle>
      </CardHeader>

      <CardContent className="flex-1 flex flex-col space-y-4">
        {/* Drop Zone */}
        <div
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition ${
            dragActive
              ? "border-primary bg-primary/5"
              : "border-muted-foreground/25"
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            multiple
            onChange={(e) => handleUpload(e.target.files)}
            className="hidden"
            accept=".pdf,.jpg,.jpeg,.png,.txt"
          />

          <div
            onClick={() => fileInputRef.current?.click()}
            className="space-y-2"
          >
            <p className="text-sm font-medium">
              Drag files here or click to browse
            </p>
            <p className="text-xs text-muted-foreground">
              Supported: PDF, JPEG, PNG, TXT
            </p>
          </div>
        </div>

        {/* Upload History */}
        <div className="space-y-2 flex-1 overflow-y-auto">
          {uploads.length === 0 ? (
            <p className="text-xs text-muted-foreground text-center py-4">
              No uploads yet
            </p>
          ) : (
            uploads.map((upload, idx) => (
              <div
                key={`${upload.filename}-${idx}`}
                className="border rounded-lg p-3 space-y-2"
              >
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2 flex-1 min-w-0">
                    {upload.status === "uploading" && (
                      <Loader className="h-4 w-4 animate-spin flex-shrink-0" />
                    )}
                    {upload.status === "success" && (
                      <CheckCircle className="h-4 w-4 text-green-600 flex-shrink-0" />
                    )}
                    {upload.status === "error" && (
                      <AlertCircle className="h-4 w-4 text-red-600 flex-shrink-0" />
                    )}

                    <p className="text-sm truncate">{upload.filename}</p>
                  </div>

                  <span className="text-xs px-2 py-1 rounded-full bg-muted">
                    {upload.progress}%
                  </span>
                </div>

                {upload.status === "uploading" && (
                  <div className="w-full bg-muted rounded-full h-1">
                    <div
                      className="bg-primary h-1 rounded-full transition-all"
                      style={{ width: `${upload.progress}%` }}
                    />
                  </div>
                )}

                <p className="text-xs text-muted-foreground">{upload.message}</p>

                {upload.data?.analysis && (
                  <Alert className="mt-2">
                    <AlertDescription className="text-xs">
                      {upload.data.analysis.summary}
                    </AlertDescription>
                  </Alert>
                )}
              </div>
            ))
          )}
        </div>
      </CardContent>
    </Card>
  );
}
