import { useRef, useState } from "react";
import "./App.css";

function App() {
  const [image, setImage] = useState(null);
  const [preview, setPreview] = useState(null);

  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fileInputRef = useRef(null);

  // =========================================================
  // IMAGE SELECTION
  // =========================================================

  const handleImageChange = (event) => {
    const file = event.target.files[0];

    if (!file) {
      return;
    }

    // Check image type
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

    // Clear old result
    setResult(null);
    setError(null);
  };

  // =========================================================
  // REMOVE IMAGE
  // =========================================================

  const handleRemoveImage = () => {
    if (preview) {
      URL.revokeObjectURL(preview);
    }

    setImage(null);
    setPreview(null);
    setResult(null);
    setError(null);

    // Allow selecting same image again
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  // =========================================================
  // CHANGE IMAGE
  // =========================================================

  const handleChangeImage = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  // =========================================================
  // ANALYZE IMAGE
  // =========================================================

  const handleAnalyze = async () => {
    if (!image) {
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      // Create FormData
      const formData = new FormData();

      // IMPORTANT:
      // FastAPI endpoint expects the field name "file"
      formData.append("file", image);

      // Send image to FastAPI
      const response = await fetch(
        "http://127.0.0.1:8000/predict",
        {
          method: "POST",
          body: formData,
        }
      );

      // Check response
      if (!response.ok) {
        throw new Error(
          `Backend error: ${response.status}`
        );
      }

      // Convert response to JSON
      const data = await response.json();

      console.log("Backend response:", data);

      setResult(data);

    } catch (err) {
      console.error("Prediction error:", err);

      setError(
        "Unable to connect to the AI backend. Make sure FastAPI is running on port 8000."
      );
    } finally {
      setLoading(false);
    }
  };

  // =========================================================
  // UI
  // =========================================================

  return (
    <div className="app">

      {/* =====================================================
          HEADER
      ===================================================== */}

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


      {/* =====================================================
          MAIN
      ===================================================== */}

      <main className="main-container">

        {/* =================================================
            HERO
        ================================================= */}

        <section className="hero">

          <p className="eyebrow">
            AI SEMICONDUCTOR INSPECTION
          </p>

          <h1>
            Wafer Defect
            <span> Detection System</span>
          </h1>

          <p className="hero-text">
            Upload a semiconductor wafer image and let our AI
            model identify potential manufacturing defects.
          </p>

        </section>


        {/* =================================================
            UPLOAD CARD
        ================================================= */}

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


          {/* =================================================
              UPLOAD AREA
          ================================================= */}

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
                >
                  Change Image
                </button>

                <button
                  type="button"
                  className="remove-button"
                  onClick={handleRemoveImage}
                >
                  Remove
                </button>

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
              </div>

            </div>

          )}

        </section>


        {/* =================================================
            RESULTS
        ================================================= */}

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


            {/* =================================================
                PREDICTION
            ================================================= */}

            <div className="prediction-section">

              <p className="result-label">
                DETECTED DEFECT
              </p>

              <h1 className="defect-name">
                {result.defect}
              </h1>

            </div>


            {/* =================================================
                CONFIDENCE
            ================================================= */}

            <div className="confidence-section">

              <p className="result-label">
                CONFIDENCE
              </p>

              <h2 className="confidence-value">
                {result.confidence}%
              </h2>

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


            {/* =================================================
                INPUT + HEATMAP
            ================================================= */}

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
                    src={`http://127.0.0.1:8000${result.heatmap}`}
                    alt="AI heatmap"
                    className="result-image"
                  />

                </div>

              )}

            </div>


            {/* =================================================
                TIMESTAMP
            ================================================= */}

            {result.timestamp && (

              <p className="inspection-time">
                Inspection time: {result.timestamp}
              </p>

            )}

          </section>

        )}


        {/* =================================================
            INFORMATION CARDS
        ================================================= */}

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


      {/* =====================================================
          FOOTER
      ===================================================== */}

      <footer>
        SemiVision • Semiconductor Wafer Defect Detection
      </footer>

    </div>
  );
}

export default App;