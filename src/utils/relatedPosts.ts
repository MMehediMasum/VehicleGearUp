import type { CollectionEntry } from 'astro:content';

export function getRelatedPosts(
  current: CollectionEntry<'blog'>,
  allPosts: CollectionEntry<'blog'>[],
  limit = 3
) {
  const cats = current.data.categories || [];
  return allPosts
    .filter((p) => p.id !== current.id)
    .map((p) => ({
      post: p,
      score: (p.data.categories || []).filter((c) => cats.includes(c)).length,
    }))
    .filter((x) => x.score > 0)
    .sort(
      (a, b) =>
        b.score - a.score ||
        +b.post.data.pubDate - +a.post.data.pubDate
    )
    .slice(0, limit)
    .map((x) => x.post);
}