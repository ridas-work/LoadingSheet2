import {
  CONTAINER_SIZE_OPTIONS,
  type CustomCartonForm,
  type OuterBox,
  type Product,
} from "../../types";

interface Props {
  cartons: CustomCartonForm[];
  products: Product[];
  outerBoxes: OuterBox[];
  onChange: (cartons: CustomCartonForm[]) => void;
}

function newItemKey() {
  return `item-${crypto.randomUUID()}`;
}

function newCartonKey() {
  return `carton-${crypto.randomUUID()}`;
}

export function emptyCarton(): CustomCartonForm {
  return {
    key: newCartonKey(),
    identical_count: "1",
    label: "",
    outer_box_id: "",
    items: [
      {
        key: newItemKey(),
        product_id: "",
        container_size: "as_in_catalog",
        qty: "1",
      },
    ],
  };
}

export default function CustomCartonsSection({
  cartons,
  products,
  outerBoxes,
  onChange,
}: Props) {
  function updateCarton(key: string, patch: Partial<CustomCartonForm>) {
    onChange(cartons.map((c) => (c.key === key ? { ...c, ...patch } : c)));
  }

  function removeCarton(key: string) {
    onChange(cartons.filter((c) => c.key !== key));
  }

  function updateItem(
    cartonKey: string,
    itemKey: string,
    patch: Partial<CustomCartonForm["items"][number]>,
  ) {
    onChange(
      cartons.map((c) =>
        c.key !== cartonKey
          ? c
          : {
              ...c,
              items: c.items.map((item) =>
                item.key === itemKey ? { ...item, ...patch } : item,
              ),
            },
      ),
    );
  }

  function addItem(cartonKey: string) {
    onChange(
      cartons.map((c) =>
        c.key !== cartonKey
          ? c
          : {
              ...c,
              items: [
                ...c.items,
                {
                  key: newItemKey(),
                  product_id: "",
                  container_size: "as_in_catalog",
                  qty: "1",
                },
              ],
            },
      ),
    );
  }

  function removeItem(cartonKey: string, itemKey: string) {
    onChange(
      cartons.map((c) =>
        c.key !== cartonKey
          ? c
          : { ...c, items: c.items.filter((item) => item.key !== itemKey) },
      ),
    );
  }

  return (
    <section className="card">
      <h2>Custom cartons (optional)</h2>
      <p className="help">
        Use for mixed boxes. Selecting a product line requires a container size and an
        outer shipping box (deducted from packaging inventory later).
      </p>

      {cartons.map((carton, index) => (
        <div key={carton.key} className="carton-block">
          <div className="carton-header">
            <h3>Custom carton {index + 1}</h3>
            <button type="button" className="btn danger" onClick={() => removeCarton(carton.key)}>
              Remove carton
            </button>
          </div>

          <div className="row-2">
            <label>
              How many identical cartons?
              <input
                type="number"
                min={1}
                value={carton.identical_count}
                onChange={(e) =>
                  updateCarton(carton.key, { identical_count: e.target.value })
                }
              />
            </label>
            <label>
              Label on sheet (optional)
              <input
                value={carton.label}
                onChange={(e) => updateCarton(carton.key, { label: e.target.value })}
                placeholder="Auto from products if empty"
              />
            </label>
          </div>

          <label>
            Outer box (required)
            <select
              value={carton.outer_box_id}
              onChange={(e) =>
                updateCarton(carton.key, { outer_box_id: e.target.value })
              }
              required
            >
              <option value="">Select outer box…</option>
              {outerBoxes.map((box) => (
                <option key={box.id} value={box.id}>
                  {box.name}
                </option>
              ))}
            </select>
            <span className="help">
              Empty carton deducted from inventory (generic custom size or standard
              product box).
            </span>
          </label>

          <div className="product-lines">
            <h4>Products inside this carton</h4>
            {products.length === 0 ? (
              <p className="help">
                Custom-carton products will appear here once they are added to the
                catalog (separate from the main sheet list).
              </p>
            ) : null}
            {carton.items.map((item) => (
              <div key={item.key} className="product-line-row">
                <select
                  value={item.product_id}
                  onChange={(e) =>
                    updateItem(carton.key, item.key, { product_id: e.target.value })
                  }
                  required
                >
                  <option value="">Select product…</option>
                  {products.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.name}
                    </option>
                  ))}
                </select>
                <select
                  value={item.container_size}
                  onChange={(e) =>
                    updateItem(carton.key, item.key, {
                      container_size: e.target.value as CustomCartonForm["items"][number]["container_size"],
                    })
                  }
                >
                  {CONTAINER_SIZE_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
                <input
                  type="number"
                  min={1}
                  value={item.qty}
                  onChange={(e) =>
                    updateItem(carton.key, item.key, { qty: e.target.value })
                  }
                  aria-label="Qty"
                />
                <button
                  type="button"
                  className="icon-btn"
                  onClick={() => removeItem(carton.key, item.key)}
                  disabled={carton.items.length === 1}
                  aria-label="Remove product line"
                >
                  ×
                </button>
              </div>
            ))}
            <button type="button" className="link-btn" onClick={() => addItem(carton.key)}>
              + Add product line
            </button>
          </div>
        </div>
      ))}

      <button type="button" className="btn block" onClick={() => onChange([...cartons, emptyCarton()])}>
        + Add custom carton
      </button>
    </section>
  );
}
