import Foundation

/// A node in the tree. Mentions Server in a comment, which must not count.
public protocol Node: AnyObject {
    var name: String { get }
}

public struct FileName: Hashable {
    let raw: String
}
