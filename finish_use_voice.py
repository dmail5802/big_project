"""Voice runtime helper for the local GUI.

This module exposes a small class that loads the trained voice assets once and
creates WAV files for text supplied by the main application.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from final_use_voice import (
	VoiceRuntime,
	create_voice_file,
	load_voice_runtime,
)


class VoiceFileService:
	"""Load the trained voice model and synthesize text to WAV files."""

	def __init__(
		self,
		project_root: str | Path | None = None,
		artifact_dir: str | Path | None = None,
		device: str | None = None,
	) -> None:
		self.project_root = Path(project_root).expanduser().resolve() if project_root else None
		self.artifact_dir = Path(artifact_dir).expanduser().resolve() if artifact_dir else None
		self.device = device
		self._runtime: Optional[VoiceRuntime] = None

	def load(self) -> VoiceRuntime:
		"""Load and cache the runtime components from disk."""
		if self._runtime is None:
			self._runtime = load_voice_runtime(
				project_root=self.project_root,
				artifact_dir=self.artifact_dir,
				device=self.device,
			)
		return self._runtime

	def create_voice_file(self, text: str, output_filename: str) -> Path:
		"""Create a WAV file for the supplied text and return the output path.
		
		Args:
			text: The text that the model will synthesize and say.
			output_filename: The name for the output WAV file (e.g., 'sensor_reading.wav').
		
		Returns:
			Path to the generated WAV file.
		"""
		runtime = self.load()
		return create_voice_file(
			text=text,
			runtime=runtime,
			output_filename=output_filename,
		)

	def get_output_directory(self) -> Path:
		"""Return the directory where synthesized WAV files are stored."""
		return self.load().output_wav_dir

	def get_runtime(self) -> VoiceRuntime:
		"""Expose the cached runtime for callers that need direct access."""
		return self.load()


__all__ = ["VoiceFileService"]
