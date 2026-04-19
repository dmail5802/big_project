"""Wrapper for Raspberry Pi sensor readings and audio playback.

This module provides a simplified interface to connect to a Raspberry Pi,
read temperature and light sensors, and play audio messages on the Pi's speakers.
"""

from __future__ import annotations

import json
import time
from getpass import getpass
from pathlib import Path
from typing import Any

import paramiko


def connect_pi(
    host: str,
    username: str,
    password: str | None = None,
    key_filename: str | None = None,
    port: int = 22,
    timeout: int = 10,
    prompt_for_password: bool = True,
) -> paramiko.SSHClient:
    """Open and return an SSH connection to the Raspberry Pi."""
    if password is None and key_filename is None and prompt_for_password:
        password = getpass(f"Password for {username}@{host}: ")

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        client.connect(
            hostname=host,
            port=port,
            username=username,
            password=password,
            key_filename=key_filename,
            timeout=timeout,
            allow_agent=True,
            look_for_keys=True,
        )
    except paramiko.AuthenticationException as exc:
        raise RuntimeError(
            "Authentication failed. Check PI_PASSWORD or PI_KEY_FILE."
        ) from exc
    except paramiko.SSHException as exc:
        raise RuntimeError(
            "SSH negotiation failed. Ensure SSH is enabled on the Pi."
        ) from exc

    return client


def _run_remote_command(client: paramiko.SSHClient, command: str) -> tuple[str, str, int]:
    """Run a command on the Pi and return stdout, stderr, and exit status."""
    stdin, stdout, stderr = client.exec_command(command)
    _ = stdin

    raw_output = stdout.read().decode("utf-8").strip()
    raw_error = stderr.read().decode("utf-8").strip()
    exit_status = stdout.channel.recv_exit_status()
    return raw_output, raw_error, exit_status


def _run_remote_json_command(client: paramiko.SSHClient, command: str) -> dict[str, Any]:
    """Run a Pi command that returns JSON and decode it."""
    raw_output, raw_error, exit_status = _run_remote_command(client=client, command=command)

    if exit_status != 0:
        raise RuntimeError(
            f"Pi command failed with exit status {exit_status}. STDERR: {raw_error}"
        )
    if raw_error:
        raise RuntimeError(f"Pi returned an error: {raw_error}")
    if not raw_output:
        raise RuntimeError("Pi command returned no output.")

    try:
        return json.loads(raw_output)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Expected JSON from Pi, got: {raw_output}") from exc


