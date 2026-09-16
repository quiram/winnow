// SystemAudioCapture — captures the system (speaker) audio mix via a Core
// Audio process tap (macOS 14.2+) and writes raw PCM (s16le, mono, 48 000 Hz)
// to stdout.
//
// Uses the "System Audio Recording Only" permission (System Settings >
// Privacy & Security > Screen & System Audio Recording, lower list) — the
// narrow, audio-only consent, with no screen access involved. The first run
// triggers the system prompt.
//
// Usage:
//   SystemAudioCapture --check   verify permission; exit 0 if granted,
//                                exit 2 with instructions if not
//   SystemAudioCapture           stream PCM to stdout until killed
//
// Compiled on first run by listen.py: swiftc -O SystemAudioCapture.swift

import AudioToolbox
import CoreAudio
import Foundation

let OUTPUT_RATE = 48_000.0

func stderrLine(_ message: String) {
    FileHandle.standardError.write((message + "\n").data(using: .utf8)!)
}

let permissionHelp = """
System audio recording permission is not granted to this terminal/agent \
process. If a prompt just appeared, approve it. Otherwise grant it in: \
System Settings > Privacy & Security > Screen & System Audio Recording, \
under "System Audio Recording Only", then restart the terminal and try again.
"""

func fourCC(_ status: OSStatus) -> String {
    let n = UInt32(bitPattern: status)
    let bytes = [n >> 24, n >> 16, n >> 8, n].map { UInt8($0 & 0xFF) }
    if bytes.allSatisfy({ $0 >= 0x20 && $0 < 0x7F }) {
        return "'\(String(bytes: bytes, encoding: .ascii)!)' (\(status))"
    }
    return "\(status)"
}

// --------------------------------------------------------------------------
// Tap + aggregate device setup
// --------------------------------------------------------------------------

func createTap() -> (tap: AudioObjectID, description: CATapDescription)? {
    let description = CATapDescription(stereoGlobalTapButExcludeProcesses: [])
    description.name = "winnow-system-audio-tap"
    description.isPrivate = true
    description.muteBehavior = .unmuted
    var tapID = AudioObjectID(kAudioObjectUnknown)
    let status = AudioHardwareCreateProcessTap(description, &tapID)
    guard status == noErr, tapID != kAudioObjectUnknown else {
        stderrLine("could not create system audio tap: error \(fourCC(status))")
        return nil
    }
    return (tapID, description)
}

let checkMode = CommandLine.arguments.contains("--check")

guard let (tapID, tapDescription) = createTap() else {
    stderrLine(permissionHelp)
    exit(2)
}

if checkMode {
    AudioHardwareDestroyProcessTap(tapID)
    print("permission: granted")
    exit(0)
}

// Read the tap's stream format (float32 at the output device's native rate).
var format = AudioStreamBasicDescription()
var formatAddress = AudioObjectPropertyAddress(
    mSelector: kAudioTapPropertyFormat,
    mScope: kAudioObjectPropertyScopeGlobal,
    mElement: kAudioObjectPropertyElementMain
)
var formatSize = UInt32(MemoryLayout<AudioStreamBasicDescription>.size)
var status = AudioObjectGetPropertyData(tapID, &formatAddress, 0, nil, &formatSize, &format)
guard status == noErr else {
    stderrLine("could not read tap format: error \(fourCC(status))")
    exit(1)
}
let sourceRate = format.mSampleRate
let channelCount = Int(format.mChannelsPerFrame)
let nonInterleaved = (format.mFormatFlags & kAudioFormatFlagIsNonInterleaved) != 0

// Wrap the tap in a private aggregate device so an IO proc can pull from it.
let aggregateDescription: [String: Any] = [
    kAudioAggregateDeviceNameKey as String: "winnow-system-audio",
    kAudioAggregateDeviceUIDKey as String: UUID().uuidString,
    kAudioAggregateDeviceIsPrivateKey as String: true,
    kAudioAggregateDeviceTapAutoStartKey as String: true,
    kAudioAggregateDeviceSubDeviceListKey as String: [[String: Any]](),
    kAudioAggregateDeviceTapListKey as String: [
        [
            kAudioSubTapUIDKey as String: tapDescription.uuid.uuidString,
            kAudioSubTapDriftCompensationKey as String: true,
        ]
    ],
]
var aggregateID = AudioObjectID(kAudioObjectUnknown)
status = AudioHardwareCreateAggregateDevice(aggregateDescription as CFDictionary, &aggregateID)
guard status == noErr, aggregateID != kAudioObjectUnknown else {
    stderrLine("could not create aggregate device: error \(fourCC(status))")
    exit(1)
}

