import Foundation

final class Server {
    weak var tree: Tree?

    func send(_ name: FileName) {}
    func list() {}

    class func shared() -> Server { Server() }
}
