import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";

export type Crumb = {
  label: string;
  to?: string;
};

type Props = {
  items: Crumb[];
};

export default function Breadcrumbs({ items }: Props) {
  const { t } = useTranslation();
  if (items.length === 0) return null;
  return (
    <nav className="breadcrumbs" aria-label={t("common.a11y.breadcrumb")}>
      <ol>
        {items.map((item, index) => {
          const last = index === items.length - 1;
          return (
            <li key={`${item.label}-${index}`}>
              {last || !item.to ? (
                <span aria-current={last ? "page" : undefined}>{item.label}</span>
              ) : (
                <Link to={item.to}>{item.label}</Link>
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
