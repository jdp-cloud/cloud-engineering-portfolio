import type { ReactNode } from "react";

export const metadata = {
  title: "Project 07",
  description: "Web service for the Project 07 ECS pipeline lab",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
