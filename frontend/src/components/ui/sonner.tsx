import { Toaster as Sonner } from "sonner";
import { useTheme } from "@/context/ThemeContext";

type ToasterProps = React.ComponentProps<typeof Sonner>;

const Toaster = ({ ...props }: ToasterProps) => {
  const { theme } = useTheme();

  return (
    <Sonner
      theme={theme as ToasterProps["theme"]}
      className="toaster group"
      toastOptions={{
        classNames: {
          toast:
            "group toast group-[.toaster]:bg-card/95 group-[.toaster]:text-foreground group-[.toaster]:border-border/60 group-[.toaster]:shadow-2xl group-[.toaster]:backdrop-blur-xl group-[.toaster]:rounded-xl font-sans text-sm border p-4",
          description: "group-[.toast]:text-muted-foreground text-xs mt-0.5",
          actionButton:
            "group-[.toast]:bg-gradient-brand group-[.toast]:text-white font-semibold text-xs rounded-lg px-3 py-1.5 shadow-sm transition-transform active:scale-95 hover:opacity-95 shrink-0 ml-auto cursor-pointer",
          cancelButton:
            "group-[.toast]:bg-muted group-[.toast]:text-muted-foreground text-xs rounded-lg px-3 py-1.5",
          success:
            "group-[.toaster]:border-success/40 group-[.toaster]:bg-success/5 group-[.toast]:text-foreground group-[.toast]:[&>svg]:text-success",
          error:
            "group-[.toaster]:border-destructive/40 group-[.toaster]:bg-destructive/5 group-[.toast]:text-foreground group-[.toast]:[&>svg]:text-destructive",
          warning:
            "group-[.toaster]:border-warning/40 group-[.toaster]:bg-warning/5 group-[.toast]:text-foreground group-[.toast]:[&>svg]:text-warning",
          info:
            "group-[.toaster]:border-brand/40 group-[.toaster]:bg-brand/5 group-[.toast]:text-foreground group-[.toast]:[&>svg]:text-brand",
        },
      }}
      {...props}
    />
  );
};

export { Toaster };
