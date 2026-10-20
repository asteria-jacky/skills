import XCTest
@testable import Core

final class TreeTests: XCTestCase {
    func testUpload() {
        let tree = Tree()
        XCTAssertEqual(tree.name, "root")
    }
}
