// swift-tools-version:5.9
import PackageDescription

let package = Package(
    name: "Files",
    targets: [
        .target(name: "Core"),
        .executableTarget(name: "App", dependencies: ["Core", .product(name: "Logging", package: "swift-log")]),
        .testTarget(name: "CoreTests", dependencies: ["Core"]),
    ]
)