// --------------------------------------------------------------------------
// IO proc: downmix to mono, resample to OUTPUT_RATE, write s16le to stdout
// --------------------------------------------------------------------------

let out = FileHandle.standardOutput
let ratio = sourceRate / OUTPUT_RATE
// Linear-interpolation resampler state, carried across callbacks.
var resamplePos = 0.0
var previousSample: Float = 0

func handleInput(_ inputData: UnsafePointer<AudioBufferList>) {
    let buffers = UnsafeMutableAudioBufferListPointer(
        UnsafeMutablePointer(mutating: inputData)
    )
    // Downmix to mono float.
    var mono = [Float]()
    if nonInterleaved {
        var channelPointers: [UnsafePointer<Float32>] = []
        var frameCount = Int.max
        for buffer in buffers {
            guard let base = buffer.mData else { continue }
            channelPointers.append(
                UnsafePointer(base.assumingMemoryBound(to: Float32.self))
            )
            frameCount = min(frameCount, Int(buffer.mDataByteSize) / 4)
        }
        guard !channelPointers.isEmpty, frameCount != Int.max else { return }
        mono.reserveCapacity(frameCount)
        for frame in 0..<frameCount {
            var sum: Float = 0
            for pointer in channelPointers { sum += pointer[frame] }
            mono.append(sum / Float(channelPointers.count))
        }
    } else {
        guard let buffer = buffers.first, let base = buffer.mData else { return }
        let channels = max(1, Int(buffer.mNumberChannels))
        let frameCount = Int(buffer.mDataByteSize) / (4 * channels)
        let floats = base.assumingMemoryBound(to: Float32.self)
        mono.reserveCapacity(frameCount)
        for frame in 0..<frameCount {
            var sum: Float = 0
            for channel in 0..<channels { sum += floats[frame * channels + channel] }
            mono.append(sum / Float(channels))
        }
    }
    guard !mono.isEmpty else { return }

    // Resample sourceRate -> OUTPUT_RATE with linear interpolation.
    // `resamplePos` is the fractional read position within [previousSample] + mono.
    var output = [Int16]()
    output.reserveCapacity(Int(Double(mono.count) / ratio) + 2)
    var pos = resamplePos
    while Int(pos) < mono.count {
        let index = Int(pos)
        let frac = Float(pos - Double(index))
        let earlier = index == 0 ? previousSample : mono[index - 1]
        let later = mono[index]
        let sample = earlier * (1 - frac) + later * frac
        let clamped = max(-1, min(1, sample))
        output.append(Int16(clamped * 32767))
        pos += ratio
    }
    resamplePos = pos - Double(mono.count)
    previousSample = mono[mono.count - 1]

    guard !output.isEmpty else { return }
    var pcm = Data()
    output.withUnsafeBytes { pcm.append(contentsOf: $0) }
    do {
        try out.write(contentsOf: pcm)
    } catch {
        exit(0) // downstream closed the pipe; we are done
    }
}

var ioProcID: AudioDeviceIOProcID?
status = AudioDeviceCreateIOProcIDWithBlock(
    &ioProcID, aggregateID, DispatchQueue(label: "winnow.audio")
) { _, inputData, _, _, _ in
    handleInput(inputData)
}
guard status == noErr, let procID = ioProcID else {
    stderrLine("could not install audio IO proc: error \(fourCC(status))")
    exit(1)
}
status = AudioDeviceStart(aggregateID, procID)
guard status == noErr else {
    stderrLine("could not start audio capture: error \(fourCC(status))")
    exit(1)
}
stderrLine("capturing (source: \(Int(sourceRate)) Hz, \(channelCount) ch)")

signal(SIGTERM) { _ in exit(0) }
signal(SIGINT) { _ in exit(0) }

dispatchMain()
