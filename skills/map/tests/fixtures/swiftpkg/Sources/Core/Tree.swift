import Foundation

public final class Tree: Node {
    public let name = "root"
    var server: Server?
    var names: [FileName] = []

    struct Entry {
        let file: FileName
    }

    func upload(_ entry: Entry) {
        let label = "Server upload"   // a string mentioning Server must not count
        server?.send(entry.file)
    }
}

extension Tree {
    func refresh() { server?.list() }
}