class RaspberryPiSensor:
    """Interface for reading sensors and controlling audio on a Raspberry Pi."""

    def __init__(
        self,
        host: str,
        username: str = "pi",
        password: str | None = None,
        key_filename: str | None = None,
        port: int = 22,
        prompt_for_password: bool = False,
    ) -> None:
        """Initialize the Pi sensor connection.

        Args:
            host: IP address or hostname of the Raspberry Pi.
            username: SSH username (default: 'pi').
            password: SSH password (will prompt if not provided and key_filename is None).
            key_filename: Path to SSH private key file (optional).
            port: SSH port (default: 22).
            prompt_for_password: Whether to prompt for password if not provided (default: False).
        """
        self.host = host
        self.username = username
        self.password = password
        self.key_filename = key_filename
        self.port = port
        self.prompt_for_password = prompt_for_password
        self._client: paramiko.SSHClient | None = None

    def connect(self) -> None:
        """Establish SSH connection to the Raspberry Pi."""
        self._client = connect_pi(
            host=self.host,
            username=self.username,
            password=self.password,
            key_filename=self.key_filename,
            port=self.port,
            prompt_for_password=self.prompt_for_password,
        )

    def disconnect(self) -> None:
        """Close SSH connection to the Raspberry Pi."""
        if self._client is not None:
            self._client.close()
            self._client = None

    def _ensure_connected(self) -> None:
        """Ensure connection is open, connect if needed."""
        if self._client is None:
            self.connect()

    def get_light_reading(self, light_sensor_port: int = 0) -> dict[str, Any]:
        """Read light sensor value from the Pi.

        Args:
            light_sensor_port: GPIO port of the light sensor (default: 0).

        Returns:
            Dictionary with sensor, port, value, and timestamp.
        """
        self._ensure_connected()

        command = (
            "python3 -c \""
            "import json,time,grovepi;"
            f"value=int(grovepi.analogRead({light_sensor_port}));"
            f"print(json.dumps({{'sensor':'light','port':{light_sensor_port},'value':value,'timestamp':time.time()}}))"
            "\""
        )

        return _run_remote_json_command(client=self._client, command=command)

    def get_temperature_reading(
        self,
        dht_sensor_port: int = 5,
        dht_sensor_type: int = 0,
    ) -> dict[str, Any]:
        """Read temperature and humidity from the Pi.

        Args:
            dht_sensor_port: GPIO port of the DHT sensor (default: 5).
            dht_sensor_type: DHT sensor type (default: 0 for DHT11).

        Returns:
            Dictionary with sensor, port, temperature_c, temperature_f, humidity, and timestamp.

        Raises:
            RuntimeError: If the DHT sensor read fails or returns invalid data.
        """
        self._ensure_connected()

        command = (
            "python3 -c \""
            "import json,time,grovepi,math;"
            f"temp_c,humidity=grovepi.dht({dht_sensor_port},{dht_sensor_type});"
            "temp_c=float(temp_c) if temp_c is not None else float('nan');"
            "humidity=float(humidity) if humidity is not None else float('nan');"
            "ok=not (math.isnan(temp_c) or math.isnan(humidity));"
            "temp_f=(temp_c*9/5+32) if ok else float('nan');"
            f"print(json.dumps({{'sensor':'dht','port':{dht_sensor_port},'sensor_type':{dht_sensor_type},'temperature_c':temp_c,'temperature_f':temp_f,'humidity':humidity,'ok':ok,'timestamp':time.time()}}))"
            "\""
        )

        data = _run_remote_json_command(client=self._client, command=command)
        if not data.get("ok", False):
            raise RuntimeError(
                "DHT read returned invalid data. Try reading again in a moment."
            )
        return data

    def play_audio_file(
        self,
        audio_file_path: str,
        blocking: bool = True,
    ) -> dict[str, Any]:
        """Play an audio file on the Pi's speakers.

        Args:
            audio_file_path: Path to the WAV file on the Pi (e.g., '/home/pi/message.wav').
            blocking: Whether to wait for playback to finish (default: True).

        Returns:
            Dictionary with playback status and details.

        Raises:
            FileNotFoundError: If the audio file doesn't exist on the Pi.
            RuntimeError: If no audio player is available or playback fails.
        """
        self._ensure_connected()

        mode = "blocking" if blocking else "background"
        command = f'''python3 -c "import json, os, shutil, subprocess
audio_path = {audio_file_path!r}
mode = {mode!r}
exists = os.path.isfile(audio_path)
players = ['aplay', 'mpg123', 'omxplayer']
player = next((p for p in players if shutil.which(p)), None)
result = {{'audio_path': audio_path, 'exists': exists, 'player': player, 'mode': mode}}
if (not exists) or (player is None):
    print(json.dumps(result))
    raise SystemExit(0)
cmd = [player, audio_path]
if mode == 'background':
    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    result['started'] = True
    result['returncode'] = None
else:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    result['started'] = (proc.returncode == 0)
    result['returncode'] = proc.returncode
    result['stderr'] = proc.stderr.strip()
print(json.dumps(result))"'''

        result = _run_remote_json_command(client=self._client, command=command)
        if not result.get("exists", False):
            raise FileNotFoundError(
                f"Audio file not found on Pi: {audio_file_path}"
            )
        if result.get("player") is None:
            raise RuntimeError(
                "No supported audio player found on Pi. Install aplay, mpg123, or omxplayer."
            )
        if blocking and not result.get("started", False):
            raise RuntimeError(
                f"Audio playback failed. Player stderr: {result.get('stderr', '')}"
            )
        return result

    def play_local_audio_file(
        self,
        local_audio_file_path: str | Path,
        blocking: bool = True,
        remote_directory: str = "/tmp",
    ) -> dict[str, Any]:
        """Upload a local audio file to the Pi and play it through the Pi's speakers.

        Args:
            local_audio_file_path: Path to the audio file on the PC running this code.
            blocking: Whether to wait for playback to finish (default: True).
            remote_directory: Directory on the Pi to store the uploaded file temporarily.

        Returns:
            Dictionary with upload and playback details.

        Raises:
            FileNotFoundError: If the local audio file does not exist.
            RuntimeError: If upload or playback fails.
        """
        self._ensure_connected()

        local_path = Path(local_audio_file_path)
        if not local_path.exists():
            raise FileNotFoundError(f"Local audio file not found: {local_path}")

        remote_path = f"{remote_directory.rstrip('/')}/{local_path.name}"

        assert self._client is not None
        with self._client.open_sftp() as sftp:
            sftp.put(str(local_path), remote_path)

        playback_result = self.play_audio_file(remote_path, blocking=blocking)
        playback_result["uploaded_from"] = str(local_path)
        playback_result["remote_audio_path"] = remote_path
        return playback_result
    
    def play_audio_file2(self, audio_file_path: str) -> None:
        self._ensure_connected()
        command = f"aplay {audio_file_path}"
        _, error, status = _run_remote_command(self._client, command)

        if status != 0:
            raise RuntimeError(f"Playback failed: {error}")
        
    def stream_light_readings(
        self,
        sample_count: int = 10,
        interval_seconds: float = 1.0,
        light_sensor_port: int = 0,
    ) -> list[dict[str, Any]]:
        """Collect multiple light readings from the Pi at a fixed interval.

        Args:
            sample_count: Number of samples to collect (default: 10).
            interval_seconds: Seconds between samples (default: 1.0).
            light_sensor_port: GPIO port of the light sensor (default: 0).

        Returns:
            List of light reading dictionaries.
        """
        readings: list[dict[str, Any]] = []
        for _ in range(sample_count):
            readings.append(self.get_light_reading(light_sensor_port=light_sensor_port))
            time.sleep(interval_seconds)
        return readings


__all__ = [
    "RaspberryPiSensor",
    "connect_pi",
]
