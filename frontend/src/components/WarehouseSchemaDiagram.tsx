import { useLayoutEffect, useMemo, useRef, useState, type CSSProperties } from "react";
import { useTranslation } from "react-i18next";
import { WarehouseRelationship, WarehouseTableAdmin } from "../api";

const CELL_W = 252;
const CELL_H = 300;
const PAD_X = 24;
const PAD_Y = 20;

/** Grid placement for the core warehouse + customer-linked app tables. */
const CORE_LAYOUT: Record<string, { col: number; row: number }> = {
  DWH_FCT_POLICY_STATUS: { col: 1, row: 0 },
  DWH_FCT_INVESTMENT_TRACK: { col: 2, row: 0 },
  DWH_DIM_CUSTOMERS_UNIQUE: { col: 0, row: 1 },
  DWH_DIM_ALL_POLICY: { col: 1, row: 1 },
  DWH_FCT_POLICY_INVESTMENT_TRACK: { col: 2, row: 1 },
  DWH_FCT_FORECLOSURES: { col: 0, row: 2 },
  DWH_FCT_FORECLOSURES_ASSETS: { col: 1, row: 2 },
  APP_CUSTOMER_INTERACTION_EVENTS: { col: 0, row: 3 },
  APP_CUSTOMER_CHURN_SCORES: { col: 1, row: 3 },
  APP_CUSTOMER_METRICS: { col: 2, row: 3 },
};

type EdgeSegment = {
  key: string;
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  label: string;
};

function layerClass(layer: string) {
  if (layer === "warehouse") return "warehouse-schema-card--warehouse";
  return "warehouse-schema-card--application";
}

function fkColumnsForTable(
  tableName: string,
  relationships: WarehouseRelationship[],
): Set<string> {
  const cols = new Set<string>();
  for (const r of relationships) {
    if (r.from_table === tableName) cols.add(r.from_column);
    if (r.to_table === tableName) cols.add(r.to_column);
  }
  return cols;
}

function SchemaCard({
  table,
  fkColumns,
  style,
  placed,
  cardRef,
}: {
  table: WarehouseTableAdmin;
  fkColumns: Set<string>;
  style?: CSSProperties;
  placed?: boolean;
  cardRef: (el: HTMLDivElement | null) => void;
}) {
  const { t } = useTranslation();
  return (
    <article
      ref={cardRef}
      className={`warehouse-schema-card ${layerClass(table.layer)}${
        placed ? " warehouse-schema-card--placed" : ""
      }${table.table_exists ? "" : " warehouse-schema-card--missing"}`}
      style={style}
      aria-label={`${table.table_name} schema`}
    >
      <header className="warehouse-schema-card-head">
        <code className="warehouse-schema-card-name">{table.table_name}</code>
        <span className={`warehouse-schema-layer warehouse-schema-layer-${table.layer}`}>
          {table.layer}
        </span>
      </header>
      <p className="muted small warehouse-schema-card-meta">
        {table.domain} · {table.role}
        {table.table_exists
          ? ` · ${table.row_count.toLocaleString()} ${t("admin.schemaDiagram.rowsSuffix")}`
          : ` · ${t("admin.schemaDiagram.notCreated")}`}
      </p>
      <ul className="warehouse-schema-columns">
        {table.columns.length === 0 && (
          <li className="muted small">{t("admin.schemaDiagram.noColumns")}</li>
        )}
        {(table.columns ?? []).map((col) => {
          const isFk = fkColumns.has(col.name);
          return (
            <li
              key={col.name}
              className={
                col.pk
                  ? "warehouse-schema-col warehouse-schema-col-pk"
                  : isFk
                    ? "warehouse-schema-col warehouse-schema-col-fk"
                    : "warehouse-schema-col"
              }
            >
              <span className="warehouse-schema-col-name">{col.name}</span>
              <span className="warehouse-schema-col-type">{col.type}</span>
            </li>
          );
        })}
      </ul>
    </article>
  );
}

function connectorPoint(
  from: DOMRect,
  to: DOMRect,
  container: DOMRect,
): { x1: number; y1: number; x2: number; y2: number } {
  const fc = {
    x: from.left + from.width / 2 - container.left,
    y: from.top + from.height / 2 - container.top,
  };
  const tc = {
    x: to.left + to.width / 2 - container.left,
    y: to.top + to.height / 2 - container.top,
  };
  const dx = tc.x - fc.x;
  const dy = tc.y - fc.y;

  let x1 = fc.x;
  let y1 = fc.y;
  let x2 = tc.x;
  let y2 = tc.y;

  if (Math.abs(dx) >= Math.abs(dy)) {
    x1 = fc.x + (dx > 0 ? from.width / 2 : -from.width / 2);
    x2 = tc.x + (dx > 0 ? -to.width / 2 : to.width / 2);
  } else {
    y1 = fc.y + (dy > 0 ? from.height / 2 : -from.height / 2);
    y2 = tc.y + (dy > 0 ? -to.height / 2 : to.height / 2);
  }

  return { x1, y1, x2, y2 };
}

type Props = {
  tables: WarehouseTableAdmin[];
  relationships: WarehouseRelationship[];
};

