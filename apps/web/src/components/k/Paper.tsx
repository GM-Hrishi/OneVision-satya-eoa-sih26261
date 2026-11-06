// White "paper" with the one soft shadow style K allows (documents, the evidence viewer frame).
import type { ComponentPropsWithoutRef } from "react";

export function Paper({ className, ...rest }: ComponentPropsWithoutRef<"div">) {
  return <div className={`k-paper${className ? ` ${className}` : ""}`} {...rest} />;
}
