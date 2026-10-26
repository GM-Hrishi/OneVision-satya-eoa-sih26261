import Link from "next/link";

export default function NotFound() {
  return (
    <>
      <h1>Page not found</h1>
      <p>
        This mock portal has one page. <Link href="/">Go to Send test event</Link>.
      </p>
    </>
  );
}
