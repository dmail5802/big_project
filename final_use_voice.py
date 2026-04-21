"""Runtime helpers for loading the trained voice artifacts and creating WAV files.

This module is intended to be called from the local GUI / main application.
It loads the saved SpeechT5 LoRA adapter, processor, vocoder, and speaker
embedding from the artifacts produced by create_voice.ipynb.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING
from pathlib import Path
from typing import Any

if TYPE_CHECKING:
    import numpy as np
    import torch
    from peft import PeftModel
    from transformers import SpeechT5ForTextToSpeech, SpeechT5HifiGan, SpeechT5Processor

DEFAULT_ARTIFACT_DIR_NAME = "voice_model_artifacts"
DEFAULT_PACKAGE_FILENAME = "teacher_voice_package.pt"
DEFAULT_ADAPTER_DIR_NAME = "teacher_voice_lora_adapter"
DEFAULT_PROCESSOR_DIR_NAME = "processor"
DEFAULT_VOCODER_DIR_NAME = "vocoder"
DEFAULT_OUTPUT_WAV_DIR_NAME = "synthesized_audio"
DEFAULT_SAMPLE_RATE = 16000
DEFAULT_BASE_MODEL_NAME = "microsoft/speecht5_tts"


@dataclass
class VoiceRuntime:
    """Container for the loaded voice synthesis components."""

    project_root: Path
    artifact_dir: Path
    output_wav_dir: Path
    processor: Any
    model: Any
    vocoder: Any
    speaker_embedding: Any
    sample_rate: int
    base_model_name: str
    device: torch.device


def _resolve_project_root(project_root: str | Path | None = None) -> Path:
    if project_root is not None:
        return Path(project_root).expanduser().resolve()
    return Path(__file__).resolve().parent


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _load_package(package_path: Path) -> dict[str, Any]:
    import torch
    
    if not package_path.exists():
        return {}
    try:
        return torch.load(package_path, map_location="cpu", weights_only=False)
    except TypeError:
        return torch.load(package_path, map_location="cpu")


def _extract_base_model_name(artifact_dir: Path, fallback: str = DEFAULT_BASE_MODEL_NAME) -> str:
    adapter_config_path = artifact_dir / DEFAULT_ADAPTER_DIR_NAME / "adapter_config.json"
    adapter_config = _read_json(adapter_config_path)
    base_model_name = adapter_config.get("base_model_name_or_path")
    if base_model_name:
        return str(base_model_name)

    train_config = _read_json(artifact_dir / "train_config.json")
    return str(train_config.get("base_model_name", fallback))


def _sanitize_filename(text: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", text.strip())
    cleaned = cleaned.strip("._-")
    return cleaned or "speech_output"


def load_voice_runtime(
    project_root: str | Path | None = None,
    artifact_dir: str | Path | None = None,
    device: str | "torch.device" | None = None,
) -> VoiceRuntime:
    """Load the trained voice components from disk.

    The loader prefers the saved SpeechT5 LoRA adapter if present. If the
    adapter is missing, it falls back to the base model name stored in the
    artifact metadata.
    """

    import torch
    from peft import PeftModel
    from transformers import SpeechT5ForTextToSpeech, SpeechT5HifiGan, SpeechT5Processor

    root = _resolve_project_root(project_root)
    resolved_artifact_dir = Path(artifact_dir).expanduser().resolve() if artifact_dir else root / DEFAULT_ARTIFACT_DIR_NAME
    resolved_artifact_dir.mkdir(parents=True, exist_ok=True)

    train_config = _read_json(resolved_artifact_dir / "train_config.json")
    package = _load_package(resolved_artifact_dir / DEFAULT_PACKAGE_FILENAME)

    resolved_device = torch.device(device) if device is not None else torch.device("cpu")
    sample_rate = int(train_config.get("sample_rate", DEFAULT_SAMPLE_RATE))
    output_wav_dir_name = str(train_config.get("output_wav_dir", DEFAULT_OUTPUT_WAV_DIR_NAME))
    output_wav_dir = resolved_artifact_dir / output_wav_dir_name
    output_wav_dir.mkdir(parents=True, exist_ok=True)

    processor_dir = resolved_artifact_dir / DEFAULT_PROCESSOR_DIR_NAME
    vocoder_dir = resolved_artifact_dir / DEFAULT_VOCODER_DIR_NAME
    adapter_dir = resolved_artifact_dir / DEFAULT_ADAPTER_DIR_NAME

    if not processor_dir.exists():
        raise FileNotFoundError(f"Processor directory not found: {processor_dir}")
    if not vocoder_dir.exists():
        raise FileNotFoundError(f"Vocoder directory not found: {vocoder_dir}")

    processor = SpeechT5Processor.from_pretrained(str(processor_dir))
    vocoder = SpeechT5HifiGan.from_pretrained(str(vocoder_dir)).to(resolved_device)

    base_model_name = _extract_base_model_name(resolved_artifact_dir)
    base_model = SpeechT5ForTextToSpeech.from_pretrained(base_model_name).to(resolved_device)

    if adapter_dir.exists():
        try:
            model: SpeechT5ForTextToSpeech | PeftModel = PeftModel.from_pretrained(base_model, str(adapter_dir))
        except Exception:
            # If the adapter cannot be restored, fall back to the base model.
            model = base_model
    else:
        model = base_model

    speaker_embedding = package.get("speaker_embedding")
    if speaker_embedding is None:
        speaker_embedding = torch.zeros(512, dtype=torch.float32)
    elif not isinstance(speaker_embedding, torch.Tensor):
        speaker_embedding = torch.tensor(speaker_embedding, dtype=torch.float32)

    return VoiceRuntime(
        project_root=root,
        artifact_dir=resolved_artifact_dir,
        output_wav_dir=output_wav_dir,
        processor=processor,
        model=model,
        vocoder=vocoder,
        speaker_embedding=speaker_embedding.float(),
        sample_rate=sample_rate,
        base_model_name=base_model_name,
        device=resolved_device,
    )


def create_voice_file(
    text: str,
    runtime: VoiceRuntime | None = None,
    output_filename: str | None = None,
    project_root: str | Path | None = None,
    artifact_dir: str | Path | None = None,
    device: str | "torch.device" | None = None,
) -> Path:
    """Synthesize text to a WAV file and return the saved file path."""

    active_runtime = runtime or load_voice_runtime(
        project_root=project_root,
        artifact_dir=artifact_dir,
        device=device,
    )

    if not text or not text.strip():
        raise ValueError("Text to synthesize cannot be empty.")

    normalized_text = " ".join(text.strip().split())
    filename = output_filename or f"output_{_sanitize_filename(normalized_text)}.wav"
    output_path = active_runtime.output_wav_dir / filename

    active_runtime.model.eval()
    active_runtime.vocoder.eval()

    import numpy as np
    import scipy.io.wavfile as wavfile
    import torch

    inputs = active_runtime.processor(text=normalized_text, return_tensors="pt")
    input_ids = inputs["input_ids"].to(active_runtime.device)
    speaker_embeddings = active_runtime.speaker_embedding.to(active_runtime.device).unsqueeze(0)

    with torch.no_grad():
        spectrogram = active_runtime.model.generate_speech(
            input_ids,
            speaker_embeddings=speaker_embeddings,
        )
        waveform = active_runtime.vocoder(spectrogram).detach().cpu().squeeze().numpy()

    waveform = np.asarray(waveform, dtype=np.float32)
    if waveform.ndim > 1:
        waveform = waveform.squeeze()

    peak = float(np.max(np.abs(waveform))) if waveform.size else 0.0
    if peak > 0:
        waveform = waveform / peak

    audio_int16 = (waveform * 32767).astype(np.int16)

    wavfile.write(str(output_path), active_runtime.sample_rate, audio_int16)
    return output_path


def create_voice_file_from_runtime(text: str, runtime: VoiceRuntime) -> Path:
    """Convenience wrapper for callers that already loaded the runtime."""

    return create_voice_file(text=text, runtime=runtime)


def load_and_create_voice_file(
    text: str,
    project_root: str | Path | None = None,
    artifact_dir: str | Path | None = None,
    device: str | "torch.device" | None = None,
    output_filename: str | None = None,
) -> Path:
    """Load the voice runtime and synthesize a file in one call."""

    runtime = load_voice_runtime(
        project_root=project_root,
        artifact_dir=artifact_dir,
        device=device,
    )
    return create_voice_file(
        text=text,
        runtime=runtime,
        output_filename=output_filename,
    )


__all__ = [
    "VoiceRuntime",
    "load_voice_runtime",
    "create_voice_file",
    "create_voice_file_from_runtime",
    "load_and_create_voice_file",
]
