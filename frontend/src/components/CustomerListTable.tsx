import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { CustomerSortBy, CustomerSummary, SortOrder } from "../api";
import { customerPath } from "../appRoutes";
import ChurnBadge from "../ChurnBadge";
import { formatMoneyIls } from "../localeFormat";
import {
  displayCustomerId,
  displayCustomerName,
  formatCity,
  formatLastLogin,
  maskEmail,
  maskPhone,
} from "../pii";

type Props = {
  customers: CustomerSummary[];
  showRank: boolean;
  rankStart: number;
  dashboardReturn: string;
  sortBy: CustomerSortBy;
  sortOrder: SortOrder;
  onToggleColumnSort: (by: CustomerSortBy) => void;
};

function sortIndicator(sortBy: CustomerSortBy, order: SortOrder, column: CustomerSortBy) {
  if (sortBy !== column) return "";
  return order === "desc" ? " ↓" : " ↑";
}

export default function CustomerListTable({
  customers,
  showRank,
  rankStart,
  dashboardReturn,
  sortBy,
  sortOrder,
  onToggleColumnSort,
}: Props) {
  const { t } = useTranslation();
  const col = (key: string) => t(`customer.table.columns.${key}`);
  return (
    <table className="table table-interactive">
      <thead>
        <tr>
          {showRank && <th>#</th>}
          <th>
            <button type="button" className="th-sort-btn" onClick={() => onToggleColumnSort("name")}>
              {col("name")}{sortIndicator(sortBy, sortOrder, "name")}
            </button>
          </th>
          <th>{col("id")}</th>
          <th>{col("city")}</th>
          <th>{col("email")}</th>
          <th>{col("mobile")}</th>
          <th>
            <button
              type="button"
              className={`th-sort-btn${sortBy === "customer_value" ? " th-sorted" : ""}`}
              onClick={() => onToggleColumnSort("customer_value")}
            >
              {col("value")}{sortIndicator(sortBy, sortOrder, "customer_value")}
            </button>
          </th>
          <th>
            <button
              type="button"
              className={`th-sort-btn${sortBy === "policy_count" ? " th-sorted" : ""}`}
              onClick={() => onToggleColumnSort("policy_count")}
            >
              {col("policies")}{sortIndicator(sortBy, sortOrder, "policy_count")}
            </button>
          </th>
          <th>
            <button
              type="button"
              className={`th-sort-btn${sortBy === "investment_count" ? " th-sorted" : ""}`}
              onClick={() => onToggleColumnSort("investment_count")}
            >
              {col("investments")}{sortIndicator(sortBy, sortOrder, "investment_count")}
            </button>
          </th>
          <th>{col("lastLogin")}</th>
          <th>
            <button
              type="button"
              className={`th-sort-btn${sortBy === "churn_risk" ? " th-sorted" : ""}`}
              onClick={() => onToggleColumnSort("churn_risk")}
            >
              {col("churn")}{sortIndicator(sortBy, sortOrder, "churn_risk")}
            </button>
          </th>
        </tr>
      </thead>
      <tbody>
        {customers.length === 0 ? (
          <tr>
            <td colSpan={showRank ? 11 : 10} className="muted">
              {t("customer.table.empty")}
            </td>
          </tr>
        ) : (
          customers.map((cust, index) => (
            <tr key={cust.customer_id} className="table-row-click">
              {showRank && <td className="rank-cell">{rankStart + index}</td>}
              <td>
                <Link to={customerPath(cust.customer_id)} state={{ businessReturn: dashboardReturn }}>
                  {displayCustomerName(cust.customer_name)}
                </Link>
              </td>
              <td>
                <Link to={customerPath(cust.customer_id)} state={{ businessReturn: dashboardReturn }}>
                  {displayCustomerId(cust.customer_id)}
                </Link>
              </td>
              <td>{formatCity(cust.city_name)}</td>
              <td>{maskEmail(cust.email)}</td>
              <td>{maskPhone(cust.mobile_no)}</td>
              <td>{formatMoneyIls(cust.customer_value)}</td>
              <td>{cust.policy_count ?? 0}</td>
              <td>{cust.investment_count ?? 0}</td>
              <td>{formatLastLogin(cust.last_login)}</td>
              <td>
                <ChurnBadge probability={cust.churn_probability} tier={cust.churn_risk_tier} />
              </td>
            </tr>
          ))
        )}
      </tbody>
    </table>
  );
}
