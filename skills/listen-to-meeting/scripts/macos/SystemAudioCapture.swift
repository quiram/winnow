// SystemAudioCapture — captures system (speaker) audio via ScreenCaptureKit
// and writes raw PCM (s16le, mono, 48 000 Hz) to stdout.
//
// Requires the Screen Recording permission (System Settings > Privacy &
// Security > Screen & System Audio Recording) — the same consent category
// Zoom or Loom ask for. No driver, no admin rights.
//
// Usage:
//   SystemAudioCapture --check   verify permission; exit 0 if granted,
//                                exit 2 with instructions if not
//   SystemAudioCapture           stream PCM to stdout until killed
//
// Compiled on first run by listen.py: swiftc -O SystemAudioCapture.swift

import Foundation
import CoreGraphics
import CoreMedia
import ScreenCaptureKit

func stderrLine(_ message: String) {
    FileHandle.standardError.write((message + "\n").data(using: .utf8)!)
}

let permissionHelp = """
Screen Recording permission is not granted to this terminal/agent process.
Grant it in: System Settings > Privacy & Security > Screen & System Audio \
Recording, then restart the terminal and try again.
"""

let checkMode = CommandLine.arguments.contains("--check")

if checkMode {
    if CGPreflightScreenCaptureAccess() {
        print("permission: granted")
        exit(0)
    }
    // Trigger the system prompt so the user can grant it without hunting
    // through System Settings.
    CGRequestScreenCaptureAccess()
    stderrLine(permissionHelp)
    exit(2)
}

final class AudioStreamOutput: NSObject, SCStreamOutput, SCStreamDelegate {
    private let out = FileHandle.standardOutput
    private var reportedExtractionError = false

    func stream(
        _ stream: SCStream,
        didOutputSampleBuffer sampleBuffer: CMSampleBuffer,
        of type: SCStreamOutputType
    ) {
        guard type == .audio, sampleBuffer.isValid else { return }
        // SCStream delivers float32 PCM at the configured rate/channel count
        // (mono 48 kHz here). Convert to s16le and write to stdout.
        var pcm = Data()
        do {
            try sampleBuffer.withAudioBufferList { audioBufferList, _ in
                for buffer in audioBufferList {
                    guard let base = buffer.mData else { continue }
                    let count = Int(buffer.mDataByteSize) / MemoryLayout<Float32>.size
                    let floats = base.bindMemory(to: Float32.self, capacity: count)
                    var samples = [Int16](repeating: 0, count: count)
                    for i in 0..<count {
                        let clamped = max(-1.0, min(1.0, floats[i]))
                        samples[i] = Int16(clamped * 32767.0)
                    }
                    samples.withUnsafeBytes { pcm.append(contentsOf: $0) }
                }
            }
        } catch {
            if !reportedExtractionError {
                reportedExtractionError = true
                stderrLine("audio buffer extraction failed: \(error)")
            }
            return
        }
        guard !pcm.isEmpty else { return }
        do {
            try out.write(contentsOf: pcm)
        } catch {
            exit(0) // downstream closed the pipe; we are done
        }
    }

    func stream(_ stream: SCStream, didStopWithError error: Error) {
        stderrLine("capture stopped: \(error.localizedDescription)")
        exit(1)
    }
}

if !CGPreflightScreenCaptureAccess() {
    CGRequestScreenCaptureAccess()
    stderrLine(permissionHelp)
    exit(2)
}

let output = AudioStreamOutput()
// Retained globally: SCStream stops delivering (and can be deallocated)
// if the only reference dies with the startup Task.
var activeStream: SCStream?

Task {
    do {
        let content = try await SCShareableContent.excludingDesktopWindows(
            false, onScreenWindowsOnly: false
        )
        guard let display = content.displays.first else {
            stderrLine("no display found to attach the audio capture to")
            exit(1)
        }
        let filter = SCContentFilter(display: display, excludingWindows: [])
        let config = SCStreamConfiguration()
        config.capturesAudio = true
        config.excludesCurrentProcessAudio = true
        config.sampleRate = 48_000
        config.channelCount = 1
        // Video is required by the API but unused: keep it as cheap as possible.
        config.width = 2
        config.height = 2
        config.minimumFrameInterval = CMTime(value: 1, timescale: 1)

        let stream = SCStream(filter: filter, configuration: config, delegate: output)
        activeStream = stream
        try stream.addStreamOutput(
            output, type: .audio,
            sampleHandlerQueue: DispatchQueue(label: "winnow.audio")
        )
        try await stream.startCapture()
        stderrLine("capturing") // readiness signal for the parent process
    } catch {
        stderrLine("failed to start capture: \(error.localizedDescription)")
        exit(1)
    }
}

signal(SIGTERM) { _ in exit(0) }
signal(SIGINT) { _ in exit(0) }

dispatchMain()
