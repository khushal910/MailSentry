import { QueryClient } from "@tanstack/react-query";
import { createRouter } from "@tanstack/react-router";
import { routeTree } from "./routeTree.gen";

export const getRouter = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 5 * 60 * 1000, // 5 minutes fresh cache
        gcTime: 10 * 60 * 1000, // 10 minutes cache retention
        refetchOnWindowFocus: false, // Prevents layout shifts on tab switching
        retry: 1,
      },
    },
  });

  const router = createRouter({
    routeTree,
    context: { queryClient },
    scrollRestoration: true,
    defaultPreload: "intent",
    defaultPreloadDelay: 0, // 0ms delay: preloads code chunk immediately on hover/intent
    defaultPreloadStaleTime: 10 * 60 * 1000, // 10 minutes preload validity
    defaultPendingMs: 1000,
    defaultPendingMinMs: 0,
  });

  return router;
};
