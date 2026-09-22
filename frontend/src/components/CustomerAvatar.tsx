import { useState } from "react";
import { customerAvatarUrl } from "../customerAvatar";

type Props = {
  customerId: number;
  customerName?: string | null;
  size?: "sm" | "md" | "lg";
  className?: string;
};

const SIZE_PX = { sm: 40, md: 56, lg: 72 } as const;

export default function CustomerAvatar({
  customerId,
  customerName,
  size = "md",
  className = "",
}: Props) {
  const [failed, setFailed] = useState(false);
  const px = SIZE_PX[size];
  const label = customerName?.trim() || `Customer ${customerId}`;

  if (failed) {
    return (
      <span
        className={`customer-avatar customer-avatar-fallback customer-avatar-${size}${className ? ` ${className}` : ""}`}
        style={{ width: px, height: px }}
        role="img"
        aria-label={label}
      />
    );
  }

  return (
    <img
      className={`customer-avatar customer-avatar-${size}${className ? ` ${className}` : ""}`}
      src={customerAvatarUrl(customerId)}
      alt=""
      width={px}
      height={px}
      loading="lazy"
      decoding="async"
      onError={() => setFailed(true)}
    />
  );
}
