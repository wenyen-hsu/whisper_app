import SwiftUI

@main
struct WhisperSwiftApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
        }
    }
}

struct ContentView: View {
    @State private var audioURL: URL?
    @State private var transcript: String = ""
    @State private var isProcessing = false
    var body: some View {
        VStack(spacing: 20) {
            Button("Select Audio") {
                let panel = NSOpenPanel()
                panel.allowsMultipleSelection = false
                panel.allowedFileTypes = ["wav", "mp3", "m4a", "mp4", "webm"]
                if panel.runModal() == .OK {
                    audioURL = panel.url
                }
            }
            if let url = audioURL {
                Text(url.lastPathComponent)
            }
            Button("Transcribe") {
                if let url = audioURL {
                    transcribe(url: url)
                }
            }.disabled(audioURL == nil || isProcessing)
            if isProcessing {
                ProgressView()
            }
            ScrollView {
                Text(transcript).frame(maxWidth: .infinity, alignment: .leading)
            }.padding()
        }.padding()
        .frame(minWidth: 400, minHeight: 300)
    }

    private func transcribe(url: URL) {
        isProcessing = true
        transcript = ""
        DispatchQueue.global(qos: .userInitiated).async {
            let fileManager = FileManager.default
            let tmp = fileManager.temporaryDirectory.appendingPathComponent("converted.wav")
            let ffmpeg = Process()
            ffmpeg.launchPath = "/usr/bin/env"
            ffmpeg.arguments = ["ffmpeg", "-y", "-i", url.path, "-ar", "16000", "-ac", "1", "-f", "wav", tmp.path]
            ffmpeg.standardError = Pipe()
            ffmpeg.standardOutput = Pipe()
            ffmpeg.launch()
            ffmpeg.waitUntilExit()
            guard ffmpeg.terminationStatus == 0 else {
                DispatchQueue.main.async {
                    self.transcript = "ffmpeg conversion failed"
                    self.isProcessing = false
                }
                return
            }
            let whisper = Process()
            whisper.launchPath = "./whisper.cpp/build/bin/whisper-cli"
            whisper.arguments = [tmp.path, "--model", "medium", "--output-txt", "--output-file", tmp.deletingPathExtension().path]
            whisper.standardError = Pipe()
            whisper.standardOutput = Pipe()
            whisper.launch()
            whisper.waitUntilExit()
            if whisper.terminationStatus == 0 {
                let txtPath = tmp.deletingPathExtension().appendingPathExtension("txt")
                if let data = try? Data(contentsOf: txtPath), let text = String(data: data, encoding: .utf8) {
                    DispatchQueue.main.async {
                        self.transcript = text
                        self.isProcessing = false
                    }
                } else {
                    DispatchQueue.main.async {
                        self.transcript = "No transcript found"
                        self.isProcessing = false
                    }
                }
            } else {
                DispatchQueue.main.async {
                    self.transcript = "whisper-cli failed"
                    self.isProcessing = false
                }
            }
        }
    }
}

#if DEBUG
struct ContentView_Previews: PreviewProvider {
    static var previews: some View {
        ContentView()
    }
}
#endif
