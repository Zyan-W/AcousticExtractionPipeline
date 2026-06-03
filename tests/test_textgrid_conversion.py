import json
import unittest

from auto_mfa_tool.pipeline import PipelineError, whisper_json_to_textgrid


class TextGridConversionTest(unittest.TestCase):
    def test_whisper_json_to_textgrid_writes_intervals_and_blanks(self):
        with self.subTest("blank intervals and escaped quotes"):
            with TemporaryDirectoryPath() as tmp_path:
                json_path = tmp_path / "sample.json"
                json_path.write_text(
                    json.dumps(
                        {
                            "segments": [
                                {"start": 0.5, "end": 1.0, "text": " hello "},
                                {"start": 1.5, "end": 2.25, "text": 'quote " here'},
                            ]
                        }
                    ),
                    encoding="utf-8",
                )

                output_path = whisper_json_to_textgrid(json_path, tmp_path / "sample")
                textgrid = output_path.read_text(encoding="utf-8")

                self.assertEqual(output_path.name, "sample.TextGrid")
                self.assertIn('name = "sentences"', textgrid)
                self.assertIn('text = ""', textgrid)
                self.assertIn('text = "hello"', textgrid)
                self.assertIn('text = "quote "" here"', textgrid)
                self.assertIn("intervals: size = 4", textgrid)

    def test_empty_segments_raise_clear_error(self):
        with TemporaryDirectoryPath() as tmp_path:
            json_path = tmp_path / "empty.json"
            json_path.write_text(json.dumps({"segments": []}), encoding="utf-8")

            with self.assertRaisesRegex(PipelineError, "No valid Whisper segments"):
                whisper_json_to_textgrid(json_path, tmp_path / "empty")

    def test_invalid_time_segments_are_skipped(self):
        with TemporaryDirectoryPath() as tmp_path:
            json_path = tmp_path / "mixed.json"
            json_path.write_text(
                json.dumps(
                    {
                        "segments": [
                            {"start": 2.0, "end": 1.0, "text": "bad"},
                            {"start": 0.0, "end": 1.0, "text": "good"},
                        ]
                    }
                ),
                encoding="utf-8",
            )

            output_path = whisper_json_to_textgrid(json_path, tmp_path / "mixed.TextGrid")
            textgrid = output_path.read_text(encoding="utf-8")

            self.assertIn('text = "good"', textgrid)
            self.assertNotIn('text = "bad"', textgrid)


class TemporaryDirectoryPath:
    def __enter__(self):
        import tempfile
        from pathlib import Path

        self._context = tempfile.TemporaryDirectory()
        return Path(self._context.__enter__())

    def __exit__(self, exc_type, exc_value, traceback):
        return self._context.__exit__(exc_type, exc_value, traceback)


if __name__ == "__main__":
    unittest.main()
