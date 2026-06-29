import CoreBluetooth
import Foundation

struct Options {
    var seconds: TimeInterval = 30
    var nameFilter: String = ""
    var idFilter: String = ""
    var minRSSI: Int = -127
}

final class CaptureScanner: NSObject, CBCentralManagerDelegate {
    private var manager: CBCentralManager!
    private let options: Options

    init(options: Options) {
        self.options = options
        super.init()
        self.manager = CBCentralManager(delegate: self, queue: DispatchQueue.main)
        Timer.scheduledTimer(withTimeInterval: options.seconds, repeats: false) { _ in
            self.finish()
        }
    }

    func centralManagerDidUpdateState(_ central: CBCentralManager) {
        guard central.state == .poweredOn else {
            fputs("Bluetooth unavailable. State: \(central.state.rawValue)\n", stderr)
            finish()
            return
        }

        central.scanForPeripherals(
            withServices: nil,
            options: [CBCentralManagerScanOptionAllowDuplicatesKey: true]
        )
    }

    func centralManager(
        _ central: CBCentralManager,
        didDiscover peripheral: CBPeripheral,
        advertisementData: [String: Any],
        rssi RSSI: NSNumber
    ) {
        let rssi = RSSI.intValue
        if rssi < options.minRSSI || rssi == 127 {
            return
        }

        let localName = advertisementData[CBAdvertisementDataLocalNameKey] as? String
        let name = peripheral.name ?? localName ?? ""
        let id = peripheral.identifier.uuidString

        if !options.nameFilter.isEmpty && !name.lowercased().contains(options.nameFilter.lowercased()) {
            return
        }
        if !options.idFilter.isEmpty && id.lowercased() != options.idFilter.lowercased() {
            return
        }

        let services = (advertisementData[CBAdvertisementDataServiceUUIDsKey] as? [CBUUID] ?? [])
            .map { $0.uuidString }
        let manufacturerData = (advertisementData[CBAdvertisementDataManufacturerDataKey] as? Data).map(hex) ?? ""
        let serviceData = (advertisementData[CBAdvertisementDataServiceDataKey] as? [CBUUID: Data] ?? [:])
            .reduce(into: [String: String]()) { result, item in
                result[item.key.uuidString] = hex(item.value)
            }

        let record: [String: Any] = [
            "timestamp": iso(Date()),
            "name": name.isEmpty ? "(no name)" : name,
            "id": id,
            "rssi": rssi,
            "services": services,
            "manufacturerData": manufacturerData,
            "serviceData": serviceData
        ]

        if let data = try? JSONSerialization.data(withJSONObject: record, options: [.sortedKeys]),
           let line = String(data: data, encoding: .utf8) {
            print(line)
            fflush(stdout)
        }
    }

    private func finish() {
        manager.stopScan()
        CFRunLoopStop(CFRunLoopGetMain())
    }
}

func parseOptions() -> Options {
    var options = Options()
    var args = Array(CommandLine.arguments.dropFirst())

    while !args.isEmpty {
        let arg = args.removeFirst()
        switch arg {
        case "--seconds":
            options.seconds = TimeInterval(args.removeFirst()) ?? options.seconds
        case "--name":
            options.nameFilter = args.removeFirst()
        case "--id":
            options.idFilter = args.removeFirst()
        case "--min-rssi":
            options.minRSSI = Int(args.removeFirst()) ?? options.minRSSI
        default:
            fputs("Unknown argument: \(arg)\n", stderr)
            exit(2)
        }
    }

    return options
}

func iso(_ date: Date) -> String {
    let formatter = ISO8601DateFormatter()
    formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
    return formatter.string(from: date)
}

func hex(_ data: Data) -> String {
    data.map { String(format: "%02X", $0) }.joined()
}

_ = CaptureScanner(options: parseOptions())
CFRunLoopRun()
