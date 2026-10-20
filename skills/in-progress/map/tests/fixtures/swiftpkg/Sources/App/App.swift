import Core

@main
struct App {
    static func main() {
        let tree = Tree()
        print(tree.name)
    }
}

extension FileName: CustomStringConvertible {
    public var description: String { raw }
}
