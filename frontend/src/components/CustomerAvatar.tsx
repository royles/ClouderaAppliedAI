type Props = {
  customerId: number;
  customerName?: string | null;
  size?: "sm" | "md" | "lg";
  className?: string;
};

const SIZE_PX = { sm: 40, md: 56, lg: 72 } as const;

/** Neutral profile placeholder — circle head + rounded shoulders (no photo). */
function ProfileOutlineIcon() {
  return (
    <svg
      className="customer-avatar-icon"
      viewBox="0 0 80 80"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden
    >
      <circle cx="40" cy="27" r="13" className="customer-avatar-icon-shape" />
      <rect
        x="19"
        y="44"
        width="42"
        height="26"
        rx="13"
        className="customer-avatar-icon-shape"
      />
    </svg>
  );
}

export default function CustomerAvatar({
  customerId,
  customerName,
  size = "md",
  className = "",
}: Props) {
  const px = SIZE_PX[size];
  const label = customerName?.trim() || `Customer ${customerId}`;

  return (
    <span
      className={`customer-avatar customer-avatar-outline customer-avatar-${size}${className ? ` ${className}` : ""}`}
      style={{ width: px, height: px }}
      role="img"
      aria-label={label}
    >
      <ProfileOutlineIcon />
    </span>
  );
}
