"use client";
import Link from "next/link";
// Generic error page: no stack traces or internal detail, only an opaque reference.
import { useTranslations } from "next-intl";
import { Button } from "react-aria-components";
import styles from "@/components/ui/Page.module.css";

export default function ErrorPage({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  const t = useTranslations("error");
  return (
    <main id="main" className={styles.panel}>
      <h1>{t("heading")}</h1>
      <p>{t("body")}</p>
      {error.digest && <p className={styles.reference}>{t("reference", { digest: error.digest })}</p>}
      <p>
        <Button className={styles.button} onPress={reset}>
          {t("retry")}
        </Button>
      </p>
      <p>
        <Link href="/">{t("home")}</Link>
      </p>
    </main>
  );
}
