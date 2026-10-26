"use client";
// next-auth v4 starts the OIDC flow with a CSRF-protected POST; signIn() does that, then the
// browser goes to Keycloak. Auto-starts once; the button is the fallback and the retry.
import { SessionProvider, signIn } from "next-auth/react";
import { useEffect, useRef } from "react";
import { Button } from "react-aria-components";
import styles from "@/components/ui/Page.module.css";

type Props = { callbackUrl: string; auto: boolean; message: string; button: string };

export function SignInRedirect(props: Props) {
  // Auth.js lives under /auth because Caddy sends /api/* to the gateway.
  return (
    <SessionProvider basePath="/auth" refetchOnWindowFocus={false}>
      <Start {...props} />
    </SessionProvider>
  );
}

function Start(props: Props) {
  const started = useRef(false);
  const start = () => void signIn("keycloak", { callbackUrl: props.callbackUrl });
  useEffect(() => {
    if (props.auto && !started.current) {
      started.current = true;
      start();
    }
  });
  return (
    <div className={styles.panel}>
      <p role="status">{props.message}</p>
      <Button className={styles.button} onPress={start}>
        {props.button}
      </Button>
    </div>
  );
}
