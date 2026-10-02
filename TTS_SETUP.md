# AI4Bharat Indic-TTS & TranslateGemma Setup Guide 🎙️

This document details the installation, configuration, bugfixes, and model setup for running **AI4Bharat Indic-TTS** (Coqui TTS / FastPitch + HiFi-GAN V1 architecture) and **TranslateGemma** neural translation within the **SmritiCare NER** cognitive health platform.

---

## 📌 Supported Languages & Execution Strategy

SmritiCare is configured with a streamlined 2-language bilingual pipeline tailored for the North Eastern Region:

| Language | TTS Engine / Strategy | Pre-TTS Neural Translation | Model Location |
| :--- | :--- | :--- | :--- |
| **English** | **Device Offline Speech Engine** (`window.speechSynthesis`) | None (Native English Voice) | Built-in OS / Browser offline voices |
| **Assamese (অসমীয়া)** | **AI4Bharat Indic-TTS** (FastPitch + HiFi-GAN V1) | **TranslateGemma** (`translategemma:4b`) | `IndicTTS/as/` (1.5 GB Weights Extracted) |

### Key Workflow Highlights
1. **English Speech:** Completely offline, zero network latency, uses the device's native high-quality speech synthesizer.
2. **Assamese Speech:** If the input or reminder text is in English, **TranslateGemma automatically translates it into natural Assamese script** first, and then passes the translated text to the local IndicTTS pipeline!
3. **Local IndicTTS Checkpoints Extracted:**
   - FastPitch Acoustic Model: `IndicTTS/as/fastpitch/best_model.pth`
   - Acoustic Config: `IndicTTS/as/config.json`
   - HiFi-GAN Vocoder: `IndicTTS/as/hifigan/best_model.pth`
   - Vocoder Config: `IndicTTS/as/hifigan/config.json`
4. **Resilient Offline Fallback:** Even when completely disconnected from the internet, the local edge engine guarantees speech output without failure.

---

## ⚡ Zero-Install Quickstart (Pre-Configured in SmritiCare)

SmritiCare includes a built-in neural TTS pipeline (`/api/tts`) with **automatic model routing** and **local disk audio caching** (`audio_cache/`).

1. Ensure SmritiCare server is running:
   ```bash
   python server.py
   ```
2. Open `http://localhost:8080` in your web browser.
3. Use the header **🗣️ Voice:** dropdown to toggle between **অসমীয়া (IndicTTS)** and **English (Device)**.
4. Click **🎙️ Voice Settings** in the top navigation bar to test voice personas (Female / Male) or preview synthesized phrases.

---

## 🛠️ Complete Local Offline Installation (Trainer & TTS Setup)

For researchers, offline field deployments in rural tea gardens, or developers who want to run neural FastPitch + HiFi-GAN inference directly on local GPUs:

### Prerequisites
- **OS:** Ubuntu 20.04 / 22.04 LTS, Windows Subsystem for Linux (WSL2), or Windows 10/11 x64
- **Python:** Python 3.9 or 3.10 (recommended for PyTorch 1.11 / CUDA 11.3 wheels)
- **NVIDIA GPU:** GTX 1660 / RTX 3050 / RTX 4050 / RTX 5050 or higher with CUDA drivers

---

### Step 1: System Packages & Virtual Environment

#### On Linux / WSL:
```bash
sudo apt-get update
sudo apt-get install -y libsndfile1-dev ffmpeg enchant libespeak-ng-dev
conda create -n tts-env python=3.10 -y
conda activate tts-env
```

#### On Windows:
1. Ensure `ffmpeg` and `libsndfile` are accessible in your PATH.
2. Create virtual environment:
   ```bash
   conda create -n tts-env python=3.10 -y
   conda activate tts-env
   ```

---

### Step 2: PyTorch with CUDA 11.3 Setup

```bash
pip3 install -U torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu113
```

---

### Step 3: Setup Trainer & Apply Fixes

Clone and install `gokulkarthik/Trainer`:

```bash
git clone https://github.com/gokulkarthik/Trainer
cd Trainer
pip3 install -e .[all]
cd ..
```

#### Fixes & Patches for Trainer:
1. **Fix multi-GPU distribution string parsing** in `Trainer/trainer/distribute.py` (line 53):
   ```python
   # Line 53 in trainer/distribute.py:
   gpus = [str(gpu) for gpu in gpus]
   ```
2. **Copy logging & test fixes (if updating a site-packages installation):**
   ```bash
   cp Trainer/trainer/logging/wandb_logger.py <SITE_PACKAGES>/trainer/logging/
   cp Trainer/trainer/trainer.py <SITE_PACKAGES>/trainer/
   ```

---

### Step 4: Setup TTS & Apply Fixes

Clone and install `gokulkarthik/TTS` (Coqui TTS fork with Indic support):

```bash
git clone https://github.com/gokulkarthik/TTS
cd TTS
pip3 install -e .[all]
cd ..
```

#### Fixes & Patches for TTS:
1. **Multi-output synthesis support:**
   ```bash
   cp TTS/TTS/bin/synthesize.py <SITE_PACKAGES>/TTS/bin/
   ```

---

### Step 5: Install Supporting Requirements

```bash
pip3 install -r requirements.txt
```

