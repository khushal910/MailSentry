import type { ElementType } from "react";

export type SearchCategory =
  | "Emails"
  | "Auto Classifier"
  | "Dashboard"
  | "Predictions"
  | "Profile"
  | "Settings"
  | "Quick Actions"
  | "Navigation";

export interface SearchResultItem {
  id: string;
  title: string;
  description: string;
  category: SearchCategory;
  icon: ElementType;
  action: () => void | Promise<void>;
  badge?: string;
  score?: number;
  snippet?: string;
}

export interface SearchGroup {
  category: SearchCategory;
  items: SearchResultItem[];
}
