import { useTranslation } from "react-i18next";

export function Placeholder({ name }: { name: string }) {
  const { t } = useTranslation();
  return (
    <section data-testid={`route-${name}`}>
      <h1>{t(`nav.${name}`)}</h1>
      <p>{t("state.coming_later")}</p>
    </section>
  );
}
