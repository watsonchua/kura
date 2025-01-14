import { z } from "zod";

export const DataPoint = z.object({
  x: z.string(),
  y: z.number(),
});

export const Cluster = z.object({
  id: z.string(),
  name: z.string(),
  description: z.string(),
  chat_ids: z.array(z.string()),
  parent_id: z.string().nullable(),
  count: z.number(),
  x_coord: z.number(),
  y_coord: z.number(),
  level: z.number(),
});

export const analyticsSchema = z.object({
  cumulative_words: z.array(DataPoint),
  messages_per_chat: z.array(DataPoint),
  messages_per_week: z.array(DataPoint),
  new_chats_per_week: z.array(DataPoint),
  clusters: z.array(Cluster),
});

export type Analytics = z.infer<typeof analyticsSchema>;
export type Cluster = z.infer<typeof Cluster>;
