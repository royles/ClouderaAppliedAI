import { ReactNode } from "react";

type Props = {
  id: string;
  title: string;
  /** Shown on the right when collapsed (e.g. current backend label). */
  meta?: string | null;
  description?: string;
  defaultOpen?: boolean;
  children: ReactNode;
};

export default function AdminAccordionSection({
  id,
  title,
  meta,
  description,
  defaultOpen = false,
  children,
}: Props) {
  return (
    <details className="panel admin-accordion" id={id} open={defaultOpen ? true : undefined}>
      <summary className="admin-accordion-summary">
        <span className="admin-accordion-heading">
          <span className="admin-accordion-chevron" aria-hidden />
          <span className="admin-accordion-title">{title}</span>
        </span>
        {meta ? <span className="admin-accordion-meta muted small">{meta}</span> : null}
      </summary>
      {description ? <p className="muted small admin-accordion-lead">{description}</p> : null}
      <div className="admin-accordion-body">{children}</div>
    </details>
  );
}