Recommended dependency versions:
- `soundfile>=0.12.1`
- `scipy>=1.10.0`
- `librosa>=0.10.0`
- `indic-nlp-library>=0.92`

---

## 📦 Model Weights Download (Checkpoints)

Download pre-trained FastPitch acoustic models and HiFi-GAN vocoders from the official AI4Bharat release:

🔗 **GitHub Checkpoints Release:**  
[https://github.com/AI4Bharat/Indic-TTS/releases/tag/v1-checkpoints-release](https://github.com/AI4Bharat/Indic-TTS/releases/tag/v1-checkpoints-release)

### Direct Asset Downloads:
- **Assamese:** [as.zip](https://github.com/AI4Bharat/Indic-TTS/releases/download/v1-checkpoints-release/as.zip) (~1.44 GB)
- **Bodo:** [brx.zip](https://github.com/AI4Bharat/Indic-TTS/releases/download/v1-checkpoints-release/brx.zip) (~1.45 GB)
- **Meitei (Manipuri):** [mni.zip](https://github.com/AI4Bharat/Indic-TTS/releases/download/v1-checkpoints-release/mni.zip) (~1.44 GB)
- **Bengali:** [bn.zip](https://github.com/AI4Bharat/Indic-TTS/releases/download/v1-checkpoints-release/bn.zip) (~1.44 GB)
- **Hindi:** [hi.zip](https://github.com/AI4Bharat/Indic-TTS/releases/download/v1-checkpoints-release/hi.zip) (~1.44 GB)
- **English:** [en.zip](https://github.com/AI4Bharat/Indic-TTS/releases/download/v1-checkpoints-release/en.zip) (~1.46 GB)
- **Marathi:** [mr.zip](https://github.com/AI4Bharat/Indic-TTS/releases/download/v1-checkpoints-release/mr.zip)
- **Gujarati:** [gu.zip](https://github.com/AI4Bharat/Indic-TTS/releases/download/v1-checkpoints-release/gu.zip)
- **Odia:** [or.zip](https://github.com/AI4Bharat/Indic-TTS/releases/download/v1-checkpoints-release/or.zip)
- **Punjabi:** [pa.zip](https://github.com/AI4Bharat/Indic-TTS/releases/download/v1-checkpoints-release/pa.zip)
- **Rajasthani:** [raj.zip](https://github.com/AI4Bharat/Indic-TTS/releases/download/v1-checkpoints-release/raj.zip)

### Placement in SmritiCare:
Extract checkpoints directly into `IndicTTS/`:
```
SmritiCARE/
├── IndicTTS/
│   ├── as/
│   │   ├── fastpitch/
│   │   │   ├── best_model.pth    (637 MB)
│   │   │   └── speakers.pth      (female: 0, male: 1)
│   │   ├── config.json           (Acoustic config)
│   │   ├── hifigan/
│   │   │   ├── best_model.pth    (1 GB)
│   │   │   └── config.json       (Vocoder config)
│   └── as.zip                    (Downloaded source archive)
├── models/
│   └── v1/as/fastpitch/speakers.pth (Compatibility mirror)
├── TTS/                          (Cloned Coqui TTS with Indic extensions)
└── Trainer/                      (Cloned Trainer with distributed fix)
```

SmritiCare automatically detects local checkpoints and runs 100% offline local neural synthesis with disk audio caching (`audio_cache/`).

---

## 🎙️ Command-Line Inference Test (Verified Working)

```bash
python -m TTS.bin.synthesize \
    --text "নমস্কাৰ, আপুনি কেনে আছে?" \
    --speaker_idx female \
    --model_path IndicTTS/as/fastpitch/best_model.pth \
    --config_path IndicTTS/as/config.json \
    --vocoder_path IndicTTS/as/hifigan/best_model.pth \
    --vocoder_config_path IndicTTS/as/hifigan/config.json \
    --out_path audio_cache/output_as.wav
```

---

## 🌐 TranslateGemma Integration

SmritiCare uses `translategemma:4b` in local Ollama for bidirectional translation:

### 1. Ensure Model is Pulled in Ollama:
```bash
ollama pull translategemma:4b
```

### 2. Test Translation via API:
```bash
curl -X POST http://localhost:8080/api/ai/translate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Good morning! Did you drink your morning tea?",
    "target_language": "Assamese"
  }'
```

Response:
```json
{
  "success": true,
  "original": "Good morning! Did you drink your morning tea?",
  "target_language": "Assamese",
  "translated": "সুপ্রভাত! আপুনি ৰাতিপুৱাৰ চাহ খালে নেকি?"
}
```

---

## 📜 References
- **Paper:** *Towards Building Text-To-Speech Systems for the Next Billion Users* (ICASSP 2023)  
  Authors: Gokul Karthik Kumar, Praveen S V, Pratyush Kumar, Mitesh M. Khapra, Karthik Nandakumar  
  [https://arxiv.org/abs/2211.09536](https://arxiv.org/abs/2211.09536)
- **AI4Bharat Indic-TTS Repository:** [https://github.com/AI4Bharat/Indic-TTS](https://github.com/AI4Bharat/Indic-TTS)
- **Gokul Karthik TTS:** [https://github.com/gokulkarthik/TTS](https://github.com/gokulkarthik/TTS)
- **Coqui AI TTS:** [https://github.com/coqui-ai/TTS](https://github.com/coqui-ai/TTS)
