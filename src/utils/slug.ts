// Single source of truth for topic/category URL slugs.
// "Sofas, Seating & Living Room Furniture" -> "sofas-seating-and-living-room-furniture"
export function slugify(text: string): string {
	return text
		.toLowerCase()
		.replace(/&/g, ' and ')
		.replace(/['’]/g, '')
		.replace(/[^a-z0-9]+/g, '-')
		.replace(/^-+|-+$/g, '');
}