export default function WarehouseSchemaDiagram({ tables, relationships }: Props) {
  const { t } = useTranslation();
  const canvasRef = useRef<HTMLDivElement>(null);
  const cardRefs = useRef<Map<string, HTMLDivElement>>(new Map());
  const [edges, setEdges] = useState<EdgeSegment[]>([]);
  const [canvasSize, setCanvasSize] = useState({ w: 800, h: 600 });

  const tableByName = useMemo(() => {
    const m = new Map<string, WarehouseTableAdmin>();
    for (const t of tables) m.set(t.table_name, t);
    return m;
  }, [tables]);

  const coreTables = useMemo(
    () =>
      Object.keys(CORE_LAYOUT)
        .map((name) => tableByName.get(name))
        .filter((t): t is WarehouseTableAdmin => t != null),
    [tableByName],
  );

  const otherTables = useMemo(
    () => tables.filter((t) => !(t.table_name in CORE_LAYOUT)),
    [tables],
  );

  const gridSize = useMemo(() => {
    let maxCol = 0;
    let maxRow = 0;
    for (const pos of Object.values(CORE_LAYOUT)) {
      maxCol = Math.max(maxCol, pos.col);
      maxRow = Math.max(maxRow, pos.row);
    }
    return {
      w: PAD_X * 2 + (maxCol + 1) * CELL_W,
      h: PAD_Y * 2 + (maxRow + 1) * CELL_H,
    };
  }, []);

  useLayoutEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const measure = () => {
      const container = canvas.getBoundingClientRect();
      setCanvasSize({ w: container.width, h: container.height });

      const next: EdgeSegment[] = [];
      for (const rel of relationships) {
        const fromEl = cardRefs.current.get(rel.from_table);
        const toEl = cardRefs.current.get(rel.to_table);
        if (!fromEl || !toEl) continue;
        const from = fromEl.getBoundingClientRect();
        const to = toEl.getBoundingClientRect();
        const { x1, y1, x2, y2 } = connectorPoint(from, to, container);
        next.push({
          key: `${rel.from_table}-${rel.to_table}-${rel.from_column}`,
          x1,
          y1,
          x2,
          y2,
          label: rel.label,
        });
      }
      setEdges(next);
    };

    measure();
    const ro = new ResizeObserver(measure);
    ro.observe(canvas);
    window.addEventListener("resize", measure);
    return () => {
      ro.disconnect();
      window.removeEventListener("resize", measure);
    };
  }, [relationships, tables, gridSize]);

  const setCardRef = (name: string) => (el: HTMLDivElement | null) => {
    if (el) cardRefs.current.set(name, el);
    else cardRefs.current.delete(name);
  };

  return (
    <div className="warehouse-schema-diagram">
      <div
        ref={canvasRef}
        className="warehouse-schema-canvas"
        style={{ width: gridSize.w, height: gridSize.h, minWidth: "100%" }}
      >
        <svg
          className="warehouse-schema-edges"
          width={canvasSize.w}
          height={canvasSize.h}
          aria-hidden
        >
          <defs>
            <marker
              id="warehouse-schema-arrow"
              markerWidth="8"
              markerHeight="8"
              refX="7"
              refY="4"
              orient="auto"
            >
              <path d="M0,0 L8,4 L0,8 Z" fill="#5a7a94" />
            </marker>
          </defs>
          {edges.map((e) => {
            const mx = (e.x1 + e.x2) / 2;
            const path = `M ${e.x1} ${e.y1} C ${mx} ${e.y1}, ${mx} ${e.y2}, ${e.x2} ${e.y2}`;
            return (
              <g key={e.key}>
                <path
                  d={path}
                  className="warehouse-schema-edge"
                  markerEnd="url(#warehouse-schema-arrow)"
                />
                <title>{e.label}</title>
              </g>
            );
          })}
        </svg>
        {coreTables.map((table) => {
          const pos = CORE_LAYOUT[table.table_name];
          const fkColumns = fkColumnsForTable(table.table_name, relationships);
          return (
            <SchemaCard
              key={table.table_name}
              table={table}
              fkColumns={fkColumns}
              placed
              cardRef={setCardRef(table.table_name)}
              style={{
                left: PAD_X + pos.col * CELL_W,
                top: PAD_Y + pos.row * CELL_H,
                width: CELL_W - 16,
              }}
            />
          );
        })}
      </div>

      {otherTables.length > 0 && (
        <div className="warehouse-schema-other">
          <h3 className="subsection-title">{t("admin.schemaDiagram.cachesTitle")}</h3>
          <p className="muted small">{t("admin.schemaDiagram.cachesLede")}</p>
          <div className="warehouse-schema-other-grid">
            {otherTables.map((table) => (
              <SchemaCard
                key={table.table_name}
                table={table}
                fkColumns={fkColumnsForTable(table.table_name, relationships)}
                cardRef={() => {}}
                style={{}}
              />
            ))}
          </div>
        </div>
      )}

      <p className="muted small warehouse-schema-legend">
        <span className="warehouse-schema-legend-pk">{t("admin.schemaDiagram.legendPk")}</span>
        <span className="warehouse-schema-legend-fk">{t("admin.schemaDiagram.legendFk")}</span>
        {t("admin.schemaDiagram.legendArrows")}
      </p>
    </div>
  );
}
