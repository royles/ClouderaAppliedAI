import { Link } from "react-router-dom";
import { CustomerSortBy, CustomerSummary, SortOrder } from "../api";
import ChurnBadge from "../ChurnBadge";
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
  return (
    <table className="table table-interactive">
      <thead>
        <tr>
          {showRank && <th>#</th>}
          <th>
            <button type="button" className="th-sort-btn" onClick={() => onToggleColumnSort("name")}>
              Name{sortIndicator(sortBy, sortOrder, "name")}
            </button>
          </th>
          <th>ID</th>
          <th>City</th>
          <th>Email</th>
          <th>Mobile</th>
          <th>
            <button
              type="button"
              className={`th-sort-btn${sortBy === "policy_count" ? " th-sorted" : ""}`}
              onClick={() => onToggleColumnSort("policy_count")}
            >
              Policies{sortIndicator(sortBy, sortOrder, "policy_count")}
            </button>
          </th>
          <th>
            <button
              type="button"
              className={`th-sort-btn${sortBy === "investment_count" ? " th-sorted" : ""}`}
              onClick={() => onToggleColumnSort("investment_count")}
            >
              Investments{sortIndicator(sortBy, sortOrder, "investment_count")}
            </button>
          </th>
          <th>Last login</th>
          <th>
            <button
              type="button"
              className={`th-sort-btn${sortBy === "churn_risk" ? " th-sorted" : ""}`}
              onClick={() => onToggleColumnSort("churn_risk")}
            >
              Churn risk{sortIndicator(sortBy, sortOrder, "churn_risk")}
            </button>
          </th>
        </tr>
      </thead>
      <tbody>
        {customers.length === 0 ? (
          <tr>
            <td colSpan={showRank ? 10 : 9} className="muted">
              No customers match this filter.
            </td>
          </tr>
        ) : (
          customers.map((c, index) => (
            <tr key={c.customer_id} className="table-row-click">
              {showRank && <td className="rank-cell">{rankStart + index}</td>}
              <td>
                <Link to={`/customers/${c.customer_id}`} state={{ dashboardReturn }}>
                  {displayCustomerName(c.customer_name)}
                </Link>
              </td>
              <td>
                <Link to={`/customers/${c.customer_id}`} state={{ dashboardReturn }}>
                  {displayCustomerId(c.customer_id)}
                </Link>
              </td>
              <td>{formatCity(c.city_name)}</td>
              <td>{maskEmail(c.email)}</td>
              <td>{maskPhone(c.mobile_no)}</td>
              <td>{c.policy_count ?? 0}</td>
              <td>{c.investment_count ?? 0}</td>
              <td>{formatLastLogin(c.last_login)}</td>
              <td>
                <ChurnBadge probability={c.churn_probability} tier={c.churn_risk_tier} />
              </td>
            </tr>
          ))
        )}
      </tbody>
    </table>
  );
}
