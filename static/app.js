document.addEventListener("DOMContentLoaded", () => {
  // Elements
  const videoUrlInput = document.getElementById("videoUrl");
  const pasteBtn = document.getElementById("pasteBtn");
  const clearUrlBtn = document.getElementById("clearUrlBtn");
  const generateBtn = document.getElementById("generateBtn");
  const translateOption = document.getElementById("translateOption");
  const activeEngineBadge = document.getElementById("activeEngineBadge");

  // Progress & Error
  const progressCard = document.getElementById("progressCard");
  const progressTitle = document.getElementById("progressTitle");
  const progressSubtitle = document.getElementById("progressSubtitle");
  const progressBar = document.getElementById("progressBar");
  const errorCard = document.getElementById("errorCard");
  const errorMessage = document.getElementById("errorMessage");
  const apiKeyPrompt = document.getElementById("apiKeyPrompt");

  // Result Elements
  const resultCard = document.getElementById("resultCard");
  const videoThumb = document.getElementById("videoThumb");
  const videoTitle = document.getElementById("videoTitle");
  const videoAuthor = document.getElementById("videoAuthor");
  const videoDurationBadge = document.getElementById("videoDurationBadge");
  const videoPlatformBadge = document.getElementById("videoPlatformBadge");

  // Tabs & Views
  const tabHindi = document.getElementById("tabHindi");
  const tabEnglish = document.getElementById("tabEnglish");
  const tabTimestamps = document.getElementById("tabTimestamps");
  const hindiView = document.getElementById("hindiView");
  const englishView = document.getElementById("englishView");
  const timestampsView = document.getElementById("timestampsView");
  const transcriptDisplay = document.getElementById("transcriptDisplay");

  // Actions
  const copyBtn = document.getElementById("copyBtn");
  const downloadDropdownBtn = document.getElementById("downloadDropdownBtn");
  const downloadMenu = document.getElementById("downloadMenu");
  const downloadTxtBtn = document.getElementById("downloadTxtBtn");
  const downloadSrtBtn = document.getElementById("downloadSrtBtn");
  const increaseFontBtn = document.getElementById("increaseFontBtn");
  const decreaseFontBtn = document.getElementById("decreaseFontBtn");

  // Settings Modal Elements
  const settingsBtn = document.getElementById("settingsBtn");
  const settingsModal = document.getElementById("settingsModal");
  const closeSettingsBtn = document.getElementById("closeSettingsBtn");
  const saveSettingsBtn = document.getElementById("saveSettingsBtn");
  const openSettingsFromError = document.getElementById("openSettingsFromError");
  const groqApiKeyInput = document.getElementById("groqApiKey");
  const geminiApiKeyInput = document.getElementById("geminiApiKey");
  const groqKeySection = document.getElementById("groqKeySection");
  const geminiKeySection = document.getElementById("geminiKeySection");
  const toast = document.getElementById("toast");

  // State
  let currentResult = null;
  let activeTab = "hindi";
  let currentFontSize = 14; // px
  let serverConfig = { has_groq_key: false, has_gemini_key: false };

  // 1. Initial Load & Settings Sync
  fetchServerConfig();
  loadSavedPreferences();

  async function fetchServerConfig() {
    try {
      const res = await fetch("/api/config");
      serverConfig = await res.json();
      updateEngineDisplay();
    } catch (e) {
      console.warn("Could not fetch server config:", e);
    }
  }

  function loadSavedPreferences() {
    const savedEngine = localStorage.getItem("bs_engine") || "groq";
    const savedGroqKey = localStorage.getItem("bs_groq_key") || "";
    const savedGeminiKey = localStorage.getItem("bs_gemini_key") || "";
    const savedTranslate = localStorage.getItem("bs_translate") === "true";

    groqApiKeyInput.value = savedGroqKey;
    geminiApiKeyInput.value = savedGeminiKey;
    translateOption.checked = savedTranslate;

    const radio = document.querySelector(`input[name="engineSelect"][value="${savedEngine}"]`);
    if (radio) radio.checked = true;

    toggleEngineKeyInputs(savedEngine);
    updateEngineDisplay();
  }

  function getSelectedEngine() {
    const checked = document.querySelector('input[name="engineSelect"]:checked');
    return checked ? checked.value : "groq";
  }

  function toggleEngineKeyInputs(engine) {
    if (engine === "gemini") {
      geminiKeySection.classList.remove("hidden");
      groqKeySection.classList.add("hidden");
    } else {
      groqKeySection.classList.remove("hidden");
      geminiKeySection.classList.add("hidden");
    }
  }

  function updateEngineDisplay() {
    const engine = getSelectedEngine();
    if (engine === "gemini") {
      activeEngineBadge.textContent = "Gemini 2.0 Flash";
    } else {
      activeEngineBadge.textContent = "Groq Whisper";
    }
  }

  // Engine selection radio change
  document.querySelectorAll('input[name="engineSelect"]').forEach(radio => {
    radio.addEventListener("change", (e) => {
      toggleEngineKeyInputs(e.target.value);
      updateEngineDisplay();
    });
  });

  // Settings Modal Handlers
  settingsBtn.addEventListener("click", () => settingsModal.classList.remove("hidden"));
  closeSettingsBtn.addEventListener("click", () => settingsModal.classList.add("hidden"));
  openSettingsFromError.addEventListener("click", () => {
    errorCard.classList.add("hidden");
    settingsModal.classList.remove("hidden");
  });

  saveSettingsBtn.addEventListener("click", () => {
    const engine = getSelectedEngine();
    localStorage.setItem("bs_engine", engine);
    localStorage.setItem("bs_groq_key", groqApiKeyInput.value.trim());
    localStorage.setItem("bs_gemini_key", geminiApiKeyInput.value.trim());
    localStorage.setItem("bs_translate", translateOption.checked);

    settingsModal.classList.add("hidden");
    updateEngineDisplay();
    showToast("Preferences saved!");
  });

  translateOption.addEventListener("change", () => {
    localStorage.setItem("bs_translate", translateOption.checked);
  });

  // 2. URL Cleaning & Paste Handling
  function cleanVideoUrl(rawUrl) {
    if (!rawUrl) return "";
    let trimmed = rawUrl.trim();
    try {
      if (trimmed.includes("facebook.com/login") || trimmed.includes("share_url=") || trimmed.includes("next=")) {
        const urlObj = new URL(trimmed);
        const params = urlObj.searchParams;
        if (params.has("share_url")) {
          return decodeURIComponent(params.get("share_url"));
        }
        if (params.has("next")) {
          const nextVal = decodeURIComponent(params.get("next"));
          try {
            const nextObj = new URL(nextVal.startsWith("http") ? nextVal : "https://" + nextVal);
            if (nextObj.searchParams.has("share_url")) {
              return decodeURIComponent(nextObj.searchParams.get("share_url"));
            }
          } catch (e) {}
          return nextVal;
        }
      }
    } catch (e) {}
    return trimmed;
  }

  videoUrlInput.addEventListener("input", () => {
    clearUrlBtn.classList.toggle("hidden", !videoUrlInput.value);
  });

  videoUrlInput.addEventListener("blur", () => {
    if (videoUrlInput.value) {
      videoUrlInput.value = cleanVideoUrl(videoUrlInput.value);
    }
  });

  clearUrlBtn.addEventListener("click", () => {
    videoUrlInput.value = "";
    clearUrlBtn.classList.add("hidden");
    videoUrlInput.focus();
  });

  pasteBtn.addEventListener("click", async () => {
    try {
      const text = await navigator.clipboard.readText();
      if (text) {
        const cleaned = cleanVideoUrl(text);
        videoUrlInput.value = cleaned;
        clearUrlBtn.classList.remove("hidden");
        showToast(cleaned !== text.trim() ? "Facebook link unwrapped & pasted!" : "Link pasted!");
      }
    } catch (err) {
      showToast("Clipboard access denied. Please paste manually.");
    }
  });

  // 3. Transcript Generation
  generateBtn.addEventListener("click", handleGenerate);

  async function handleGenerate() {
    const url = videoUrlInput.value.trim();
    if (!url) {
      showError("कृपया मान्य यूट्यूब या फेसबुक वीडियो लिंक डालें (Please enter a valid video link).");
      return;
    }

    const engine = getSelectedEngine();
    let apiKey = engine === "gemini" 
      ? (localStorage.getItem("bs_gemini_key") || geminiApiKeyInput.value.trim())
      : (localStorage.getItem("bs_groq_key") || groqApiKeyInput.value.trim());

    // Hide previous results and errors
    errorCard.classList.add("hidden");
    apiKeyPrompt.classList.add("hidden");
    resultCard.classList.add("hidden");
    progressCard.classList.remove("hidden");

    // Stepper updates
    setStep(1, "Connecting to Video...", "Locating stream & extracting audio");

    const timer1 = setTimeout(() => {
      setStep(2, "Extracting Audio...", "Converting audio to speech-optimized stream");
    }, 2500);

    const timer2 = setTimeout(() => {
      setStep(3, "Transcribing Hindi Speech...", `Running ${engine === 'gemini' ? 'Gemini 2.0 Flash' : 'Whisper-Large-v3'} AI`);
    }, 5500);

    try {
      generateBtn.disabled = true;

      const payload = {
        url: url,
        engine: engine,
        api_key: apiKey || null,
        translate: translateOption.checked
      };

      const response = await fetch("/api/transcribe", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      clearTimeout(timer1);
      clearTimeout(timer2);

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "An error occurred during transcription.");
      }

      currentResult = data;
      renderResult(data);
      progressCard.classList.add("hidden");
      resultCard.classList.remove("hidden");
      resultCard.scrollIntoView({ behavior: "smooth" });

    } catch (err) {
      clearTimeout(timer1);
      clearTimeout(timer2);
      progressCard.classList.add("hidden");
      showError(err.message);
    } finally {
      generateBtn.disabled = false;
    }
  }

  function setStep(step, title, subtitle) {
    progressTitle.textContent = title;
    progressSubtitle.textContent = subtitle;
    if (step === 1) progressBar.style.width = "30%";
    if (step === 2) progressBar.style.width = "65%";
    if (step === 3) progressBar.style.width = "90%";
  }

  function showError(msg) {
    errorMessage.textContent = msg;
    errorCard.classList.remove("hidden");
    if (msg.toLowerCase().includes("api key") || msg.toLowerCase().includes("missing")) {
      apiKeyPrompt.classList.remove("hidden");
    }
  }

  // 4. Render Transcription Results
  function renderResult(data) {
    // Video Metadata
    videoTitle.textContent = data.title || "Untitled Video";
    videoAuthor.textContent = data.uploader || "Creator";
    videoPlatformBadge.textContent = (data.platform || "VIDEO").toUpperCase();
    
    if (data.duration) {
      const mins = Math.floor(data.duration / 60);
      const secs = Math.floor(data.duration % 60);
      videoDurationBadge.textContent = `${mins}:${secs < 10 ? '0' : ''}${secs}`;
      videoDurationBadge.classList.remove("hidden");
    } else {
      videoDurationBadge.classList.add("hidden");
    }

    if (data.thumbnail) {
      videoThumb.src = data.thumbnail;
      videoThumb.classList.remove("hidden");
    } else {
      videoThumb.classList.add("hidden");
    }

    // Hindi Text Pane
    hindiView.textContent = data.hindi_transcript || "कोई ट्रांसक्रिप्ट उपलब्ध नहीं है (No transcript generated).";

    // English Text Pane
    if (data.english_transcript && data.english_transcript.trim()) {
      englishView.textContent = data.english_transcript;
      tabEnglish.classList.remove("hidden");
    } else {
      tabEnglish.classList.add("hidden");
    }

    // Timestamps Pane
    renderTimestamps(data.segments || []);

    // Reset to Hindi tab
    switchTab("hindi");
  }

  function renderTimestamps(segments) {
    timestampsView.innerHTML = "";
    if (!segments || segments.length === 0) {
      timestampsView.innerHTML = `<p class="text-xs text-slate-500 italic">No detailed segment timestamps available.</p>`;
      return;
    }

    segments.forEach(seg => {
      const item = document.createElement("div");
      item.className = "p-2 rounded-xl bg-slate-950/60 border border-slate-800/80 hover:border-orange-500/40 transition-all text-xs flex gap-2.5 items-start cursor-pointer group";
      
      const timeTag = seg.start_formatted || `${seg.start || 0}s`;
      item.innerHTML = `
        <span class="px-2 py-0.5 rounded-md bg-orange-500/20 text-orange-400 font-mono text-[11px] font-semibold shrink-0 group-hover:bg-orange-500/30">
          ${timeTag}
        </span>
        <div class="flex-1">
          <p class="text-slate-200 font-hindi leading-snug">${seg.hindi || seg.text || ""}</p>
          ${seg.english ? `<p class="text-slate-400 text-[11px] mt-0.5 font-sans">${seg.english}</p>` : ""}
        </div>
      `;

      item.addEventListener("click", () => {
        const textToCopy = `[${timeTag}] ${seg.hindi || seg.text || ""}`;
        copyTextToClipboard(textToCopy);
        showToast(`Copied snippet (${timeTag})!`);
      });

      timestampsView.appendChild(item);
    });
  }

  // 5. Tabs Switching
  tabHindi.addEventListener("click", () => switchTab("hindi"));
  tabEnglish.addEventListener("click", () => switchTab("english"));
  tabTimestamps.addEventListener("click", () => switchTab("timestamps"));

  function switchTab(tab) {
    activeTab = tab;

    // Reset active styles
    [tabHindi, tabEnglish, tabTimestamps].forEach(btn => {
      btn.className = "flex-1 py-2 rounded-xl text-xs font-medium transition-all text-slate-400 hover:text-white";
    });

    hindiView.classList.add("hidden");
    englishView.classList.add("hidden");
    timestampsView.classList.add("hidden");

    if (tab === "hindi") {
      tabHindi.className = "flex-1 py-2 rounded-xl text-xs font-semibold transition-all bg-orange-500/20 text-orange-400 border border-orange-500/30";
      hindiView.classList.remove("hidden");
    } else if (tab === "english") {
      tabEnglish.className = "flex-1 py-2 rounded-xl text-xs font-semibold transition-all bg-orange-500/20 text-orange-400 border border-orange-500/30";
      englishView.classList.remove("hidden");
    } else if (tab === "timestamps") {
      tabTimestamps.className = "flex-1 py-2 rounded-xl text-xs font-semibold transition-all bg-orange-500/20 text-orange-400 border border-orange-500/30";
      timestampsView.classList.remove("hidden");
    }
  }

  // 6. Copy & Download Handlers
  copyBtn.addEventListener("click", () => {
    if (!currentResult) return;
    let content = "";
    if (activeTab === "hindi") {
      content = currentResult.hindi_transcript;
    } else if (activeTab === "english") {
      content = currentResult.english_transcript;
    } else {
      content = (currentResult.segments || []).map(s => `[${s.start_formatted || s.start}] ${s.hindi || s.text || ""}`).join("\n");
    }

    if (content) {
      copyTextToClipboard(content);
      showToast("Transcript copied!");
    }
  });

  downloadDropdownBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    downloadMenu.classList.toggle("hidden");
  });

  document.addEventListener("click", () => {
    downloadMenu.classList.add("hidden");
  });

  downloadTxtBtn.addEventListener("click", () => {
    if (!currentResult) return;
    const title = (currentResult.title || "transcript").replace(/[/\\?%*:|"<>]/g, '-');
    let content = `Title: ${currentResult.title}\nPlatform: ${currentResult.platform}\n\n=== HINDI TRANSCRIPT ===\n${currentResult.hindi_transcript}\n`;
    if (currentResult.english_transcript) {
      content += `\n=== ENGLISH TRANSLATION ===\n${currentResult.english_transcript}\n`;
    }
    triggerDownload(`${title}.txt`, content, "text/plain");
  });

  downloadSrtBtn.addEventListener("click", () => {
    if (!currentResult) return;
    const title = (currentResult.title || "subtitles").replace(/[/\\?%*:|"<>]/g, '-');
    const srt = currentResult.srt_hindi || "1\n00:00:00,000 --> 00:00:05,000\n" + (currentResult.hindi_transcript || "");
    triggerDownload(`${title}.srt`, srt, "text/plain");
  });

  function triggerDownload(filename, content, type) {
    const blob = new Blob([content], { type: `${type};charset=utf-8;` });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    showToast(`Saved as ${filename}`);
  }

  function copyTextToClipboard(text) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text);
    } else {
      const textarea = document.createElement("textarea");
      textarea.value = text;
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand("copy");
      document.body.removeChild(textarea);
    }
  }

  // 7. Font Size Controls
  increaseFontBtn.addEventListener("click", () => {
    if (currentFontSize < 24) {
      currentFontSize += 2;
      transcriptDisplay.style.fontSize = `${currentFontSize}px`;
    }
  });

  decreaseFontBtn.addEventListener("click", () => {
    if (currentFontSize > 12) {
      currentFontSize -= 2;
      transcriptDisplay.style.fontSize = `${currentFontSize}px`;
    }
  });

  // 8. Toast Helper
  let toastTimer = null;
  function showToast(message) {
    toast.textContent = message;
    toast.classList.remove("opacity-0");
    toast.classList.add("opacity-100");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => {
      toast.classList.remove("opacity-100");
      toast.classList.add("opacity-0");
    }, 2200);
  }
});
