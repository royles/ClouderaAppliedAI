import { useTranslation } from "react-i18next";
import { CustomerSummary } from "../api";
import { customerPath } from "../appRoutes";
import CustomerSummaryCard from "./CustomerSummaryCard";

type Props = {
  customers: CustomerSummary[];
  showRank: boolean;
  rankStart: number;
  dashboardReturn: string;
};

export default function CustomerCardGrid({
  customers,
  showRank,
  rankStart,
  dashboardReturn,
}: Props) {
  const { t } = useTranslation();
  if (customers.length === 0) {
    return <p className="muted customer-grid-empty">{t("customer.table.empty")}</p>;
  }

  return (
    <ul className="customer-card-grid">
      {customers.map((c, index) => {
        const rank = rankStart + index;
        return (
          <li key={c.customer_id}>
            <CustomerSummaryCard
              customer={c}
              showRank={showRank}
              rank={rank}
              to={customerPath(c.customer_id)}
              linkState={{ businessReturn: dashboardReturn }}
            />
          </li>
        );
      })}
    </ul>
  );
}
