export type Role = "order_clerk" | "batch_clerk" | "dispatch_clerk" | "admin";

export interface User {
  id: number;
  username: string;
  first_name: string;
  last_name: string;
  role: Role;
  email: string;
  can_market_visit: boolean;
}

export interface Customer {
  id: number;
  name: string;
  default_city: string;
  is_approved: boolean;
}

export interface Product {
  id: number;
  name: string;
  bottles_per_carton: number;
  unit_label: "bottles" | "bundles";
  show_on_sheet: boolean;
  is_active: boolean;
  sort_order: number;
}

export interface OuterBox {
  id: number;
  name: string;
  is_active: boolean;
}

export type ContainerSize =
  | "as_in_catalog"
  | "5kg_litre_jar"
  | "1_litre"
  | "500_ml"
  | "750_ml"
  | "250_ml"
  | "100_ml"
  | "25_ltr_kg_can"
  | "120_drum"
  | "150_drum"
  | "200_drum";

export const CONTAINER_SIZE_OPTIONS: { value: ContainerSize; label: string }[] = [
  { value: "as_in_catalog", label: "As in catalog" },
  { value: "5kg_litre_jar", label: "5 kg / litre jar" },
  { value: "1_litre", label: "1 litre" },
  { value: "500_ml", label: "500 ml" },
  { value: "750_ml", label: "750 ml" },
  { value: "250_ml", label: "250 ml" },
  { value: "100_ml", label: "100 ml" },
  { value: "25_ltr_kg_can", label: "25 Ltr/Kg Can" },
  { value: "120_drum", label: "120 Litre Drum" },
  { value: "150_drum", label: "150 Litre Drum" },
  { value: "200_drum", label: "200 Litre Drum" },
];

export interface OrderListItem {
  id: number;
  po_number: string;
  customer_name: string;
  city: string;
  deadline_date: string;
  status: string;
  created_by_username: string;
  created_at: string;
  total_bottles: number;
  total_products: number;
}

export interface OrderDetail {
  id: number;
  po_number: string;
  customer_id: number;
  customer_name: string;
  city: string;
  deadline_date: string;
  status: string;
  created_by_username: string;
  created_at: string;
  lines: {
    id: number;
    product_id: number;
    product_name: string;
    bottles: number;
    bottles_per_carton: number;
    cartons: number;
  }[];
  custom_cartons: {
    id: number;
    identical_count: number;
    label: string;
    outer_box_id: number;
    outer_box_name: string;
    items: {
      id: number;
      product_id: number;
      product_name: string;
      container_size: ContainerSize;
      qty: number;
    }[];
  }[];
}

export interface CustomCartonFormItem {
  key: string;
  product_id: string;
  container_size: ContainerSize;
  qty: string;
}

export interface CustomCartonForm {
  key: string;
  identical_count: string;
  label: string;
  outer_box_id: string;
  items: CustomCartonFormItem[];
}

export type AvailabilityValue = "" | "Y" | "N";

export interface MarketVisitColumn {
  code: string;
  group: string;
  label: string;
}

export interface MarketVisitColumnGroup {
  group: string;
  columns: { code: string; label: string }[];
}

export interface MarketVisitStoreRow {
  key: string;
  store_name: string;
  location: string;
  remarks: string;
  availability: Record<string, AvailabilityValue>;
  facing: Record<string, string>;
}

export type MarketVisitStatus = "in_process" | "submitted";

export interface MarketVisitDetail {
  id: number | null;
  visit_date: string;
  status: MarketVisitStatus;
  created_by_username: string;
  store_count: number;
  stores: {
    id: number;
    store_name: string;
    location: string;
    remarks: string;
    availability: Record<string, string>;
    facing: Record<string, number | null>;
    sort_order: number;
  }[];
  created_at: string | null;
  updated_at: string | null;
}

export interface MarketVisitListItem {
  id: number;
  visit_date: string;
  status: MarketVisitStatus;
  created_by_username: string;
  store_count: number;
  title: string;
  first_location: string;
  created_at: string;
  updated_at: string;
}

export type BatchPurpose = "regular" | "sample";
export type BatchQuantityUnit = "L" | "ml";
export type BatchQCResult = "successful" | "unsuccessful";

export interface BatchProduct {
  id: number;
  code: string;
  name: string;
  sort_order: number;
}

export type PackagingMaterialType =
  | "bottle"
  | "lid"
  | "cap"
  | "label"
  | "box"
  | "partition"
  | "pouch"
  | "sticker"
  | "other";

export interface PackagingMaterial {
  id: number;
  name: string;
  code: string;
  material_type: PackagingMaterialType | string;
  purchased_qty: number;
  rejected_qty: number;
  uip_qty: number;
  balance: number;
  is_active: boolean;
  sort_order: number;
  created_at: string;
  updated_at: string;
}

export interface DispatchOrder {
  id: number;
  po_number: string;
  customer_name: string;
  city: string;
  deadline_date: string;
  status: string;
  created_by_username: string;
  total_products: number;
  total_bottles: number;
  created_at: string;
}

export type TripStatus = "planned" | "delivered";

export interface TripOrderItem {
  id: number;
  order_id: number;
  po_number: string;
  customer_name: string;
  city: string;
  deadline_date: string;
  created_by_username: string;
  challan_no: string;
  sort_order: number;
}

export interface Trip {
  id: number;
  vehicle_no: string;
  driver_name: string;
  helper_name: string;
  production_incharge: string;
  security: string;
  default_challan_no: string;
  status: TripStatus;
  trip_orders: TripOrderItem[];
  order_count: number;
  created_by_username: string;
  created_by_name: string;
  created_at: string;
  updated_at: string;
}

export interface TripWritePayload {
  vehicle_no: string;
  driver_name: string;
  helper_name: string;
  production_incharge: string;
  security: string;
  default_challan_no: string;
  orders: { order_id: number; challan_no: string }[];
}

export interface Batch {
  id: number;
  purpose: BatchPurpose;
  batch_number: string;
  batch_product_id: number;
  batch_product_name: string;
  batch_product_code: string;
  date: string;
  ph: string;
  solids: string;
  appearance: string;
  provider: string;
  quantity: string;
  quantity_unit: BatchQuantityUnit;
  remaining_quantity: string;
  customer_name: string;
  qc_result: BatchQCResult;
  comment: string;
  is_closed: boolean;
  is_available: boolean;
  status_label: string;
  created_by_username: string;
  created_by_name: string;
  created_at: string;
  updated_at: string;
}

