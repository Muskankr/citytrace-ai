"use client";

import {
  useEffect,
  useRef,
  useState,
} from "react";

import {
  getCameras,
  getProcessingStatus,
} from "@/lib/api";


// ============================================================
// TYPES
// ============================================================

interface Camera {
  id: number;
  camera_id: string;
  name: string;
  road_name: string;
  direction: string;
  latitude: number;
  longitude: number;
  is_active: boolean;
}

interface UploadResponse {
  message: string;
  job_id: string;
  camera_code: string;
  filename: string;
  saved_path: string;
  status: string;
}

interface ProcessingJob {
  job_id: string;
  camera_code: string;
  filename: string;
  status: string;
  message: string;
  progress: number;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  error: string | null;
}


// ============================================================
// PIPELINE STAGES
// ============================================================

const stages = [
  "Video Ingestion",
  "Vehicle Detection",
  "Vehicle Tracking",
  "License Plate Detection",
  "OCR & Validation",
  "Database Logging",
  "Trajectory Analysis",
  "Traffic Analytics",
  "Alert Intelligence",
];


// ============================================================
// PAGE
// ============================================================

export default function VideoPage() {

  const [cameras, setCameras] =
    useState<Camera[]>([]);

  const [selectedCamera, setSelectedCamera] =
    useState("");

  const [selectedFile, setSelectedFile] =
    useState<File | null>(null);

  const [uploading, setUploading] =
    useState(false);

  const [result, setResult] =
    useState<UploadResponse | null>(null);

  const [job, setJob] =
    useState<ProcessingJob | null>(null);

  const [error, setError] =
    useState("");

  const [loadingCameras, setLoadingCameras] =
    useState(true);

  const pollingRef =
    useRef<ReturnType<typeof setInterval> | null>(
      null
    );


  // ==========================================================
  // LOAD CAMERAS
  // ==========================================================

  useEffect(() => {

    async function loadCameras() {

      try {

        const data =
          await getCameras();

        setCameras(data);

        if (
          data.length > 0 &&
          !selectedCamera
        ) {
          setSelectedCamera(
            data[0].camera_id
          );
        }

      } catch (error) {

        console.error(
          "Camera API Error:",
          error
        );

        setError(
          "Unable to load cameras."
        );

      } finally {

        setLoadingCameras(false);

      }

    }

    loadCameras();

  }, [selectedCamera]);


  // ==========================================================
  // CLEANUP POLLING
  // ==========================================================

  useEffect(() => {

    return () => {

      if (pollingRef.current) {

        clearInterval(
          pollingRef.current
        );

        pollingRef.current = null;

      }

    };

  }, []);


  // ==========================================================
  // STOP POLLING
  // ==========================================================

  function stopPolling() {

    if (pollingRef.current) {

      clearInterval(
        pollingRef.current
      );

      pollingRef.current = null;

    }

  }


  // ==========================================================
  // CHECK PROCESSING STATUS
  // ==========================================================

  async function checkProcessingStatus(
    jobId: string
  ) {

    try {

      const data =
        await getProcessingStatus(
          jobId
        );

      setJob(data);


      // Stop polling when finished
      if (
        data.status === "completed" ||
        data.status === "failed"
      ) {

        stopPolling();

      }

    } catch (error) {

      console.error(
        "Processing Status Error:",
        error
      );

    }

  }


  // ==========================================================
  // FILE SELECTION
  // ==========================================================

  function handleFileChange(
    event: React.ChangeEvent<HTMLInputElement>
  ) {

    const file =
      event.target.files?.[0];

    setError("");
    setResult(null);
    setJob(null);

    stopPolling();

    if (!file) {

      setSelectedFile(null);

      return;

    }


    const extension =
      file.name
        .split(".")
        .pop()
        ?.toLowerCase();


    const allowedExtensions = [
      "mp4",
      "avi",
      "mov",
      "mkv",
    ];


    if (
      !allowedExtensions.includes(
        extension || ""
      )
    ) {

      setError(
        "Please select an MP4, AVI, MOV or MKV video."
      );

      setSelectedFile(null);

      return;

    }


    setSelectedFile(file);

  }


  // ==========================================================
  // UPLOAD VIDEO
  // ==========================================================

  async function handleUpload() {

    if (!selectedCamera) {

      setError(
        "Please select a camera."
      );

      return;

    }


    if (!selectedFile) {

      setError(
        "Please select a video file."
      );

      return;

    }


    setUploading(true);
    setError("");
    setResult(null);
    setJob(null);

    stopPolling();


    try {

      const formData =
        new FormData();


      formData.append(
        "camera_code",
        selectedCamera
      );


      formData.append(
        "video",
        selectedFile
      );


      const apiUrl =
        process.env.NEXT_PUBLIC_API_URL ||
        "http://127.0.0.1:8000";


      const response =
        await fetch(
          `${apiUrl}/video/upload`,
          {
            method: "POST",
            body: formData,
          }
        );


      const data =
        await response.json();


      if (!response.ok) {

        throw new Error(
          data.detail ||
            "Video upload failed."
        );

      }


      setResult(data);

      setSelectedFile(null);


      const fileInput =
        document.getElementById(
          "video-file"
        ) as HTMLInputElement | null;


      if (fileInput) {

        fileInput.value = "";

      }


      // ======================================================
      // START STATUS MONITORING
      // ======================================================

      if (data.job_id) {

        // Get status immediately
        await checkProcessingStatus(
          data.job_id
        );


        // Then poll every 2 seconds
        pollingRef.current =
          setInterval(() => {

            checkProcessingStatus(
              data.job_id
            );

          }, 2000);

      }

    } catch (error) {

      console.error(
        "Video Upload Error:",
        error
      );


      setError(
        error instanceof Error
          ? error.message
          : "Video upload failed."
      );

    } finally {

      setUploading(false);

    }

  }


  // ==========================================================
  // STATUS COLOR
  // ==========================================================

  function getStatusColor(
    status: string
  ) {

    switch (status) {

      case "completed":
        return "bg-green-100 text-green-700";

      case "failed":
        return "bg-red-100 text-red-700";

      case "processing":
        return "bg-blue-100 text-blue-700";

      case "queued":
        return "bg-yellow-100 text-yellow-700";

      default:
        return "bg-gray-100 text-gray-700";

    }

  }


  // ==========================================================
  // STAGE STATUS
  // ==========================================================
  //
  // IMPORTANT:
  // Current backend only reports:
  // 5%  -> pipeline started
  // 10% -> AI models / processing
  // 100% -> completed
  //
  // Therefore this UI intentionally does NOT claim that
  // individual backend stages are independently tracked yet.
  // ==========================================================

  function getStageStatus(
    index: number
  ) {

    if (!job) {
      return "waiting";
    }


    if (job.status === "failed") {

      return "waiting";

    }


    if (job.status === "completed") {

      return "completed";

    }


    if (
      job.status === "queued"
    ) {

      if (index === 0) {
        return "processing";
      }

      return "waiting";

    }


    if (
      job.status === "processing"
    ) {

      // Current backend has not yet exposed
      // individual stage callbacks.
      if (index === 0) {
        return "completed";
      }

      if (index === 1) {
        return "processing";
      }

      return "waiting";

    }


    return "waiting";

  }


  // ==========================================================
  // STAGE UI
  // ==========================================================

  function getStageClasses(
    status: string
  ) {

    if (status === "completed") {

      return {
        container:
          "border-green-200 bg-green-50",
        circle:
          "bg-green-100 text-green-700",
        text:
          "text-green-800",
        sub:
          "text-green-600",
      };

    }


    if (status === "processing") {

      return {
        container:
          "border-blue-200 bg-blue-50",
        circle:
          "bg-blue-100 text-blue-700",
        text:
          "text-blue-800",
        sub:
          "text-blue-600",
      };

    }


    return {
      container:
        "border-gray-200 bg-gray-50",
      circle:
        "bg-gray-200 text-gray-500",
      text:
        "text-gray-700",
      sub:
        "text-gray-500",
    };

  }


  // ==========================================================
  // RENDER
  // ==========================================================

  return (

    <main className="min-h-screen bg-gray-50 p-6 md:p-8">


      {/* =====================================================
          HEADER
      ===================================================== */}

      <div className="mb-8">

        <p className="text-sm font-medium uppercase tracking-wider text-blue-600">
          AI Video Processing
        </p>


        <h1 className="mt-1 text-3xl font-bold text-gray-900">
          Video Processing Center
        </h1>


        <p className="mt-2 max-w-3xl text-gray-600">
          Upload traffic camera footage and
          start the CityAI multi-stage
          detection, tracking, ANPR and
          analytics pipeline.
        </p>

      </div>


      {/* =====================================================
          MAIN GRID
      ===================================================== */}

      <div className="grid gap-6 lg:grid-cols-3">


        {/* ===================================================
            UPLOAD CARD
        =================================================== */}

        <div className="lg:col-span-2">

          <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">


            <div className="mb-6">

              <h2 className="text-xl font-semibold text-gray-900">
                Upload Traffic Video
              </h2>

              <p className="mt-1 text-sm text-gray-500">
                Select the camera source and
                upload its traffic footage.
              </p>

            </div>


            {/* CAMERA */}

            <div className="mb-6">

              <label className="mb-2 block text-sm font-medium text-gray-700">
                Camera Source
              </label>


              {loadingCameras ? (

                <div className="rounded-lg border border-gray-200 bg-gray-50 px-4 py-3 text-sm text-gray-500">
                  Loading cameras...
                </div>

              ) : (

                <select
                  value={selectedCamera}
                  onChange={(e) =>
                    setSelectedCamera(
                      e.target.value
                    )
                  }
                  className="w-full rounded-lg border border-gray-300 bg-white px-4 py-3 text-gray-900 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
                >

                  <option value="">
                    Select Camera
                  </option>


                  {cameras.map(
                    (camera) => (

                      <option
                        key={
                          camera.camera_id
                        }
                        value={
                          camera.camera_id
                        }
                      >
                        {camera.camera_id} —{" "}
                        {camera.name}
                      </option>

                    )
                  )}

                </select>

              )}

            </div>


            {/* VIDEO FILE */}

            <div>

              <label className="mb-2 block text-sm font-medium text-gray-700">
                Traffic Video
              </label>


              <label
                htmlFor="video-file"
                className="flex min-h-52 cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed border-gray-300 bg-gray-50 px-6 py-10 text-center transition hover:border-blue-400 hover:bg-blue-50"
              >

                <div className="text-5xl">
                  🎥
                </div>


                <p className="mt-4 text-base font-semibold text-gray-800">
                  Click to select traffic video
                </p>


                <p className="mt-2 text-sm text-gray-500">
                  MP4, AVI, MOV or MKV
                </p>


                {selectedFile && (

                  <div className="mt-4 rounded-lg bg-white px-4 py-2 shadow-sm">

                    <p className="text-sm font-medium text-blue-600">
                      {selectedFile.name}
                    </p>


                    <p className="mt-1 text-xs text-gray-500">
                      {(
                        selectedFile.size /
                        (1024 * 1024)
                      ).toFixed(2)}{" "}
                      MB
                    </p>

                  </div>

                )}

              </label>


              <input
                id="video-file"
                type="file"
                accept=".mp4,.avi,.mov,.mkv,video/*"
                onChange={
                  handleFileChange
                }
                className="hidden"
              />

            </div>


            {/* ERROR */}

            {error && (

              <div className="mt-5 rounded-lg border border-red-200 bg-red-50 p-4">

                <p className="text-sm font-medium text-red-700">
                  {error}
                </p>

              </div>

            )}


            {/* UPLOAD BUTTON */}

            <button
              onClick={handleUpload}
              disabled={
                uploading ||
                !selectedFile ||
                !selectedCamera
              }
              className="mt-6 w-full rounded-lg bg-blue-600 px-5 py-3.5 text-sm font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-gray-300"
            >

              {uploading
                ? "Uploading & Starting AI Pipeline..."
                : "Start AI Video Processing"}

            </button>

          </div>

        </div>


        {/* ===================================================
            PIPELINE CARD
        =================================================== */}

        <div>

          <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">

            <h2 className="text-xl font-semibold text-gray-900">
              AI Pipeline
            </h2>

            <p className="mt-1 text-sm text-gray-500">
              Processing stages
            </p>


            <div className="mt-6 space-y-4">

              {stages.map(
                (stage, index) => (

                  <div
                    key={stage}
                    className="flex items-center gap-3"
                  >

                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-blue-100 text-sm font-bold text-blue-600">
                      {index + 1}
                    </div>


                    <div className="text-sm font-medium text-gray-700">
                      {stage}
                    </div>

                  </div>

                )
              )}

            </div>

          </div>

        </div>

      </div>


      {/* =====================================================
          UPLOAD SUCCESS
      ===================================================== */}

      {result && (

        <div className="mt-6 rounded-xl border border-green-200 bg-green-50 p-6">

          <div className="flex items-start gap-4">

            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-green-100 text-xl text-green-600">
              ✓
            </div>


            <div className="min-w-0">

              <h2 className="font-semibold text-green-800">
                AI Processing Started
              </h2>


              <p className="mt-1 text-sm text-green-700">
                Your traffic video has been
                uploaded successfully and
                the AI pipeline is processing
                it in the background.
              </p>

            </div>

          </div>


          <div className="mt-5 grid gap-4 sm:grid-cols-3">


            <div className="rounded-lg border border-green-200 bg-white p-4">

              <p className="text-xs text-gray-400">
                Camera
              </p>

              <p className="mt-1 font-semibold text-gray-900">
                {result.camera_code}
              </p>

            </div>


            <div className="rounded-lg border border-green-200 bg-white p-4">

              <p className="text-xs text-gray-400">
                Video
              </p>

              <p className="mt-1 break-all font-medium text-gray-900">
                {result.filename}
              </p>

            </div>


            <div className="rounded-lg border border-green-200 bg-white p-4">

              <p className="text-xs text-gray-400">
                Job ID
              </p>

              <p className="mt-1 break-all font-mono text-xs text-gray-700">
                {result.job_id}
              </p>

            </div>

          </div>

        </div>

      )}


      {/* =====================================================
          LIVE PROCESSING STATUS
      ===================================================== */}

      {job && (

        <div className="mt-6 rounded-xl border border-gray-200 bg-white p-6 shadow-sm">


          {/* STATUS HEADER */}

          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">

            <div>

              <p className="text-xs font-medium uppercase tracking-wider text-blue-600">
                Live Processing
              </p>

              <h2 className="mt-1 text-xl font-semibold text-gray-900">
                AI Pipeline Status
              </h2>

            </div>


            <span
              className={`rounded-full px-4 py-2 text-xs font-bold ${getStatusColor(
                job.status
              )}`}
            >
              {job.status.toUpperCase()}
            </span>

          </div>


          {/* =================================================
              PROGRESS
          ================================================= */}

          <div className="mt-7">

            <div className="mb-2 flex items-center justify-between">

              <span className="text-sm font-medium text-gray-700">
                Overall Progress
              </span>


              <span className="text-sm font-bold text-gray-900">
                {job.progress}%
              </span>

            </div>


            <div className="h-3 overflow-hidden rounded-full bg-gray-200">

              <div
                className={`h-full rounded-full transition-all duration-700 ${
                  job.status === "failed"
                    ? "bg-red-500"
                    : job.status === "completed"
                    ? "bg-green-500"
                    : "bg-blue-600"
                }`}
                style={{
                  width: `${job.progress}%`,
                }}
              />

            </div>

          </div>


          {/* MESSAGE */}

          <div className="mt-5 rounded-lg bg-gray-50 p-4">

            <p className="text-sm text-gray-700">
              {job.message}
            </p>

          </div>


          {/* =================================================
              PIPELINE STAGES
          ================================================= */}

          <div className="mt-7">

            <div className="mb-4 flex items-center justify-between">

              <h3 className="text-sm font-semibold text-gray-900">
                Processing Pipeline
              </h3>

              {job.status === "processing" && (
                <span className="text-xs text-blue-600">
                  AI engine running
                </span>
              )}

            </div>


            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">

              {stages.map(
                (stage, index) => {

                  const status =
                    getStageStatus(
                      index
                    );

                  const styles =
                    getStageClasses(
                      status
                    );


                  return (

                    <div
                      key={stage}
                      className={`rounded-lg border p-4 ${styles.container}`}
                    >

                      <div className="flex items-center gap-3">


                        <div
                          className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-xs font-bold ${styles.circle}`}
                        >

                          {status ===
                          "completed"
                            ? "✓"
                            : status ===
                              "processing"
                            ? "..."
                            : index + 1}

                        </div>


                        <div>

                          <p
                            className={`text-sm font-medium ${styles.text}`}
                          >
                            {stage}
                          </p>


                          <p
                            className={`mt-0.5 text-xs ${styles.sub}`}
                          >

                            {status ===
                            "completed"
                              ? "Completed"
                              : status ===
                                "processing"
                              ? "Processing"
                              : "Waiting"}

                          </p>

                        </div>

                      </div>

                    </div>

                  );

                }
              )}

            </div>

          </div>


          {/* =================================================
              JOB INFORMATION
          ================================================= */}

          <div className="mt-7 grid gap-4 sm:grid-cols-3">


            <div className="rounded-lg border border-gray-200 p-4">

              <p className="text-xs text-gray-400">
                Camera
              </p>

              <p className="mt-1 font-semibold text-gray-900">
                {job.camera_code}
              </p>

            </div>


            <div className="rounded-lg border border-gray-200 p-4">

              <p className="text-xs text-gray-400">
                Video
              </p>

              <p className="mt-1 break-all text-sm font-medium text-gray-900">
                {job.filename}
              </p>

            </div>


            <div className="rounded-lg border border-gray-200 p-4">

              <p className="text-xs text-gray-400">
                Job ID
              </p>

              <p className="mt-1 break-all font-mono text-xs text-gray-700">
                {job.job_id}
              </p>

            </div>

          </div>


          {/* =================================================
              ERROR
          ================================================= */}

          {job.error && (

            <div className="mt-5 rounded-lg border border-red-200 bg-red-50 p-4">

              <p className="text-sm font-semibold text-red-700">
                Processing Error
              </p>


              <p className="mt-1 break-words text-sm text-red-600">
                {job.error}
              </p>

            </div>

          )}


          {/* =================================================
              COMPLETED
          ================================================= */}

          {job.status === "completed" && (

            <div className="mt-5 rounded-lg border border-green-200 bg-green-50 p-4">

              <div className="flex items-start gap-3">

                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-green-100 text-green-700">
                  ✓
                </div>


                <div>

                  <p className="text-sm font-semibold text-green-700">
                    AI Processing Completed
                  </p>


                  <p className="mt-1 text-sm text-green-600">
                    The traffic video has finished
                    processing successfully.
                    Detection results have been
                    processed by the CityAI engine.
                  </p>

                </div>

              </div>

            </div>

          )}


          {/* =================================================
              FAILED
          ================================================= */}

          {job.status === "failed" && (

            <div className="mt-5 rounded-lg border border-red-200 bg-red-50 p-4">

              <div className="flex items-start gap-3">

                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-red-100 text-red-700">
                  !
                </div>


                <div>

                  <p className="text-sm font-semibold text-red-700">
                    AI Processing Failed
                  </p>


                  <p className="mt-1 text-sm text-red-600">
                    The backend encountered an
                    error while processing this
                    video. Check the backend
                    terminal for detailed logs.
                  </p>

                </div>

              </div>

            </div>

          )}

        </div>

      )}

    </main>

  );

}