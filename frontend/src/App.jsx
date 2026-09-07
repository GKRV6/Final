import { useEffect, useRef, useState } from "react";
import "./App.css";

const API_BASE_URL = "http://127.0.0.1:8000";
const CONFIDENCE_THRESHOLD = 70;

function App() {
  const [image, setImage] = useState(null);
  const [preview, setPreview] = useState(null);
  const [result, setResult] = useState(null);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const [scanStage, setScanStage] = useState("READY");
  const [scanProgress, setScanProgress] = useState(0);

  const [history, setHistory] = useState(() => {
    try {
      return (
        JSON.parse(
          localStorage.getItem("wafer_prediction_history")
        ) || []
      );
    } catch {
      return [];
    }
  });

  const fileInputRef = useRef(null);
  const stageTimerRef = useRef(null);

  // =====================================================
  // HERO BACKGROUND CURSOR EFFECT
  // =====================================================

  const heroRef = useRef(null);

  const handleHeroMouseMove = (event) => {
    if (!heroRef.current) return;

    const rect = heroRef.current.getBoundingClientRect();

    const x = ((event.clientX - rect.left) / rect.width) * 100;
    const y = ((event.clientY - rect.top) / rect.height) * 100;

    heroRef.current.style.setProperty(
      "--mouse-x",
      `${x}%`
    );

    heroRef.current.style.setProperty(
      "--mouse-y",
      `${y}%`
    );
  };

  /* =====================================================
     CLEANUP
  ===================================================== */

  useEffect(() => {
    return () => {
      if (preview) {
        URL.revokeObjectURL(preview);
      }

      if (stageTimerRef.current) {
        clearInterval(stageTimerRef.current);
      }
    };
  }, [preview]);

  /* =====================================================
     IMAGE SELECT
  ===================================================== */

  const handleImageChange = (event) => {
    const file = event.target.files[0];

    if (!file) return;

    if (!file.type.startsWith("image/")) {
      setError("Please select a valid image file.");
      return;
    }

    if (preview) {
      URL.revokeObjectURL(preview);
    }

    const newPreview = URL.createObjectURL(file);

    setImage(file);
    setPreview(newPreview);
    setResult(null);
    setError(null);
    setScanStage("READY");
    setScanProgress(0);
  };

  /* =====================================================
     REMOVE IMAGE
  ===================================================== */

  const handleRemoveImage = () => {
    if (preview) {
      URL.revokeObjectURL(preview);
    }

    setImage(null);
    setPreview(null);
    setResult(null);
    setError(null);
    setScanStage("READY");
    setScanProgress(0);

    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  /* =====================================================
     CHANGE IMAGE
  ===================================================== */

  const handleChangeImage = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  /* =====================================================
     SCAN ANIMATION
  ===================================================== */

  const startScanAnimation = () => {
    if (stageTimerRef.current) {
      clearInterval(stageTimerRef.current);
    }

    const stages = [
      "INITIALIZING AI CORE",
      "READING WAFER MAP",
      "PREPROCESSING IMAGE",
      "EXTRACTING FEATURES",
      "RUNNING RESNET50",
      "GENERATING GRAD-CAM",
      "FINALIZING INSPECTION",
    ];

    let progress = 0;

    setScanStage(stages[0]);
    setScanProgress(3);

    stageTimerRef.current = setInterval(() => {
      progress += 5;

      if (progress >= 100) {
        progress = 100;
      }

      setScanProgress(progress);

      const stageIndex = Math.min(
        Math.floor(progress / 15),
        stages.length - 1
      );

      setScanStage(stages[stageIndex]);

      if (progress >= 100) {
        clearInterval(stageTimerRef.current);
      }
    }, 180);
  };

  /* =====================================================
     PIPELINE STATUS
  ===================================================== */

  const getPipelineStatus = (step) => {
    if (!loading && !result) {
      return "pending";
    }

    const progress = scanProgress;

    if (step === 1) {
      return "complete";
    }

    if (step === 2) {
      return progress >= 15 ? "complete" : "active";
    }

    if (step === 3) {
      if (progress >= 35) return "complete";
      if (progress >= 20) return "active";
      return "pending";
    }

    if (step === 4) {
      if (progress >= 55) return "complete";
      if (progress >= 38) return "active";
      return "pending";
    }

    if (step === 5) {
      if (progress >= 72) return "complete";
      if (progress >= 55) return "active";
      return "pending";
    }

    if (step === 6) {
      if (progress >= 90) return "complete";
      if (progress >= 72) return "active";
      return "pending";
    }

    return "pending";
  };

  /* =====================================================
     ANALYZE IMAGE
  ===================================================== */

  const handleAnalyze = async () => {
    if (!image || loading) return;

    setLoading(true);
    setError(null);
    setResult(null);

    startScanAnimation();

    try {
      const formData = new FormData();

      formData.append("file", image);

      const response = await fetch(
        `${API_BASE_URL}/predict`,
        {
          method: "POST",
          body: formData,
        }
      );

      if (!response.ok) {
        let message = `Backend error: ${response.status}`;

        try {
          const errorData = await response.json();

          if (errorData.detail) {
            message = errorData.detail;
          }
        } catch {
          // Keep default error
        }

        throw new Error(message);
      }

      const data = await response.json();

      console.log("AI Backend Response:", data);

      if (stageTimerRef.current) {
        clearInterval(stageTimerRef.current);
      }

      setScanProgress(100);
      setScanStage("INSPECTION COMPLETE");

      setResult(data);

      /* =================================================
         SAVE HISTORY
      ================================================= */

      const historyItem = {
        id: Date.now(),
        wafer_id: data.wafer_id || image.name,
        defect: data.defect || "Unknown",
        confidence: Number(data.confidence) || 0,
        confidence_status: data.confidence_status || "",
        location:
          data.location || "Not clearly localized",
        affected_area:
          Number(data.affected_area) || 0,
        timestamp:
          data.timestamp || new Date().toLocaleString(),
        ensemble_breakdown: data.ensemble_breakdown || null,
        severity: data.severity || null,
      };

      setHistory((previousHistory) => {
        const updatedHistory = [
          historyItem,
          ...previousHistory,
        ].slice(0, 20);

        localStorage.setItem(
          "wafer_prediction_history",
          JSON.stringify(updatedHistory)
        );

        return updatedHistory;
      });
    } catch (err) {
      console.error("Prediction error:", err);

      if (stageTimerRef.current) {
        clearInterval(stageTimerRef.current);
      }

      setScanStage("ANALYSIS FAILED");

      setError(
        err.message ||
        "Unable to connect to the AI backend."
      );
    } finally {
      setLoading(false);
    }
  };

  /* =====================================================
     CLEAR HISTORY
  ===================================================== */

  const handleClearHistory = () => {
    setHistory([]);

    localStorage.removeItem(
      "wafer_prediction_history"
    );
  };

  /* =====================================================
     STATISTICS
  ===================================================== */

  const totalInspections = history.length;

  const averageConfidence =
    history.length > 0
      ? (
        history.reduce(
          (sum, item) =>
            sum + Number(item.confidence || 0),
          0
        ) / history.length
      ).toFixed(1)
      : "0.0";

  const highConfidenceCount =
    history.filter(
      (item) =>
        Number(item.confidence || 0) >=
        CONFIDENCE_THRESHOLD
    ).length;

  const lowConfidenceCount =
    history.filter(
      (item) =>
        Number(item.confidence || 0) <
        CONFIDENCE_THRESHOLD
    ).length;

  /* =====================================================
     UI
  ===================================================== */

  return (
    <div className="app">

      {/* =================================================
          HEADER
      ================================================= */}

      <header className="header">

        <div className="logo">

          <span className="logo-icon">
            ◉
          </span>

          <div>
            <div>SemiVision</div>

            <small
              style={{
                color: "#5c7182",
                fontSize: "8px",
                letterSpacing: "2px",
              }}
            >
              WAFER INTELLIGENCE
            </small>
          </div>

        </div>

        <div className="header-status">

          <span className="status-dot"></span>

          SYSTEM ONLINE

        </div>

      </header>


      {/* =================================================
          MAIN
      ================================================= */}

      <main className="main-container">


        {/* =================================================
            HERO
        ================================================= */}

        <section
          ref={heroRef}
          className="hero"
          onMouseMove={handleHeroMouseMove}
        >

          <p className="eyebrow">
            AI SEMICONDUCTOR INSPECTION
          </p>

          <h1>
            Wafer
            <span> Intelligence</span>
          </h1>

          <p className="hero-text">
            Intelligent wafer inspection powered by
            deep learning, explainable AI and automated
            defect analysis.
          </p>

          <div
            style={{
              display: "flex",
              justifyContent: "center",
              gap: "10px",
              flexWrap: "wrap",
              marginTop: "22px",
            }}
          >

            <span className="model-badge">
              DEEP LEARNING
            </span>

            <span className="model-badge">
              EXPLAINABLE AI
            </span>

            <span className="model-badge">
              INDUSTRIAL VISION
            </span>

          </div>

        </section>


        {/* =================================================
            SYSTEM OVERVIEW
        ================================================= */}

        <section
          style={{
            display: "grid",
            gridTemplateColumns:
              "repeat(4, 1fr)",
            gap: "12px",
            marginBottom: "22px",
          }}
        >

          <div className="info-card">

            <div className="info-icon">
              AI
            </div>

            <div>
              <h3>AI ENGINE</h3>
              <p>Triple Ensemble (ResNet50 + EfficientNet-B2 + ResNet18)</p>
            </div>

          </div>


          <div className="info-card">

            <div className="info-icon">
              GPU
            </div>

            <div>
              <h3>ACCELERATION</h3>
              <p>CUDA Enabled</p>
            </div>

          </div>


          <div className="info-card">

            <div className="info-icon">
              8
            </div>

            <div>
              <h3>DEFECT CLASSES</h3>
              <p>AI Classification</p>
            </div>

          </div>


          <div className="info-card">

            <div className="info-icon">
              89
            </div>

            <div>
              <h3>TEST ACCURACY</h3>
              <p>88.95%</p>
            </div>

          </div>

        </section>


        {/* =================================================
            AI TELEMETRY
        ================================================= */}

        <section
          className="upload-card"
          style={{
            marginBottom: "25px",
          }}
        >

          <div className="card-header">

            <div>

              <h2>
                AI System Telemetry
              </h2>

              <p>
                Live inspection engine status
              </p>

            </div>

            <div className="model-badge">
              LIVE
            </div>

          </div>


          <div
            style={{
              display: "grid",
              gridTemplateColumns:
                "repeat(4, 1fr)",
              gap: "12px",
            }}
          >

            <div className="info-card">

              <div className="info-icon">
                ●
              </div>

              <div>

                <h3>AI CORE</h3>

                <p>
                  {loading
                    ? "PROCESSING"
                    : "STANDBY"}
                </p>

              </div>

            </div>


            <div className="info-card">

              <div className="info-icon">
                224
              </div>

              <div>

                <h3>INPUT SIZE</h3>

                <p>
                  224 × 224
                </p>

              </div>

            </div>


            <div className="info-card">

              <div className="info-icon">
                3
              </div>

              <div>

                <h3>CHANNELS</h3>

                <p>
                  RGB Tensor
                </p>

              </div>

            </div>


            <div className="info-card">

              <div className="info-icon">
                XAI
              </div>

              <div>

                <h3>EXPLANATION</h3>

                <p>
                  Grad-CAM
                </p>

              </div>

            </div>

          </div>

        </section>


        {/* =================================================
            INSPECTION CONSOLE
        ================================================= */}

        <section className="upload-card">

          <div className="card-header">

            <div>

              <h2>
                AI Inspection Console
              </h2>

              <p>
                Upload a wafer map for automated
                semiconductor defect analysis.
              </p>

            </div>

            <div className="model-badge">
              RESNET50 • CUDA
            </div>

          </div>


          {/* =================================================
              UPLOAD AREA
          ================================================= */}

          <label className="upload-area">

            {preview ? (

              <div
                className="preview-container"
                style={{
                  position: "relative",
                  width: "100%",
                  height: "100%",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                }}
              >

                <img
                  src={preview}
                  alt="Wafer preview"
                  className="image-preview"
                />


                {/* SCANNING LINE */}

                {loading && (

                  <div
                    style={{
                      position: "absolute",
                      left: "12%",
                      right: "12%",
                      height: "2px",
                      background:
                        "linear-gradient(90deg, transparent, #00f0ff, transparent)",
                      boxShadow:
                        "0 0 22px #00eaff",
                      animation:
                        "waferScanner 2s linear infinite",
                      pointerEvents: "none",
                    }}
                  />

                )}


                {/* SCAN CORNERS */}

                {loading && (
                  <>
                    <div
                      style={{
                        position: "absolute",
                        top: "12%",
                        left: "12%",
                        width: "30px",
                        height: "30px",
                        borderTop:
                          "2px solid #00e5ff",
                        borderLeft:
                          "2px solid #00e5ff",
                      }}
                    />

                    <div
                      style={{
                        position: "absolute",
                        top: "12%",
                        right: "12%",
                        width: "30px",
                        height: "30px",
                        borderTop:
                          "2px solid #00e5ff",
                        borderRight:
                          "2px solid #00e5ff",
                      }}
                    />

                    <div
                      style={{
                        position: "absolute",
                        bottom: "12%",
                        left: "12%",
                        width: "30px",
                        height: "30px",
                        borderBottom:
                          "2px solid #00e5ff",
                        borderLeft:
                          "2px solid #00e5ff",
                      }}
                    />

                    <div
                      style={{
                        position: "absolute",
                        bottom: "12%",
                        right: "12%",
                        width: "30px",
                        height: "30px",
                        borderBottom:
                          "2px solid #00e5ff",
                        borderRight:
                          "2px solid #00e5ff",
                      }}
                    />
                  </>
                )}


                <div
                  style={{
                    position: "absolute",
                    bottom: "20px",
                    left: "50%",
                    transform:
                      "translateX(-50%)",
                    padding: "8px 14px",
                    border:
                      "1px solid rgba(0,229,255,.3)",
                    borderRadius: "999px",
                    background:
                      "rgba(2,10,17,.78)",
                    backdropFilter:
                      "blur(8px)",
                    color: "#00e5ff",
                    fontFamily:
                      "Space Mono, monospace",
                    fontSize: "9px",
                    letterSpacing: "1px",
                    whiteSpace: "nowrap",
                  }}
                >
                  {loading
                    ? scanStage
                    : "WAFER IMAGE READY"}
                </div>

              </div>

            ) : (

              <>

                <div className="upload-icon">
                  ◉
                </div>

                <h3>
                  Load Wafer Map
                </h3>

                <p>
                  Click to initialize AI inspection
                </p>

                <span>
                  PNG • JPG • JPEG
                </span>

              </>

            )}

            <input
              ref={fileInputRef}
              type="file"
              accept="image/png,image/jpeg,image/jpg"
              onChange={handleImageChange}
              hidden
            />

          </label>


          {/* =================================================
              SELECTED FILE
          ================================================= */}

          {image && (

            <div className="selected-file">

              <div className="file-name">

                <span className="file-check">
                  ✓
                </span>

                <div>

                  <small>
                    WAFER LOADED
                  </small>

                  <strong>
                    {image.name}
                  </strong>

                </div>

              </div>


              <div className="file-actions">

                <button
                  type="button"
                  className="change-button"
                  onClick={handleChangeImage}
                  disabled={loading}
                >
                  CHANGE
                </button>

                <button
                  type="button"
                  className="remove-button"
                  onClick={handleRemoveImage}
                  disabled={loading}
                >
                  REMOVE
                </button>

              </div>

            </div>

          )}


          {/* =================================================
              AI INSPECTION PIPELINE
          ================================================= */}

          {(loading || result) && (

            <div className="inspection-pipeline">

              <div className="pipeline-title">
                AI INSPECTION PIPELINE
              </div>

              <div className="pipeline-subtitle">
                REAL-TIME INFERENCE & EXPLAINABILITY
              </div>


              <div className="pipeline">

                {[
                  ["01", "IMAGE RECEIVED"],
                  ["02", "PREPROCESSING"],
                  ["03", "FEATURE EXTRACTION"],
                  ["04", "RESNET50 CLASSIFICATION"],
                  ["05", "GRAD-CAM EXPLANATION"],
                  ["06", "INSPECTION COMPLETE"],
                ].map(
                  ([number, label], index) => {

                    const status =
                      getPipelineStatus(
                        index + 1
                      );

                    return (

                      <div
                        className={`pipeline-step ${status}`}
                        key={number}
                      >

                        <div className="pipeline-node">

                          {status === "complete"
                            ? "✓"
                            : status === "active"
                              ? "●"
                              : number}

                        </div>

                        <div className="pipeline-step-content">

                          <span>
                            STEP {number}
                          </span>

                          <strong>
                            {label}
                          </strong>

                        </div>

                        {index < 5 && (
                          <div className="pipeline-connector"></div>
                        )}

                      </div>

                    );
                  }
                )}

              </div>

            </div>

          )}


          {/* =================================================
              PROGRESS
          ================================================= */}

          {loading && (

            <div
              style={{
                marginTop: "16px",
                padding: "18px",
                border:
                  "1px solid rgba(0,229,255,.14)",
                borderRadius: "12px",
                background:
                  "rgba(0,229,255,.025)",
              }}
            >

              <div
                style={{
                  display: "flex",
                  justifyContent:
                    "space-between",
                  marginBottom: "10px",
                  fontFamily:
                    "Space Mono, monospace",
                  fontSize: "10px",
                  color: "#00e5ff",
                }}
              >

                <span>
                  {scanStage}
                </span>

                <span>
                  {scanProgress}%
                </span>

              </div>


              <div
                style={{
                  height: "4px",
                  background:
                    "rgba(0,229,255,.08)",
                  borderRadius: "10px",
                  overflow: "hidden",
                }}
              >

                <div
                  style={{
                    width: `${scanProgress}%`,
                    height: "100%",
                    background:
                      "linear-gradient(90deg,#00d9ff,#00ffd5)",
                    boxShadow:
                      "0 0 15px rgba(0,229,255,.7)",
                    transition:
                      "width .2s ease",
                  }}
                />

              </div>

            </div>

          )}


          {/* =================================================
              ANALYZE BUTTON
          ================================================= */}

          <button
            className="analyze-button"
            onClick={handleAnalyze}
            disabled={!image || loading}
          >

            {loading ? (

              <>
                <span className="loading-spinner"></span>
                AI INSPECTION IN PROGRESS...
              </>

            ) : (

              <>
                START AI INSPECTION

                <span className="button-arrow">
                  →
                </span>
              </>

            )}

          </button>


          {/* =================================================
              ERROR
          ================================================= */}

          {error && (

            <div className="error-message">

              <span>
                ⚠
              </span>

              <div>

                {error}

                <div
                  style={{
                    marginTop: "6px",
                    fontSize: "10px",
                    opacity: 0.7,
                  }}
                >
                  Make sure the FastAPI backend is
                  running on port 8000.
                </div>

              </div>

            </div>

          )}

        </section>


        {/* =================================================
            INSPECTION RESULT
        ================================================= */}

        {result && (

          <section
            className="upload-card result-card"
            style={{
              marginTop: "25px",
            }}
          >

            <div className="card-header">

              <div>

                <h2>
                  Inspection Complete
                </h2>

                <p>
                  AI classification and explainability results
                </p>

              </div>

              <div className="model-badge">
                ✓ VERIFIED
              </div>

            </div>


            {/* =================================================
                DETECTED DEFECT
            ================================================= */}

            <div
              style={{
                textAlign: "center",
                marginBottom: "35px",
              }}
            >

              <div
                style={{
                  fontFamily:
                    "Space Mono, monospace",
                  fontSize: "10px",
                  color: "#00e5ff",
                  letterSpacing: "2px",
                  marginBottom: "12px",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  gap: "8px",
                  flexWrap: "wrap",
                }}
              >
                <span>DETECTED DEFECT</span>
                <span
                  style={{
                    padding: "3px 10px",
                    borderRadius: "999px",
                    background: "rgba(0, 229, 255, 0.12)",
                    border: "1px solid rgba(0, 229, 255, 0.45)",
                    color: "#00ffd5",
                    fontSize: "9px",
                    letterSpacing: "1.5px",
                    fontWeight: "700",
                    boxShadow: "0 0 10px rgba(0, 229, 255, 0.2)",
                  }}
                >
                  FINAL ENSEMBLE CONSENSUS
                </span>
              </div>

              <h1
                className="defect-name"
                style={{
                  fontSize:
                    "clamp(40px, 6vw, 64px)",
                  margin: 0,
                }}
              >
                {result.defect || "UNKNOWN"}
              </h1>

            </div>


            {/* =================================================
                CONFIDENCE & SEVERITY METRICS DUAL PANEL
            ================================================= */}

            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
                gap: "16px",
                marginBottom: "28px",
              }}
            >
              {/* CARD 1: AI CONFIDENCE */}
              <div
                style={{
                  padding: "24px",
                  borderRadius: "16px",
                  background:
                    "linear-gradient(145deg, rgba(0,229,255,.05), rgba(6,18,32,.7))",
                  border: "1px solid rgba(0,229,255,.2)",
                  boxShadow: "0 8px 30px rgba(0,0,0,.35)",
                  textAlign: "center",
                  display: "flex",
                  flexDirection: "column",
                  justifyContent: "space-between",
                }}
              >
                <div>
                  <p className="result-label" style={{ marginBottom: "10px" }}>
                    AI ENSEMBLE CONFIDENCE
                  </p>

                  <h2 className="confidence-value" style={{ margin: "4px 0 14px 0" }}>
                    {result.confidence ?? 0}%
                  </h2>

                  <div
                    style={{
                      width: "100%",
                      height: "9px",
                      margin: "14px auto",
                      borderRadius: "999px",
                      background: "rgba(0,229,255,.08)",
                      overflow: "hidden",
                      border: "1px solid rgba(0,229,255,.1)",
                    }}
                  >
                    <div
                      style={{
                        width: `${Math.min(
                          Number(result.confidence) || 0,
                          100
                        )}%`,
                        height: "100%",
                        background:
                          "linear-gradient(90deg, #00bfff, #00ffd5)",
                        boxShadow: "0 0 20px rgba(0,229,255,.55)",
                        transition: "width 1.2s ease",
                      }}
                    />
                  </div>
                </div>

                <div>
                  {Number(result.confidence) < CONFIDENCE_THRESHOLD ? (
                    <div
                      style={{
                        padding: "9px 14px",
                        border: "1px solid rgba(255,90,100,.35)",
                        borderRadius: "8px",
                        color: "#ff7777",
                        background: "rgba(255,70,80,.08)",
                        fontSize: "12px",
                        fontWeight: "600",
                      }}
                    >
                      ⚠ LOW CONFIDENCE • VERIFY
                    </div>
                  ) : (
                    <div
                      style={{
                        padding: "9px 14px",
                        border: "1px solid rgba(0,229,255,.3)",
                        borderRadius: "8px",
                        color: "#00ffd5",
                        background: "rgba(0,229,255,.08)",
                        fontSize: "12px",
                        fontWeight: "700",
                        letterSpacing: "0.5px",
                      }}
                    >
                      ✓ HIGH CONFIDENCE CONSENSUS
                    </div>
                  )}
                </div>
              </div>

              {/* CARD 2: DEFECT SEVERITY INDEX */}
              <div
                style={{
                  padding: "24px",
                  borderRadius: "16px",
                  background:
                    "linear-gradient(145deg, rgba(0,229,255,.05), rgba(6,18,32,.7))",
                  border: `1px solid ${(result.severity?.level === "CRITICAL")
                    ? "rgba(239, 68, 68, 0.45)"
                    : (result.severity?.level === "MODERATE")
                      ? "rgba(245, 158, 11, 0.45)"
                      : "rgba(16, 185, 129, 0.45)"
                    }`,
                  boxShadow: "0 8px 30px rgba(0,0,0,.35)",
                  textAlign: "center",
                  display: "flex",
                  flexDirection: "column",
                  justifyContent: "space-between",
                }}
              >
                <div>
                  <p className="result-label" style={{ marginBottom: "10px" }}>
                    DEFECT SEVERITY INDEX
                  </p>

                  <h2
                    style={{
                      margin: "4px 0 14px 0",
                      fontSize: "clamp(32px, 4vw, 42px)",
                      fontWeight: "800",
                      color: result.severity?.color || "#f59e0b",
                      fontFamily: "Space Mono, monospace",
                      letterSpacing: "1px",
                      textShadow: `0 0 20px ${(result.severity?.level === "CRITICAL")
                        ? "rgba(239, 68, 68, 0.4)"
                        : (result.severity?.level === "MODERATE")
                          ? "rgba(245, 158, 11, 0.4)"
                          : "rgba(16, 185, 129, 0.4)"
                        }`,
                    }}
                  >
                    {result.severity?.score ?? 0}
                    <span
                      style={{
                        fontSize: "16px",
                        color: "#5c7182",
                        fontWeight: "500",
                        marginLeft: "4px",
                      }}
                    >
                      / 100
                    </span>
                  </h2>

                  <div
                    style={{
                      width: "100%",
                      height: "9px",
                      margin: "14px auto",
                      borderRadius: "999px",
                      background: "rgba(255,255,255,.06)",
                      overflow: "hidden",
                      border: "1px solid rgba(255,255,255,.1)",
                    }}
                  >
                    <div
                      style={{
                        width: `${Math.min(
                          Number(result.severity?.score) || 0,
                          100
                        )}%`,
                        height: "100%",
                        background:
                          (result.severity?.level === "CRITICAL")
                            ? "linear-gradient(90deg, #f59e0b, #ef4444)"
                            : (result.severity?.level === "MODERATE")
                              ? "linear-gradient(90deg, #10b981, #f59e0b)"
                              : "linear-gradient(90deg, #00bfff, #10b981)",
                        boxShadow: `0 0 16px ${result.severity?.color || "#f59e0b"
                          }`,
                        transition: "width 1.2s ease",
                      }}
                    />
                  </div>
                </div>

                <div>
                  <div
                    style={{
                      display: "inline-flex",
                      alignItems: "center",
                      justifyContent: "center",
                      gap: "8px",
                      padding: "8px 18px",
                      borderRadius: "8px",
                      background:
                        (result.severity?.level === "CRITICAL")
                          ? "rgba(239, 68, 68, 0.15)"
                          : (result.severity?.level === "MODERATE")
                            ? "rgba(245, 158, 11, 0.15)"
                            : "rgba(16, 185, 129, 0.15)",
                      border: `1px solid ${result.severity?.color || "#f59e0b"
                        }`,
                      color: result.severity?.color || "#f59e0b",
                      fontSize: "12px",
                      fontWeight: "800",
                      fontFamily: "Space Mono, monospace",
                      letterSpacing: "1px",
                    }}
                  >
                    <span
                      style={{
                        width: "8px",
                        height: "8px",
                        borderRadius: "50%",
                        background:
                          result.severity?.color || "#f59e0b",
                        boxShadow: `0 0 8px ${result.severity?.color || "#f59e0b"
                          }`,
                      }}
                    />
                    {result.severity?.level || "MODERATE"} SEVERITY
                  </div>
                </div>
              </div>
            </div>


            {/* =================================================
                ENSEMBLE CONSENSUS BREAKDOWN
            ================================================= */}

            <div
              style={{
                marginBottom: "26px",
                padding: "20px 22px",
                borderRadius: "16px",
                background:
                  "linear-gradient(145deg, rgba(0,229,255,.05), rgba(6,18,32,.7))",
                border: "1px solid rgba(0,229,255,.22)",
                boxShadow: "0 8px 30px rgba(0,0,0,.4)",
              }}
            >

              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  marginBottom: "18px",
                  flexWrap: "wrap",
                  gap: "10px",
                }}
              >
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "8px",
                    fontFamily: "Space Mono, monospace",
                    fontSize: "10px",
                    color: "#00e5ff",
                    letterSpacing: "1.8px",
                    fontWeight: "700",
                  }}
                >
                  <span
                    style={{
                      width: "8px",
                      height: "8px",
                      borderRadius: "50%",
                      background: "#00ffd5",
                      boxShadow: "0 0 8px #00ffd5",
                      display: "inline-block",
                    }}
                  />
                  ENSEMBLE CONSENSUS BREAKDOWN
                </div>

                <div
                  style={{
                    fontFamily: "Space Mono, monospace",
                    fontSize: "9px",
                    color: "#8da0b3",
                    letterSpacing: "1.2px",
                    padding: "3px 10px",
                    borderRadius: "6px",
                    background: "rgba(0,229,255,.06)",
                    border: "1px solid rgba(0,229,255,.14)",
                  }}
                >
                  SOFT-VOTING AGGREGATION
                </div>
              </div>

              {/* 3 MODEL CARDS GRID */}
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
                  gap: "14px",
                }}
              >
                {/* 1. ResNet50 (Weight: 40%) */}
                <div
                  style={{
                    padding: "16px 18px",
                    borderRadius: "12px",
                    background:
                      "linear-gradient(145deg, rgba(0,229,255,.06), rgba(0,229,255,.015))",
                    border: "1px solid rgba(0,229,255,.18)",
                    display: "flex",
                    flexDirection: "column",
                    justifyContent: "space-between",
                    gap: "10px",
                  }}
                >
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                    }}
                  >
                    <span
                      style={{
                        fontFamily: "Space Mono, monospace",
                        fontSize: "12px",
                        fontWeight: "700",
                        color: "#ffffff",
                        letterSpacing: "1px",
                      }}
                    >
                      ResNet50
                    </span>
                    <span
                      style={{
                        fontFamily: "Space Mono, monospace",
                        fontSize: "9px",
                        padding: "2px 7px",
                        borderRadius: "4px",
                        background: "rgba(0,191,255,.15)",
                        border: "1px solid rgba(0,191,255,.3)",
                        color: "#00bfff",
                        fontWeight: "700",
                      }}
                    >
                      Weight: 40%
                    </span>
                  </div>

                  <div>
                    <div
                      style={{
                        fontFamily: "Space Mono, monospace",
                        fontSize: "9px",
                        color: "#5c7182",
                        letterSpacing: "1.2px",
                        marginBottom: "4px",
                      }}
                    >
                      PREDICTED DEFECT
                    </div>
                    <div
                      style={{
                        fontSize: "17px",
                        fontWeight: "800",
                        color: "#00e5ff",
                      }}
                    >
                      {result.ensemble_breakdown?.resnet50?.defect ||
                        result.defect ||
                        "Analyzing..."}
                    </div>
                  </div>

                  <div>
                    <div
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                        marginBottom: "6px",
                      }}
                    >
                      <span
                        style={{
                          fontFamily: "Space Mono, monospace",
                          fontSize: "9px",
                          color: "#5c7182",
                        }}
                      >
                        CONFIDENCE
                      </span>
                      <span
                        style={{
                          fontFamily: "Space Mono, monospace",
                          fontSize: "13px",
                          fontWeight: "700",
                          color: "#00ffd5",
                        }}
                      >
                        {result.ensemble_breakdown?.resnet50?.confidence ??
                          result.confidence ??
                          0}
                        %
                      </span>
                    </div>
                    <div
                      style={{
                        width: "100%",
                        height: "5px",
                        borderRadius: "999px",
                        background: "rgba(0,229,255,.1)",
                        overflow: "hidden",
                      }}
                    >
                      <div
                        style={{
                          width: `${Math.min(
                            Number(
                              result.ensemble_breakdown?.resnet50?.confidence ??
                              result.confidence ??
                              0
                            ),
                            100
                          )}%`,
                          height: "100%",
                          background:
                            "linear-gradient(90deg, #00bfff, #00ffd5)",
                          borderRadius: "999px",
                          transition: "width 1s ease",
                        }}
                      />
                    </div>
                  </div>
                </div>

                {/* 2. EfficientNet-B2 (Weight: 40%) */}
                <div
                  style={{
                    padding: "16px 18px",
                    borderRadius: "12px",
                    background:
                      "linear-gradient(145deg, rgba(0,229,255,.06), rgba(0,229,255,.015))",
                    border: "1px solid rgba(0,229,255,.18)",
                    display: "flex",
                    flexDirection: "column",
                    justifyContent: "space-between",
                    gap: "10px",
                  }}
                >
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                    }}
                  >
                    <span
                      style={{
                        fontFamily: "Space Mono, monospace",
                        fontSize: "12px",
                        fontWeight: "700",
                        color: "#ffffff",
                        letterSpacing: "1px",
                      }}
                    >
                      EfficientNet-B2
                    </span>
                    <span
                      style={{
                        fontFamily: "Space Mono, monospace",
                        fontSize: "9px",
                        padding: "2px 7px",
                        borderRadius: "4px",
                        background: "rgba(0,255,213,.15)",
                        border: "1px solid rgba(0,255,213,.3)",
                        color: "#00ffd5",
                        fontWeight: "700",
                      }}
                    >
                      Weight: 40%
                    </span>
                  </div>

                  <div>
                    <div
                      style={{
                        fontFamily: "Space Mono, monospace",
                        fontSize: "9px",
                        color: "#5c7182",
                        letterSpacing: "1.2px",
                        marginBottom: "4px",
                      }}
                    >
                      PREDICTED DEFECT
                    </div>
                    <div
                      style={{
                        fontSize: "17px",
                        fontWeight: "800",
                        color: "#00e5ff",
                      }}
                    >
                      {result.ensemble_breakdown?.efficientnet_b2?.defect ||
                        result.defect ||
                        "Analyzing..."}
                    </div>
                  </div>

                  <div>
                    <div
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                        marginBottom: "6px",
                      }}
                    >
                      <span
                        style={{
                          fontFamily: "Space Mono, monospace",
                          fontSize: "9px",
                          color: "#5c7182",
                        }}
                      >
                        CONFIDENCE
                      </span>
                      <span
                        style={{
                          fontFamily: "Space Mono, monospace",
                          fontSize: "13px",
                          fontWeight: "700",
                          color: "#00ffd5",
                        }}
                      >
                        {result.ensemble_breakdown?.efficientnet_b2
                          ?.confidence ??
                          result.confidence ??
                          0}
                        %
                      </span>
                    </div>
                    <div
                      style={{
                        width: "100%",
                        height: "5px",
                        borderRadius: "999px",
                        background: "rgba(0,229,255,.1)",
                        overflow: "hidden",
                      }}
                    >
                      <div
                        style={{
                          width: `${Math.min(
                            Number(
                              result.ensemble_breakdown?.efficientnet_b2
                                ?.confidence ??
                              result.confidence ??
                              0
                            ),
                            100
                          )}%`,
                          height: "100%",
                          background:
                            "linear-gradient(90deg, #00bfff, #00ffd5)",
                          borderRadius: "999px",
                          transition: "width 1s ease",
                        }}
                      />
                    </div>
                  </div>
                </div>

                {/* 3. ResNet18 (Weight: 20%) */}
                <div
                  style={{
                    padding: "16px 18px",
                    borderRadius: "12px",
                    background:
                      "linear-gradient(145deg, rgba(0,229,255,.06), rgba(0,229,255,.015))",
                    border: "1px solid rgba(0,229,255,.18)",
                    display: "flex",
                    flexDirection: "column",
                    justifyContent: "space-between",
                    gap: "10px",
                  }}
                >
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                    }}
                  >
                    <span
                      style={{
                        fontFamily: "Space Mono, monospace",
                        fontSize: "12px",
                        fontWeight: "700",
                        color: "#ffffff",
                        letterSpacing: "1px",
                      }}
                    >
                      ResNet18
                    </span>
                    <span
                      style={{
                        fontFamily: "Space Mono, monospace",
                        fontSize: "9px",
                        padding: "2px 7px",
                        borderRadius: "4px",
                        background: "rgba(168,85,247,.15)",
                        border: "1px solid rgba(168,85,247,.3)",
                        color: "#c084fc",
                        fontWeight: "700",
                      }}
                    >
                      Weight: 20%
                    </span>
                  </div>

                  <div>
                    <div
                      style={{
                        fontFamily: "Space Mono, monospace",
                        fontSize: "9px",
                        color: "#5c7182",
                        letterSpacing: "1.2px",
                        marginBottom: "4px",
                      }}
                    >
                      PREDICTED DEFECT
                    </div>
                    <div
                      style={{
                        fontSize: "17px",
                        fontWeight: "800",
                        color: "#00e5ff",
                      }}
                    >
                      {result.ensemble_breakdown?.resnet18?.defect ||
                        result.defect ||
                        "Analyzing..."}
                    </div>
                  </div>

                  <div>
                    <div
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                        marginBottom: "6px",
                      }}
                    >
                      <span
                        style={{
                          fontFamily: "Space Mono, monospace",
                          fontSize: "9px",
                          color: "#5c7182",
                        }}
                      >
                        CONFIDENCE
                      </span>
                      <span
                        style={{
                          fontFamily: "Space Mono, monospace",
                          fontSize: "13px",
                          fontWeight: "700",
                          color: "#00ffd5",
                        }}
                      >
                        {result.ensemble_breakdown?.resnet18?.confidence ??
                          result.confidence ??
                          0}
                        %
                      </span>
                    </div>
                    <div
                      style={{
                        width: "100%",
                        height: "5px",
                        borderRadius: "999px",
                        background: "rgba(0,229,255,.1)",
                        overflow: "hidden",
                      }}
                    >
                      <div
                        style={{
                          width: `${Math.min(
                            Number(
                              result.ensemble_breakdown?.resnet18?.confidence ??
                              result.confidence ??
                              0
                            ),
                            100
                          )}%`,
                          height: "100%",
                          background:
                            "linear-gradient(90deg, #00bfff, #00ffd5)",
                          borderRadius: "999px",
                          transition: "width 1s ease",
                        }}
                      />
                    </div>
                  </div>
                </div>
              </div>
            </div>


            {/* =================================================
                AI LOCALIZATION
            ================================================= */}

            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(2, 1fr)",
                gap: "15px",
                marginBottom: "16px",
              }}
            >

              {/* APPROXIMATE LOCATION */}

              <div
                style={{
                  padding: "24px",
                  border:
                    "1px solid rgba(0,229,255,.18)",
                  borderRadius: "14px",
                  background:
                    "linear-gradient(145deg, rgba(0,229,255,.07), rgba(0,229,255,.015))",
                  textAlign: "center",
                }}
              >

                <div
                  style={{
                    fontSize: "26px",
                    marginBottom: "10px",
                  }}
                >
                  ◎
                </div>

                <div
                  style={{
                    color: "#5c7182",
                    fontFamily:
                      "Space Mono, monospace",
                    fontSize: "9px",
                    letterSpacing: "2px",
                    marginBottom: "9px",
                  }}
                >
                  APPROXIMATE DEFECT LOCATION
                </div>

                <div
                  style={{
                    color: "#00e5ff",
                    fontSize: "23px",
                    fontWeight: "800",
                  }}
                >
                  {result.location ||
                    "Not clearly localized"}
                </div>

              </div>


              {/* HIGH-ACTIVATION REGION */}

              <div
                style={{
                  padding: "24px",
                  border:
                    "1px solid rgba(0,229,255,.18)",
                  borderRadius: "14px",
                  background:
                    "linear-gradient(145deg, rgba(0,229,255,.07), rgba(0,229,255,.015))",
                  textAlign: "center",
                }}
              >

                <div
                  style={{
                    fontSize: "26px",
                    marginBottom: "10px",
                  }}
                >
                  ◌
                </div>

                <div
                  style={{
                    color: "#5c7182",
                    fontFamily:
                      "Space Mono, monospace",
                    fontSize: "9px",
                    letterSpacing: "2px",
                    marginBottom: "9px",
                  }}
                >
                  HIGH-ACTIVATION REGION
                </div>

                <div
                  style={{
                    color: "#00e5ff",
                    fontSize: "23px",
                    fontWeight: "800",
                  }}
                >
                  {result.affected_area ?? 0}%
                </div>

                <div
                  style={{
                    marginTop: "8px",
                    color: "#627987",
                    fontSize: "9px",
                    lineHeight: "1.5",
                  }}
                >
                  Strong Grad-CAM activation
                </div>

              </div>

            </div>


            <div
              style={{
                marginBottom: "30px",
                padding: "13px 17px",
                border:
                  "1px solid rgba(0,229,255,.10)",
                borderRadius: "10px",
                background:
                  "rgba(0,229,255,.025)",
                color: "#627987",
                fontSize: "10px",
                lineHeight: 1.6,
                textAlign: "center",
              }}
            >
              AI-assisted localization based on
              Grad-CAM activation.
              <br />
              The percentage represents the region with
              strong model activation, not a measured
              physical defect area.
            </div>


            {/* =================================================
                AI EXPLANATION
            ================================================= */}

            <div
              style={{
                marginBottom: "30px",
                padding: "20px",
                border:
                  "1px solid rgba(0,229,255,.12)",
                borderRadius: "12px",
                background:
                  "rgba(0,229,255,.025)",
              }}
            >

              <div
                style={{
                  color: "#00e5ff",
                  fontFamily:
                    "Space Mono, monospace",
                  fontSize: "10px",
                  letterSpacing: "1.5px",
                  marginBottom: "10px",
                }}
              >
                AI EXPLANATION
              </div>

              <p
                style={{
                  margin: 0,
                  color: "#91a8b6",
                  lineHeight: 1.7,
                  fontSize: "13px",
                }}
              >
                The ResNet50 model classified this
                wafer map as{" "}
                <strong
                  style={{
                    color: "#d9f8ff",
                  }}
                >
                  {result.defect}
                </strong>{" "}
                with an estimated confidence of{" "}
                <strong
                  style={{
                    color: "#00e5ff",
                  }}
                >
                  {result.confidence}%
                </strong>
                . The Grad-CAM visualization
                highlights the image regions that
                contributed most strongly to the
                prediction.
              </p>

            </div>


            {/* =================================================
                IMAGE RESULTS
            ================================================= */}

            <div className="results-images">

              <div className="result-image-card">

                <h3>
                  ORIGINAL WAFER
                </h3>

                <img
                  src={preview}
                  alt="Original wafer"
                />

              </div>


              {result.heatmap && (

                <div className="result-image-card">

                  <h3>
                    AI EXPLANATION • GRAD-CAM
                  </h3>

                  <img
                    src={`${API_BASE_URL}${result.heatmap}`}
                    alt="AI Grad-CAM heatmap"
                  />

                </div>

              )}

            </div>


            {/* =================================================
                RESULT INFORMATION
            ================================================= */}

            <div className="results-grid">

              <div className="info-card">

                <div className="info-icon">
                  AI
                </div>

                <div>

                  <h3>
                    MODEL
                  </h3>

                  <p>
                    ResNet50
                  </p>

                </div>

              </div>


              <div className="info-card">

                <div className="info-icon">
                  ✓
                </div>

                <div>

                  <h3>
                    STATUS
                  </h3>

                  <p>
                    Analysis Complete
                  </p>

                </div>

              </div>


              <div className="info-card">

                <div className="info-icon">
                  XAI
                </div>

                <div>

                  <h3>
                    EXPLAINABILITY
                  </h3>

                  <p>
                    Grad-CAM Generated
                  </p>

                </div>

              </div>


              <div className="info-card">

                <div className="info-icon">
                  %
                </div>

                <div>

                  <h3>
                    CONFIDENCE
                  </h3>

                  <p>
                    {result.confidence}%
                  </p>

                </div>

              </div>

            </div>


            {/* =================================================
                TIMESTAMP
            ================================================= */}

            <div
              style={{
                marginTop: "20px",
                textAlign: "center",
                color: "#536c7c",
                fontFamily:
                  "Space Mono, monospace",
                fontSize: "9px",
                letterSpacing: "1px",
              }}
            >
              INSPECTION TIMESTAMP:{" "}
              {result.timestamp || "N/A"}
            </div>

          </section>

        )}


        {/* =================================================
            SESSION ANALYTICS
        ================================================= */}

        <section
          className="upload-card"
          style={{
            marginTop: "25px",
          }}
        >

          <div className="card-header">

            <div>

              <h2>
                Inspection Intelligence
              </h2>

              <p>
                Live analytics from the current
                inspection session
              </p>

            </div>

            <div className="model-badge">
              ANALYTICS
            </div>

          </div>


          <div className="results-grid">

            <div className="info-card">

              <div className="info-icon">
                #
              </div>

              <div>

                <h3>
                  TOTAL INSPECTIONS
                </h3>

                <p
                  style={{
                    fontSize: "25px",
                    color: "#00e5ff",
                    fontWeight: "800",
                  }}
                >
                  {totalInspections}
                </p>

              </div>

            </div>


            <div className="info-card">

              <div className="info-icon">
                %
              </div>

              <div>

                <h3>
                  AVG CONFIDENCE
                </h3>

                <p
                  style={{
                    fontSize: "25px",
                    color: "#00e5ff",
                    fontWeight: "800",
                  }}
                >
                  {averageConfidence}%
                </p>

              </div>

            </div>


            <div className="info-card">

              <div className="info-icon">
                ✓
              </div>

              <div>

                <h3>
                  HIGH CONFIDENCE
                </h3>

                <p
                  style={{
                    fontSize: "25px",
                    color: "#00e5ff",
                    fontWeight: "800",
                  }}
                >
                  {highConfidenceCount}
                </p>

              </div>

            </div>


            <div className="info-card">

              <div className="info-icon">
                !
              </div>

              <div>

                <h3>
                  REVIEW REQUIRED
                </h3>

                <p
                  style={{
                    fontSize: "25px",
                    color:
                      lowConfidenceCount > 0
                        ? "#ff7777"
                        : "#00e5ff",
                    fontWeight: "800",
                  }}
                >
                  {lowConfidenceCount}
                </p>

              </div>

            </div>

          </div>

        </section>


        {/* =================================================
            HISTORY
        ================================================= */}

        {history.length > 0 && (

          <section
            className="upload-card"
            style={{
              marginTop: "25px",
            }}
          >

            <div className="card-header">

              <div>

                <h2>
                  Inspection History
                </h2>

                <p>
                  Recent AI inspection records
                </p>

              </div>

              <div className="model-badge">
                {history.length} RECORDS
              </div>

            </div>


            <div
              style={{
                overflowX: "auto",
              }}
            >

              <table>

                <thead>

                  <tr>

                    <th>
                      WAFER
                    </th>

                    <th>
                      DEFECT
                    </th>

                    <th>
                      CONFIDENCE
                    </th>

                    <th>
                      LOCATION
                    </th>

                    <th>
                      AREA
                    </th>

                    <th>
                      REVIEW REQUIRED
                    </th>

                    <th>
                      TIME
                    </th>

                  </tr>

                </thead>


                <tbody>

                  {history.map(
                    (item) => (

                      <tr
                        key={item.id}
                      >

                        <td>
                          {item.wafer_id}
                        </td>

                        <td>

                          <strong
                            style={{
                              color:
                                "#00e5ff",
                            }}
                          >
                            {item.defect}
                          </strong>

                        </td>

                        <td>

                          {Number(
                            item.confidence
                          ).toFixed(1)}
                          %

                        </td>

                        <td>
                          {item.location ||
                            "N/A"}
                        </td>

                        <td>
                          {item.affected_area ?? 0}%
                        </td>

                        <td>

                          <strong
                            style={{
                              color:
                                Number(item.confidence || 0) <
                                  CONFIDENCE_THRESHOLD
                                  ? "#ff7777"
                                  : "#00e5ff",
                            }}
                          >
                            {Number(item.confidence || 0) <
                              CONFIDENCE_THRESHOLD
                              ? "YES"
                              : "NO"}
                          </strong>

                        </td>

                        <td>
                          {item.timestamp}
                        </td>

                      </tr>

                    )
                  )}

                </tbody>

              </table>

            </div>


            <button
              type="button"
              className="remove-button"
              onClick={handleClearHistory}
              style={{
                marginTop: "18px",
              }}
            >
              CLEAR HISTORY
            </button>

          </section>

        )}

      </main>


      {/* =================================================
          FOOTER
      ================================================= */}

      <footer>

        <div>
          SEMIVISION
        </div>

        <small>
          AI SEMICONDUCTOR WAFER INSPECTION
          {" • "}
          RESNET50
          {" • "}
          GRAD-CAM
        </small>

      </footer>

    </div>
  );
}

export default App;