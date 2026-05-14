"use client";
import { useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { FileAudio, FileImage, FileText, FileType, Upload } from "lucide-react";
import { cn } from "@/lib/utils";

const ACCEPTED_EXTENSIONS = {
  "application/pdf": [".pdf"],
  "application/msword": [".doc"],
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
  "image/*": [".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tiff"],
  "audio/*": [".mp3", ".wav", ".m4a", ".flac", ".ogg", ".aac"],
  "video/*": [".mp4", ".mkv", ".avi", ".mov", ".webm"],
};

interface Props {
  onFiles: (files: File[]) => void;
  disabled?: boolean;
}

export function Dropzone({ onFiles, disabled }: Props) {
  const onDrop = useCallback(
    (accepted: File[]) => {
      if (accepted.length) onFiles(accepted);
    },
    [onFiles]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: ACCEPTED_EXTENSIONS,
    maxSize: 50 * 1024 * 1024, // 50MB
    disabled,
  });

  return (
    <div
      {...getRootProps()}
      className={cn(
        "relative flex min-h-72 cursor-pointer flex-col items-center justify-center rounded-lg border border-dashed p-8 text-center transition-all",
        isDragActive
          ? "border-teal-300/70 bg-teal-300/8"
          : "border-white/14 bg-white/[0.025] hover:border-white/24 hover:bg-white/[0.04]",
        disabled && "opacity-40 pointer-events-none"
      )}
    >
      <input {...getInputProps()} />
      <div
        className={cn(
          "mb-4 flex h-14 w-14 items-center justify-center rounded-lg transition-colors",
          isDragActive ? "bg-teal-300/16 text-teal-300" : "bg-white/6 text-white/45"
        )}
      >
        {isDragActive ? <FileType className="h-6 w-6" /> : <Upload className="h-6 w-6" />}
      </div>
      {isDragActive ? (
        <p className="text-sm text-violet-400 font-medium">Drop to ingest</p>
      ) : (
        <>
          <p className="text-sm font-medium text-white/76">
            Drag files here or <span className="text-teal-300">click to upload</span>
          </p>
          <p className="mt-1 text-xs text-white/34">
            PDF, DOCX, images, audio, video — up to 50 MB
          </p>
          <div className="mt-5 flex flex-wrap justify-center gap-2 text-xs text-white/36">
            <span className="flex items-center gap-1 rounded-md bg-white/[0.04] px-2 py-1">
              <FileText className="h-3 w-3 text-blue-300" />
              Text
            </span>
            <span className="flex items-center gap-1 rounded-md bg-white/[0.04] px-2 py-1">
              <FileImage className="h-3 w-3 text-amber-300" />
              OCR
            </span>
            <span className="flex items-center gap-1 rounded-md bg-white/[0.04] px-2 py-1">
              <FileAudio className="h-3 w-3 text-emerald-300" />
              Whisper
            </span>
          </div>
        </>
      )}
    </div>
  );
}
