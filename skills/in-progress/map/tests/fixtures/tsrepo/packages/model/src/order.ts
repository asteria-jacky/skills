export interface Priced {
  total(): number;
}

export type LineId = string;

export class LineItem implements Priced {
  constructor(readonly id: LineId, readonly price: number) {}
  total(): number { return this.price; }
}

export abstract class Document {}

export class Order extends Document implements Priced {
  lines: LineItem[] = [];
  total(): number { return this.lines.reduce((s, l) => s + l.total(), 0); }
}
