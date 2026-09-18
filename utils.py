
def formatSize(size: int) -> str:
	if size < 1024:
		return f"{size} B"

	units = ["K", "M", "G", "T"]
	index = -1
	while size >= 1024:
		index += 1
		size /= 1024
	return f"{size:.1f} {units[index]}B"
