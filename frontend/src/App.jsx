import { useRef, useState } from "react";
import "./App.css";

const API_BASE_URL = "http://127.0.0.1:8000";
const CONFIDENCE_THRESHOLD = 70;

function App() {
  const [image, setImage] = useState(null);
  const [preview, setPreview] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // =========================
  // PREDICTION HISTORY
  // =========================

  const [history, setHistory] = useState(() => {
    try {
      return JSON.parse(
        localStorage.getItem("wafer_prediction_history")
      ) || [];
    } catch {
      return [];
    }
  });

  const fileInputRef = useRef(null);

  // =========================
  // SELECT IMAGE
  // =========================

  const handleImageChange = (event) => {
    const file = event.target.files[0];

    if (!file) return;

    if (!file.type.startsWith("image/")) {
      setError("Please select a valid image file.");
      return;
    }

    // Remove old preview
    if (preview) {
      URL.revokeObjectURL(preview);
    }

    const newPreview = URL.createObjectURL(file);

    setImage(file);
    setPreview(newPreview);

    // Clear previous result
    setResult(null);
    setError(null);
  };

  // =========================
  // REMOVE IMAGE
  // =========================

  const handleRemoveImage = () => {
    if (preview) {
      URL.revokeObjectURL(preview);
    }

    setImage(null);
    setPreview(null);
    setResult(null);
    setError(null);

    // Allows selecting the same image again
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  // =========================
  // CHANGE IMAGE
  // =========================

  const handleChangeImage = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  // =========================
  // ANALYZE IMAGE
  // =========================

  const handleAnalyze = async () => {
    if (!image) return;

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const formData = new FormData();

      // FastAPI expects "file"
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
          // Keep default error message
        }

        throw new Error(message);
      }

      const data = await response.json();

      console.log("AI Backend Response:", data);

      // Display result
      setResult(data);

      // =========================
      // SAVE PREDICTION HISTORY
      // =========================

      const historyItem = {
        id: Date.now(),
        wafer_id: data.wafer_id || image.name,
        defect: data.defect || "Unknown",
        confidence: Number(data.confidence) || 0,
        timestamp:
          data.timestamp || new Date().toLocaleString(),
      };

      const updatedHistory = [
        historyItem,
        ...history,
      ].slice(0, 20);

      setHistory(updatedHistory);

      localStorage.setItem(
        "wafer_prediction_history",
        JSON.stringify(updatedHistory)
      );

    } catch (err) {
      console.error("Prediction error:", err);

      setError(
        err.message ||
        "Unable to connect to the AI backend."
      );

    } finally {
      setLoading(false);
    }
  };

  // =========================
  // CLEAR HISTORY
  // =========================

  const handleClearHistory = () => {
    setHistory([]);

    localStorage.removeItem(
      "wafer_prediction_history"
    );
  };

  return (
    <div className="app">

      {/* =========================
          HEADER
      ========================= */}

      <header className="header">

        <div className="logo">
          <span className="logo-icon">⚡</span>
          <span>SemiVision</span>
        </div>

        <div className="header-status">
          <span className="status-dot"></span>
          SYSTEM ONLINE
        </div>

      </header>


      {/* =========================
          MAIN
      ========================= */}

      <main className="main-container">

        {/* =========================
            HERO
        ========================= */}

        <section className="hero">

          <p className="eyebrow">
            AI SEMICONDUCTOR INSPECTION
          </p>

          <h1>
            Wafer Defect
            <span> Detection System</span>
          </h1>

          <p className="hero-text">
            Upload a semiconductor wafer image and let our
            AI model identify potential manufacturing defects.
          </p>

        </section>


        {/* =========================
            UPLOAD CARD
        ========================= */}

        <section className="upload-card">

          <div className="card-header">

            <div>

              <h2>Wafer Inspection</h2>

              <p>
                Upload a wafer map image for AI analysis
              </p>

            </div>

            <div className="model-badge">
              ResNet50
            </div>

          </div>


          {/* =========================
              UPLOAD AREA
          ========================= */}

          <label className="upload-area">

            {preview ? (

              <div className="preview-container">

                <img
                  src={preview}
                  alt="Wafer preview"
                  className="image-preview"
                />

                <div className="preview-overlay">

                  <span>
                    Wafer Image Ready
                  </span>

                </div>

              </div>

            ) : (

              <>

                <div className="upload-icon">
                  ↑
                </div>

                <h3>
                  Upload Wafer Image
                </h3>

                <p>
                  Click here to select an image
                </p>

                <span>
                  PNG, JPG or JPEG
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


          {/* =========================
              SELECTED FILE
          ========================= */}

          {image && (

            <div className="selected-file">

              <div className="file-name">

                <span className="file-check">
                  ✓
                </span>

                <div>

                  <small>
                    Selected wafer
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
                  Change Image
                </button>

                <button
                  type="button"
                  className="remove-button"
                  onClick={handleRemoveImage}
                  disabled={loading}
                >
                  Remove
                </button>

              </div>

            </div>

          )}


          {/* =========================
              ANALYZE BUTTON
          ========================= */}

          <button
            className="analyze-button"
            onClick={handleAnalyze}
            disabled={!image || loading}
          >

            {loading ? (

              <>
                <span className="loading-spinner"></span>
                Analyzing Wafer...
              </>

            ) : (

              <>
                Analyze Wafer

                <span className="button-arrow">
                  →
                </span>
              </>

            )}

          </button>


          {/* =========================
              ERROR
          ========================= */}

          {error && (

            <div className="error-message">

              <span>
                ⚠
              </span>

              <div>
                {error}
              </div>

            </div>

          )}

        </section>


        {/* =========================
            AI RESULT
        ========================= */}

        {result && (

          <section className="upload-card result-card">

            {/* RESULT HEADER */}

            <div className="card-header">

              <div>

                <h2>
                  Analysis Result
                </h2>

                <p>
                  AI prediction from ResNet50
                </p>

              </div>

              <div className="model-badge result-badge">
                AI RESULT
              </div>

            </div>


            {/* =========================
                DEFECT
            ========================= */}

            <div className="prediction-section">

              <p className="result-label">
                DETECTED DEFECT
              </p>

              <h1 className="defect-name">
                {result.defect || "Unknown"}
              </h1>

            </div>


            {/* =========================
                CONFIDENCE
            ========================= */}

            <div className="confidence-section">

              <p className="result-label">
                CONFIDENCE
              </p>

              <h2 className="confidence-value">
                {result.confidence ?? 0}%
              </h2>


              {/* =========================
                  CONFIDENCE WARNING
              ========================= */}

              {Number(result.confidence) <
              CONFIDENCE_THRESHOLD ? (

                <div
                  className="confidence-warning"
                  style={{
                    margin: "15px auto",
                    padding: "14px 18px",
                    border: "1px solid #ff5c5c",
                    borderRadius: "10px",
                    background:
                      "rgba(255, 80, 80, 0.08)",
                    color: "#ff7777",
                    fontWeight: "600",
                    textAlign: "center",
                    maxWidth: "600px",
                  }}
                >

                  ⚠ Low Confidence Prediction

                  <span
                    style={{
                      display: "block",
                      marginTop: "6px",
                      fontSize: "13px",
                      fontWeight: "400",
                    }}
                  >
                    The AI confidence is below{" "}
                    {CONFIDENCE_THRESHOLD}%.
                    Please verify this wafer manually.
                  </span>

                </div>

              ) : (

                <div
                  className="confidence-success"
                  style={{
                    margin: "12px auto",
                    color: "#00e5ff",
                    fontSize: "14px",
                    fontWeight: "600",
                    textAlign: "center",
                  }}
                >
                  ✓ High Confidence Prediction
                </div>

              )}


              <div className="confidence-bar">

                <div
                  className="confidence-fill"
                  style={{
                    width: `${Math.min(
                      Number(result.confidence) || 0,
                      100
                    )}%`,
                  }}
                ></div>

              </div>

            </div>


            {/* =========================
                IMAGES
            ========================= */}

            <div className="results-images">

              {/* INPUT IMAGE */}

              <div className="result-image-card">

                <div className="result-image-header">

                  <h3>
                    Input Wafer
                  </h3>

                  <span>
                    ORIGINAL
                  </span>

                </div>

                <img
                  src={preview}
                  alt="Input wafer"
                  className="result-image"
                />

              </div>


              {/* HEATMAP */}

              {result.heatmap && (

                <div className="result-image-card">

                  <div className="result-image-header">

                    <h3>
                      AI Heatmap
                    </h3>

                    <span>
                      GRAD-CAM
                    </span>

                  </div>

                  <img
                    src={`${API_BASE_URL}${result.heatmap}`}
                    alt="AI heatmap"
                    className="result-image"
                  />

                </div>

              )}

            </div>


            {/* =========================
                EXTRA RESULT INFO
            ========================= */}

            <div className="result-details">

              <div>

                <span>
                  MODEL
                </span>

                <strong>
                  ResNet50
                </strong>

              </div>

              <div>

                <span>
                  STATUS
                </span>

                <strong>
                  Analysis Complete
                </strong>

              </div>

              {result.timestamp && (

                <div>

                  <span>
                    TIME
                  </span>

                  <strong>
                    {result.timestamp}
                  </strong>

                </div>

              )}

            </div>

          </section>

        )}


        {/* =========================
            PREDICTION HISTORY
        ========================= */}

        {history.length > 0 && (

          <section
            className="upload-card history-card"
            style={{
              marginTop: "25px",
            }}
          >

            <div className="card-header">

              <div>

                <h2>
                  Prediction History
                </h2>

                <p>
                  Recent wafer inspection results
                </p>

              </div>

              <div className="model-badge">
                {history.length} RECORDS
              </div>

            </div>


            <div
              className="history-list"
              style={{
                display: "flex",
                flexDirection: "column",
                gap: "10px",
                marginTop: "20px",
              }}
            >

              {history.map((item) => (

                <div
                  className="history-item"
                  key={item.id}
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    gap: "20px",
                    padding: "15px",
                    border:
                      "1px solid rgba(0, 229, 255, 0.15)",
                    borderRadius: "10px",
                    background:
                      "rgba(0, 20, 30, 0.5)",
                  }}
                >

                  <div
                    className="history-info"
                    style={{
                      display: "flex",
                      flexDirection: "column",
                      gap: "5px",
                    }}
                  >

                    <strong>
                      {item.wafer_id}
                    </strong>

                    <span
                      style={{
                        fontSize: "12px",
                        opacity: "0.6",
                      }}
                    >
                      {item.timestamp}
                    </span>

                  </div>


                  <div
                    className="history-prediction"
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "15px",
                    }}
                  >

                    <strong>
                      {item.defect}
                    </strong>

                    <span>
                      {item.confidence.toFixed(1)}%
                    </span>

                  </div>

                </div>

              ))}

            </div>


            {/* CLEAR HISTORY */}

            <button
              type="button"
              className="remove-button"
              onClick={handleClearHistory}
              style={{
                marginTop: "20px",
              }}
            >
              Clear History
            </button>

          </section>

        )}


        {/* =========================
            INFORMATION CARDS
        ========================= */}

        <section className="results-grid">

          <div className="info-card">

            <div className="info-icon">
              AI
            </div>

            <div>

              <h3>
                AI Classification
              </h3>

              <p>
                ResNet50 image classification model
              </p>

            </div>

          </div>


          <div className="info-card">

            <div className="info-icon">
              ✓
            </div>

            <div>

              <h3>
                Defect Detection
              </h3>

              <p>
                Identifies 8 wafer defect categories
              </p>

            </div>

          </div>


          <div className="info-card">

            <div className="info-icon">
              %
            </div>

            <div>

              <h3>
                Confidence Score
              </h3>

              <p>
                Displays AI prediction confidence
              </p>

            </div>

          </div>

        </section>

      </main>


      {/* =========================
          FOOTER
      ========================= */}

      <footer>
        SemiVision • Semiconductor Wafer Defect Detection
      </footer>

    </div>
  );
}

export default App;