import { Order } from "@app/model";
import { format } from "./format";

export class OrderView {
  constructor(private order: Order) {}
  render(): string { return format(this.order.total()); }
}
