import type { components } from "./generated.js";

/** Response models generated from the OpenAPI spec (see ../openapi.json). */
export type Schemas = components["schemas"];

export type User = Schemas["UserRead"];
export type Wallet = Schemas["WalletRead"];
export type Transaction = Schemas["TransactionResponse"];
export type Escrow = Schemas["EscrowResponse"];

/** Loosely-typed object for endpoints that return an ad-hoc JSON body
 * (e.g. wallet balance, the mobile-money deposit envelope). */
export type HostPayObject = { [key: string]: any };
