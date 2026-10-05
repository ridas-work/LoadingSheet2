import type { Product } from "../../types";

interface Props {
  products: Product[];
  bottlesByProduct: Record<number, string>;
  onBottlesChange: (productId: number, bottles: string) => void;
}

function isExactMultiple(units: number, perCarton: number) {
  if (units <= 0) return true;
  if (perCarton <= 0) return false;
  return units % perCarton === 0;
}

function cartonsFor(units: number, perCarton: number) {
  if (!units || perCarton <= 0) return 0;
  if (units % perCarton !== 0) return null;
  return units / perCarton;
}

export function findSheetQtyErrors(
  products: Product[],
  bottlesByProduct: Record<number, string>,
): string[] {
  const errors: string[] = [];
  for (const product of products) {
    const qty = Number(bottlesByProduct[product.id] || 0);
    if (qty <= 0) continue;
    const per = product.bottles_per_carton;
    if (qty % per !== 0) {
      errors.push(
        `${product.name}: enter multiples of ${per} ${product.unit_label}/carton only (e.g. ${per}, ${per * 2}, ${per * 3}…). Got ${qty}.`,
      );
    }
  }
  return errors;
}

export default function ProductsSheet({
  products,
  bottlesByProduct,
  onBottlesChange,
}: Props) {
  const filled = products.filter((p) => Number(bottlesByProduct[p.id] || 0) > 0);
  const invalid = filled.filter(
    (p) => !isExactMultiple(Number(bottlesByProduct[p.id] || 0), p.bottles_per_carton),
  );
  const totalUnits = filled.reduce(
    (sum, p) => sum + Number(bottlesByProduct[p.id] || 0),
    0,
  );
  const totalCartons = filled.reduce((sum, p) => {
    const cartons = cartonsFor(
      Number(bottlesByProduct[p.id] || 0),
      p.bottles_per_carton,
    );
    return sum + (cartons ?? 0);
  }, 0);

  return (
    <section className="card">
      <h2>Products</h2>
      <p className="help">
        Qty must be an exact full-carton multiple for each product (bottles or
        bundles). Example: 20 / carton → only 20, 40, 60… B2G1 items use the same
        rule with bundles.
      </p>
      <p className="summary">
        {filled.length} products, {totalUnits} units · {totalCartons} cartons
        {invalid.length > 0 ? (
          <span className="summary-error">
            {" "}
            · {invalid.length} invalid qty (must match carton size)
          </span>
        ) : null}
      </p>

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Product</th>
              <th>Qty</th>
              <th>Cartons</th>
            </tr>
          </thead>
          <tbody>
            {products.map((product) => {
              const unitsStr = bottlesByProduct[product.id] ?? "0";
              const units = Number(unitsStr) || 0;
              const per = product.bottles_per_carton;
              const cartons = cartonsFor(units, per);
              const unit = product.unit_label;
              const invalidRow = units > 0 && !isExactMultiple(units, per);
              return (
                <tr key={product.id} className={invalidRow ? "row-invalid" : undefined}>
                  <td>
                    <strong>{product.name}</strong>
                    <div className="meta">
                      {per} {unit} / carton
                    </div>
                    {invalidRow ? (
                      <div className="field-error">
                        Only multiples of {per} (e.g. {per}, {per * 2}, {per * 3}…)
                      </div>
                    ) : null}
                  </td>
                  <td>
                    <input
                      className={`pill-input${invalidRow ? " input-invalid" : ""}`}
                      type="number"
                      min={0}
                      step={per}
                      value={unitsStr}
                      onChange={(e) => onBottlesChange(product.id, e.target.value)}
                      aria-invalid={invalidRow}
                      aria-label={`${product.name} ${unit}`}
                    />
                  </td>
                  <td className="cartons-cell">
                    {invalidRow ? "—" : cartons}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </section>
  );
}
