import type { Customer } from "../../types";

interface Props {
  poNumber: string;
  customerId: string;
  city: string;
  deadlineDate: string;
  customers: Customer[];
  onChange: (field: "poNumber" | "customerId" | "city" | "deadlineDate", value: string) => void;
}

export default function OrderHeaderFields({
  poNumber,
  customerId,
  city,
  deadlineDate,
  customers,
  onChange,
}: Props) {
  return (
    <section className="card">
      <label>
        PO number
        <input
          value={poNumber}
          onChange={(e) => onChange("poNumber", e.target.value)}
          required
        />
      </label>

      <label>
        Customer name
        <select
          value={customerId}
          onChange={(e) => {
            onChange("customerId", e.target.value);
            const customer = customers.find((c) => String(c.id) === e.target.value);
            if (customer?.default_city) onChange("city", customer.default_city);
          }}
          required
        >
          <option value="">Select customer…</option>
          {customers.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </select>
        <span className="help">
          Choose from the list only — new customers must be opened as an account and
          approved by admin before use.
        </span>
      </label>

      <div className="row-2">
        <label>
          City
          <input
            value={city}
            onChange={(e) => onChange("city", e.target.value)}
            placeholder="e.g. LAHORE"
            required
          />
        </label>
        <label>
          Deadline date
          <input
            type="date"
            value={deadlineDate}
            onChange={(e) => onChange("deadlineDate", e.target.value)}
            required
          />
        </label>
      </div>
    </section>
  );
}
