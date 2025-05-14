import os
from src.transcribe.whisper_runner import WhisperTranscriber

def test_cli_transcribe():
    # 任選一個 uploads 下的音檔
    audio_path = os.path.abspath("uploads/record_a06c7156d9874e729236d352030d9556.wav")
    transcriber = WhisperTranscriber()
    result = transcriber.transcribe(audio_path)
    print("--- CLI 輸出結果 ---")
    print("text:\n", result["text"])
    print("srt:\n", result["srt"])
    print("segments:", result["segments"])

if __name__ == "__main__":
    test_cli_transcribe()
