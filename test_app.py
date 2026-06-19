import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import app


class AppBehaviorTests(unittest.TestCase):
    def test_build_mlx_command_uses_python_module_and_expected_options(self):
        output_dir = Path("/tmp/moss-output")

        command = app.build_mlx_command(
            text="안녕하세요",
            language="Korean",
            output_dir=output_dir,
        )

        self.assertEqual(command[:4], [app.PYTHON_BIN, "-m", "mlx_audio.tts.generate", "--model"])
        self.assertIn(app.DEFAULT_MODEL, command)
        self.assertIn("--text", command)
        self.assertIn("안녕하세요", command)
        self.assertIn("--output_path", command)
        self.assertIn(str(output_dir), command)
        self.assertIn("--join_audio", command)
        self.assertIn("--lang_code", command)
        self.assertIn("ko", command)

    def test_build_mlx_command_omits_language_for_auto(self):
        command = app.build_mlx_command(
            text="Hello",
            language="auto",
            output_dir=Path("/tmp/moss-output"),
        )

        self.assertNotIn("--lang_code", command)

    def test_validate_text_rejects_empty_input(self):
        with self.assertRaises(ValueError):
            app.validate_text("   ")

    def test_find_newest_wav_returns_latest_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            older = output_dir / "older.wav"
            newer = output_dir / "newer.wav"
            older.write_bytes(b"old")
            newer.write_bytes(b"new")
            older.touch()
            newer.touch()

            self.assertEqual(app.find_newest_wav(output_dir), newer)

    def test_generate_audio_moves_latest_wav_to_requested_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            generated = output_dir / "audio.wav"
            generated.write_bytes(b"wav")

            with patch("app.run_mlx_command") as run_command:
                result = app.generate_audio_file(
                    text="Hello",
                    language="English",
                    output_dir=output_dir,
                    output_stem="fixed-name",
                )

            run_command.assert_called_once()
            self.assertEqual(result.name, "fixed-name.wav")
            self.assertEqual(result.read_bytes(), b"wav")
            self.assertFalse(generated.exists())

    def test_api_rejects_empty_text_from_json_body(self):
        from fastapi.testclient import TestClient

        client = TestClient(app.create_app())

        response = client.post("/api/generate", json={"text": "   ", "language": "auto"})

        self.assertEqual(response.status_code, 400)
        self.assertIn("문장을 입력", response.json()["detail"])


if __name__ == "__main__":
    unittest.main()
